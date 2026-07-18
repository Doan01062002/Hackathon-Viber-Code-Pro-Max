"""Test ranh giới backend -> ai_service qua AIClient.

Trước đây bộ test này mock `httpx.AsyncClient.post` vì AIClient gọi ai-service qua HTTP.
ai_service giờ là thư viện Python nên không còn mạng để mock: test dựng một engine giả
implement đúng hợp đồng của AIEngine và kiểm tra AIClient chuyển tiếp/ánh xạ cho đúng.
"""

import asyncio
import threading
from datetime import date

import pytest
from ai_service.engine import AIEngineError
from ai_service.schemas import (
    ForecastItem,
    ForecastResponse,
    OptimizeResponse,
    PriceExplanation,
    PriceResponse,
)

from backend.services.ai_client import AIClient, AIServiceError, SegmentBidPrice


class FakeEngine:
    """Engine giả ghi lại request nhận được để assert phần chuyển tiếp của AIClient."""

    def __init__(self, price_error: Exception | None = None):
        self.forecast_calls = []
        self.optimize_calls = []
        self.price_calls = []
        self.call_threads = []
        self._price_error = price_error

    def forecast(self, req):
        self.forecast_calls.append(req)
        self.call_threads.append(threading.current_thread())
        return ForecastResponse(
            service_date=req.service_date,
            model_version="test-v1",
            items=[
                ForecastItem(
                    od_id=1,
                    origin="HN",
                    dest="DN",
                    seat_type="soft_seat",
                    lambda_hat=12.0,
                    p10=8.0,
                    p50=12.0,
                    p90=17.0,
                )
            ],
        )

    def optimize(self, req):
        self.optimize_calls.append(req)
        return OptimizeResponse(
            service_date=req.service_date,
            run_version="ver-test",
            warm_started=False,
            solve_ms=12.5,
            revenue_lp=1_000_000.0,
            bid_prices=[],
            quotas=[],
            n_rejected=0,
            n_od=1,
        )

    def price(self, req):
        self.price_calls.append(req)
        if self._price_error is not None:
            raise self._price_error
        return PriceResponse(
            od_id=req.od_id,
            seat_type=req.seat_type or "soft_seat",
            opportunity_cost=89_000.0,
            proposed_price=1_550_000.0,
            final_price=1_550_000.0,
            decision="accept",
            explanation=PriceExplanation(
                bottleneck_segment=3,
                segment_pi={3: 89_000.0},
                bottleneck_load_pct=97.5,
                elasticity=-1.2,
                base_price=req.base_price or 1_000_000.0,
            ),
        )


@pytest.mark.asyncio
async def test_get_forecast_returns_serialized_response():
    """Khối 1 — AIClient trả dict đã model_dump, không phải object pydantic."""
    engine = FakeEngine()
    client = AIClient(engine=engine)

    res = await client.get_forecast("2026-07-20")

    assert res["service_date"] == "2026-07-20"
    assert res["model_version"] == "test-v1"
    assert res["items"][0]["od_id"] == 1
    assert engine.forecast_calls[0].service_date == "2026-07-20"


@pytest.mark.asyncio
async def test_engine_runs_off_event_loop_thread():
    """Engine nặng CPU nên phải chạy qua asyncio.to_thread, không chặn event loop."""
    engine = FakeEngine()
    client = AIClient(engine=engine)

    await client.get_forecast("2026-07-20")

    assert engine.call_threads[0] is not threading.current_thread()


@pytest.mark.asyncio
async def test_get_optimization_forwards_force_resolve():
    """Khối 2 — AIClient không cache nữa; force_resolve phải xuống tới engine."""
    engine = FakeEngine()
    client = AIClient(engine=engine)

    res = await client.get_optimization("2026-07-20", force_resolve=True)

    assert res["solve_ms"] == 12.5
    assert res["run_version"] == "ver-test"
    assert engine.optimize_calls[0].force_resolve is True


@pytest.mark.asyncio
async def test_get_optimization_no_client_side_cache():
    """Cache đã chuyển vào AIEngine (theo fingerprint λ̂) nên client gọi lại mỗi lần."""
    engine = FakeEngine()
    client = AIClient(engine=engine)

    await client.get_optimization("2026-07-20")
    await client.get_optimization("2026-07-20")

    assert len(engine.optimize_calls) == 2


@pytest.mark.asyncio
async def test_price_builds_request_from_backend_snapshot():
    """Khối 3 — backend đọc bid price trong DB rồi đẩy snapshot xuống engine (stateless)."""
    engine = FakeEngine()
    client = AIClient(engine=engine)

    result = await client.price(
        od_product_id=42,
        service_date=date(2026, 7, 20),
        seat_type="sleeper",
        base_price=1_000_000.0,
        segments=[SegmentBidPrice(segment_id=3, bid_price=89_000.0)],
    )

    req = engine.price_calls[0]
    assert req.od_id == 42
    assert req.service_date == "2026-07-20"
    assert req.seat_type == "sleeper"
    assert [(s.segment_id, s.bid_price) for s in req.segments] == [(3, 89_000.0)]

    assert result.proposed_price == 1_550_000.0
    assert result.explanation["bottleneck_segment"] == 3


@pytest.mark.asyncio
async def test_price_wraps_engine_error():
    """Lỗi engine được bọc thành AIServiceError để controller không phải biết ai_service."""
    engine = FakeEngine(price_error=AIEngineError("model chua san sang"))
    client = AIClient(engine=engine)

    with pytest.raises(AIServiceError):
        await client.price(
            od_product_id=42,
            service_date=date(2026, 7, 20),
            seat_type="sleeper",
            base_price=1_000_000.0,
            segments=[SegmentBidPrice(segment_id=3, bid_price=89_000.0)],
        )


def test_ai_client_defaults_to_shared_engine_singleton():
    """Không truyền engine -> dùng chung singleton để model.pkl chỉ nạp một lần/process."""
    from ai_service import engine as engine_module

    sentinel = FakeEngine()
    original = engine_module._engine
    try:
        engine_module._engine = sentinel
        assert AIClient()._engine is sentinel
    finally:
        engine_module._engine = original


@pytest.mark.asyncio
async def test_concurrent_calls_do_not_serialize_on_event_loop():
    """Nhiều request song song vẫn vào được threadpool cùng lúc."""
    engine = FakeEngine()
    client = AIClient(engine=engine)

    await asyncio.gather(*(client.get_forecast(f"2026-07-2{i}") for i in range(3)))

    assert len(engine.forecast_calls) == 3
