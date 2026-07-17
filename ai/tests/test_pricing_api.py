from ai_service.app import app, price
from ai_service.schemas import PriceRequest, SegmentPriceInput
from fastapi.testclient import TestClient


def test_internal_price_accepts_backend_segment_snapshot():
    response = price(
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


def test_internal_price_http_endpoint_starts_without_forecast_model():
    with TestClient(app) as client:
        response = client.post(
            "/internal/price",
            json={
                "od_id": 42,
                "service_date": "2026-07-19",
                "seat_type": "ngoi_mem",
                "base_price": 100_000,
                "segments": [{"segment_id": 10, "bid_price": 200_000}],
            },
        )

    assert response.status_code == 200
    assert response.json()["opportunity_cost"] == 200_000
