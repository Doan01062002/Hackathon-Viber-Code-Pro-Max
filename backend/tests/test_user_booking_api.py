import pytest
from sqlalchemy import text

from backend.database import get_session_factory


@pytest.mark.asyncio
async def test_search_booking_products(client):
    response = await client.get(
        "/api/v1/booking/search",
        params={
            "origin": "HAN",
            "destination": "PHL",
            "service_date": "2024-01-01",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {item["seat_type"] for item in data} == {"ngoi_mem", "giuong_nam_k6"}
    assert all(item["availability"] >= 0 for item in data)


@pytest.mark.asyncio
async def test_booking_options_are_cascading_and_db_backed(client):
    response = await client.get(
        "/api/v1/booking/options",
        params={"origin": "HAN", "destination": "DAN"},
    )

    assert response.status_code == 200
    data = response.json()
    assert any(item["code"] == "DAN" for item in data["destinations"])
    assert data["departure_dates"][0] == "2024-01-01"
    assert data["departure_dates"][-1] == "2025-12-30"
    assert data["return_dates"] == []


@pytest.mark.asyncio
async def test_booking_seat_plan_uses_physical_seat_ids(client):
    response = await client.get("/api/v1/booking/products/1/seats")

    assert response.status_code == 200
    data = response.json()
    assert data["od_product_id"] == 1
    assert data["coaches"]
    assert data["coaches"][0]["seats"]
    assert data["coaches"][0]["seats"][0]["seat_id"] > 0
    assert data["segments"]
    assert data["segments"][0]["capacity"] >= data["segments"][0]["remaining"]
    assert data["coaches"][0]["seats"][0]["status"] in {
        "available",
        "held",
        "confirmed",
        "blocked",
    }


@pytest.mark.asyncio
async def test_booking_detail_by_code(client):
    db = get_session_factory()()
    try:
        booking_code = db.execute(
            text("""
                SELECT booking_code
                FROM bookings
                WHERE status = 'confirmed'
                ORDER BY id
                LIMIT 1
            """)
        ).scalar_one()
    finally:
        db.close()

    response = await client.get(f"/api/v1/booking/code/{booking_code}")

    assert response.status_code == 200
    data = response.json()
    assert data["booking_code"] == booking_code
    assert data["origin_code"] != data["destination_code"]
    assert data["departure_at"] < data["arrival_at"]
