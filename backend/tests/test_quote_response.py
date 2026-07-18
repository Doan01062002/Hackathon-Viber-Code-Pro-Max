import pytest

from backend.controllers.pricing_controller import get_pricing_service
from backend.services.ai_pricing_client import AIServiceError
from backend.views.pricing_view import PricingExplanation, PricingQuoteODResponse

REQUEST_BODY = {
    "origin": "HN",
    "destination": "DAN",
    "service_date": "2026-07-19",
    "seat_type": "giuong_nam_k6",
}


class SuccessfulPricingService:
    async def create_pricing_quote_from_od(self, request, db):
        return PricingQuoteODResponse(
            quote_id=2048,
            od_product_id=15,
            policy_id=3,
            opportunity_cost=350_000,
            proposed_price=420_000,
            final_price=420_000,
            decision="accepted",
            explanation=PricingExplanation(
                base_opportunity_cost=350_000,
                markup_factor=1.2,
                applied_policies=["STANDARD_MARKUP"],
                bottleneck_segment_id=101,
                bottleneck_segment="Hue -> Da Nang",
                segment_bid_prices={"100": 100_000, "101": 250_000},
            ),
            expires_at="2026-07-18T12:15:00+00:00",
            origin="Ha Noi",
            destination="Da Nang",
            service_date="2026-07-19",
            seat_type=request.seat_type,
            availability=18,
        )


class MissingODPricingService:
    async def create_pricing_quote_from_od(self, request, db):
        raise ValueError("Khong tim thay san pham OD phu hop voi yeu cau")


class UnavailableAIPricingService:
    async def create_pricing_quote_from_od(self, request, db):
        raise AIServiceError("AI pricing service khong kha dung")


@pytest.mark.asyncio
async def test_quote_returns_complete_be_07_4_response(app, client):
    app.dependency_overrides[get_pricing_service] = lambda: SuccessfulPricingService()

    response = await client.post("/api/v1/quote", json=REQUEST_BODY)

    assert response.status_code == 200
    assert response.json() == {
        "quote_id": 2048,
        "od_product_id": 15,
        "policy_id": 3,
        "opportunity_cost": 350_000.0,
        "proposed_price": 420_000.0,
        "final_price": 420_000.0,
        "decision": "accepted",
        "explanation": {
            "base_opportunity_cost": 350_000.0,
            "markup_factor": 1.2,
            "applied_policies": ["STANDARD_MARKUP"],
            "bottleneck_segment_id": 101,
            "bottleneck_segment": "Hue -> Da Nang",
            "segment_bid_prices": {"100": 100_000.0, "101": 250_000.0},
        },
        "expires_at": "2026-07-18T12:15:00+00:00",
        "origin": "Ha Noi",
        "destination": "Da Nang",
        "service_date": "2026-07-19",
        "seat_type": "giuong_nam_k6",
        "availability": 18,
    }


@pytest.mark.asyncio
async def test_quote_returns_404_when_od_cannot_be_mapped(app, client):
    app.dependency_overrides[get_pricing_service] = lambda: MissingODPricingService()

    response = await client.post("/api/v1/quote", json=REQUEST_BODY)

    assert response.status_code == 404
    assert response.json()["detail"] == "Khong tim thay san pham OD phu hop voi yeu cau"


@pytest.mark.asyncio
async def test_quote_returns_502_when_ai_service_is_unavailable(app, client):
    app.dependency_overrides[get_pricing_service] = lambda: UnavailableAIPricingService()

    response = await client.post("/api/v1/quote", json=REQUEST_BODY)

    assert response.status_code == 502
    assert response.json()["detail"] == "AI pricing service khong kha dung"


@pytest.mark.asyncio
async def test_quote_returns_422_for_invalid_request(client):
    invalid_body = {key: value for key, value in REQUEST_BODY.items() if key != "seat_type"}

    response = await client.post("/api/v1/quote", json=invalid_body)

    assert response.status_code == 422
