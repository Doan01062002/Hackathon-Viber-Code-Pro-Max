import pytest


@pytest.mark.asyncio
async def test_legs_heatmap_success(client):
    response = await client.get("/api/v1/analytics/legs-heatmap?trip_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == 1
    assert "legs" in data
    assert len(data["legs"]) > 0

    first_leg = data["legs"][0]
    required_keys = {
        "segment_id",
        "sequence_no",
        "origin_station_code",
        "destination_station_code",
        "capacity",
        "remaining",
        "seat_type",
        "bid_price",
        "is_bottleneck",
    }
    assert required_keys.issubset(first_leg.keys())


@pytest.mark.asyncio
async def test_legs_heatmap_alias_success(client):
    response = await client.get("/api/v1/segments/load?trip_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == 1
    assert len(data["legs"]) > 0


@pytest.mark.asyncio
async def test_legs_heatmap_not_found(client):
    response = await client.get("/api/v1/analytics/legs-heatmap?trip_id=999999")
    assert response.status_code == 404
    assert "Không tìm thấy" in response.json()["detail"]


@pytest.mark.asyncio
async def test_forecast_success(client):
    response = await client.get("/api/v1/forecast?trip_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == 1
    assert "forecasts" in data
    assert "booking_curve" in data

    # Booking curve should cover 60 to 0 lead_days (61 points)
    assert len(data["booking_curve"]) == 61
    assert data["booking_curve"][0]["lead_days"] == 60
    assert data["booking_curve"][-1]["lead_days"] == 0


@pytest.mark.asyncio
async def test_forecast_alias_success(client):
    response = await client.get("/api/v1/analytics/forecast?trip_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == 1
    assert len(data["booking_curve"]) == 61


@pytest.mark.asyncio
async def test_forecast_with_seat_type_filter(client):
    response = await client.get("/api/v1/forecast?trip_id=1&seat_type=ngoi_mem")
    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == 1
    # Check that all forecasts in response match the ngoi_mem seat_type
    for item in data["forecasts"]:
        assert item["seat_type"] == "ngoi_mem"


@pytest.mark.asyncio
async def test_forecast_not_found(client):
    response = await client.get("/api/v1/forecast?trip_id=999999")
    assert response.status_code == 404
    assert "Không tìm thấy" in response.json()["detail"]
