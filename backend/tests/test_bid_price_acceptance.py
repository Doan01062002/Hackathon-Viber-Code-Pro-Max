from datetime import date, datetime, timezone
UTC = timezone.utc

import pytest

from backend.services.ai_pricing_client import AIPriceResult
from backend.services.pricing_service import PricingService, evaluate_bid_price
from backend.views.pricing_view import PricingQuoteRequest


def test_accept_when_fare_covers_opportunity_cost():
    assert evaluate_bid_price(fare=500_000, opportunity_cost=450_000, availability=3) == "accepted"


def test_reject_when_fare_is_below_opportunity_cost():
    assert evaluate_bid_price(fare=400_000, opportunity_cost=450_000, availability=3) == "rejected"


def test_reject_when_od_is_sold_out():
    assert evaluate_bid_price(fare=500_000, opportunity_cost=450_000, availability=0) == "rejected"


class FakeAIClient:
    def __init__(self) -> None:
        self.received_segments = []

    async def price(self, **kwargs):
        self.received_segments = kwargs["segments"]
        return AIPriceResult(proposed_price=250_000, explanation={"elasticity": 1.8})


class InsertResult:
    def fetchone(self):
        return 101, datetime(2026, 7, 18, 12, 15, tzinfo=UTC)


class InsertOnlySession:
    def execute(self, statement, parameters):
        return InsertResult()


@pytest.mark.asyncio
async def test_od_quote_calls_ai_with_mapped_bid_prices(monkeypatch):
    ai_client = FakeAIClient()
    service = PricingService(ai_client=ai_client)
    monkeypatch.setattr(
        service,
        "_find_od_product",
        lambda request, db: {
            "id": 7,
            "base_price": 100_000,
            "seat_type": "ngoi_mem",
            "service_date": date(2026, 7, 19),
            "origin_name": "Ha Noi",
            "destination_name": "Da Nang",
        },
    )
    monkeypatch.setattr(
        service,
        "_load_segments",
        lambda od_product_id, seat_type, db: [
            {
                "segment_id": 11,
                "origin_name": "Ha Noi",
                "destination_name": "Hue",
                "remaining": 18,
                "bid_price": 200_000,
                "run_version": "run-1",
            },
            {
                "segment_id": 12,
                "origin_name": "Hue",
                "destination_name": "Da Nang",
                "remaining": 10,
                "bid_price": 100_000,
                "run_version": "run-1",
            },
        ],
    )
    monkeypatch.setattr(service, "_load_policy", lambda od_product_id, db: None)

    response = await service.create_pricing_quote_from_od(
        PricingQuoteRequest(
            origin="HN",
            destination="DAN",
            service_date="2026-07-19",
            seat_type="ngoi_mem",
        ),
        InsertOnlySession(),
    )

    assert [segment.bid_price for segment in ai_client.received_segments] == [200_000, 100_000]
    assert response.opportunity_cost == 300_000
    assert response.availability == 10
    assert response.decision == "rejected"
