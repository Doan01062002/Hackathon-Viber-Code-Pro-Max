"""Test contract cho AIEngine: forecast / optimize / price.

Trước đây bộ test này gọi qua HTTP (FastAPI TestClient). Giờ ai_service là thư viện thuần
Python nên gọi thẳng method; các assert về status code đổi thành assert về exception.

Dùng model đã train sẵn tại ai/models/model.pkl (chạy `python scripts/train.py`
trước nếu file chưa tồn tại — xem README/AGENTS.md).
"""

import os

import pytest
from ai_service.engine import AIEngine, InvalidRequestError, ODNotFoundError, MODEL_PATH
from ai_service.schemas import ForecastRequest, OptimizeRequest, PriceRequest

pytestmark = pytest.mark.skipif(
    not os.path.exists(MODEL_PATH),
    reason=f"Chưa có model tại {MODEL_PATH} — chạy `python scripts/train.py` trước.",
)

SERVICE_DATE = "2024-03-01"


@pytest.fixture()
def engine():
    # Engine mới mỗi test để cache tối ưu không rò rỉ giữa các test
    # (trước đây mỗi test dựng TestClient riêng nên STATE cũng sạch).
    return AIEngine()


def test_forecast_returns_items(engine):
    body = engine.forecast(ForecastRequest(service_date=SERVICE_DATE))
    assert body.service_date == SERVICE_DATE
    assert len(body.items) > 0
    item = body.items[0]
    assert item.p10 <= item.p50 <= item.p90
    assert item.lambda_hat >= 0


def test_forecast_rejects_bad_date(engine):
    with pytest.raises(InvalidRequestError):
        engine.forecast(ForecastRequest(service_date="not-a-date"))


def test_optimize_returns_valid_schema(engine):
    body = engine.optimize(OptimizeRequest(service_date=SERVICE_DATE))
    assert body.run_version
    assert isinstance(body.warm_started, bool)
    assert body.revenue_lp >= 0
    assert body.n_od > 0
    for bp in body.bid_prices:
        assert bp.bid_price >= 0


def test_optimize_second_call_warm_starts_with_same_run_version(engine):
    first = engine.optimize(OptimizeRequest(service_date=SERVICE_DATE))
    second = engine.optimize(OptimizeRequest(service_date=SERVICE_DATE))

    assert first.warm_started is False
    assert second.warm_started is True
    assert second.run_version == first.run_version


def test_optimize_force_resolve_bypasses_cache(engine):
    first = engine.optimize(OptimizeRequest(service_date=SERVICE_DATE))
    forced = engine.optimize(OptimizeRequest(service_date=SERVICE_DATE, force_resolve=True))

    assert forced.warm_started is False
    assert forced.run_version != first.run_version


def test_price_valid_od(engine):
    body = engine.price(PriceRequest(od_id=0, service_date=SERVICE_DATE))
    assert body.od_id == 0
    assert body.final_price >= 0
    assert body.decision in ("accepted", "blocked")
    explanation = body.explanation.model_dump()
    assert "bottleneck_segment" in explanation
    assert "elasticity" in explanation


def test_price_od_not_found(engine):
    with pytest.raises(ODNotFoundError):
        engine.price(PriceRequest(od_id=999_999, service_date=SERVICE_DATE))


def test_price_policy_guard_blocks(engine):
    body = engine.price(
        PriceRequest(
            od_id=0,
            service_date=SERVICE_DATE,
            min_price=999_999_999,
            max_price=999_999_999,
        )
    )
    assert body.decision == "blocked"
    assert body.final_price == 999_999_999


def test_clear_cache_forces_resolve(engine):
    first = engine.optimize(OptimizeRequest(service_date=SERVICE_DATE))
    engine.clear_cache()
    after = engine.optimize(OptimizeRequest(service_date=SERVICE_DATE))

    assert after.warm_started is False
    assert after.run_version != first.run_version
