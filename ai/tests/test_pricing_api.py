from ai_service.engine import AIEngine
from ai_service.schemas import PriceRequest, SegmentPriceInput


def test_price_accepts_backend_segment_snapshot():
    engine = AIEngine()
    response = engine.price(
        PriceRequest(
            od_id=42,
            service_date="2026-07-19",
            seat_type="ngoi_mem",
            base_price=100_000,
            segments=[
                SegmentPriceInput(segment_id=10, bid_price=200_000),
                SegmentPriceInput(segment_id=11, bid_price=100_000),
            ],
        )
    )

    assert response.od_id == 42
    assert response.opportunity_cost == 300_000
    assert response.proposed_price == 250_000
    assert response.explanation["bottleneck_segment"] == 10


def test_price_snapshot_works_without_forecast_model():
    """Nhánh snapshot là stateless — không cần model, engine vẫn định giá được."""
    engine = AIEngine(model_path=None)
    assert engine.health()["forecast_model_ready"] is False

    response = engine.price(
        PriceRequest(
            od_id=42,
            service_date="2026-07-19",
            seat_type="ngoi_mem",
            base_price=100_000,
            segments=[SegmentPriceInput(segment_id=10, bid_price=200_000)],
        )
    )

    assert response.opportunity_cost == 200_000
