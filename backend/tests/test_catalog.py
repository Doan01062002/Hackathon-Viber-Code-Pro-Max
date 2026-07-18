import pytest


@pytest.mark.asyncio
async def test_catalog_returns_reference_data(client):
    response = await client.get("/api/v1/catalog")

    assert response.status_code == 200
    data = response.json()
    assert data["stations"]
    assert data["seat_types"]
    assert data["service_date_min"] <= data["service_date_max"]
    assert {"id", "code", "name", "display_order"} <= set(data["stations"][0])
