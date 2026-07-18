import pytest


@pytest.mark.asyncio
async def test_get_coaches_success(client):
    """Kiểm tra lấy danh sách các toa tàu thành công."""
    response = await client.get("/api/v1/seats/coaches?trip_id=1")
    assert response.status_code == 200
    coaches = response.json()
    assert isinstance(coaches, list)
    assert len(coaches) > 0

    first_coach = coaches[0]
    assert "name" in first_coach
    assert "type" in first_coach
    assert "occupancy" in first_coach
    assert "coach_no" in first_coach

@pytest.mark.asyncio
async def test_get_coaches_not_found(client):
    """Kiểm tra lấy danh sách các toa của trip không tồn tại trả về 404."""
    response = await client.get("/api/v1/seats/coaches?trip_id=99999")
    assert response.status_code == 404
    assert "Không tìm thấy chuyến tàu" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_seat_layout_success(client):
    """Kiểm tra lấy sơ đồ ghế 2D của một toa thành công."""
    response = await client.get("/api/v1/seats/layout?trip_id=1&coach_no=01")
    assert response.status_code == 200
    layout = response.json()

    assert "route" in layout
    assert layout["coach"] == "Toa 01"
    assert layout["seat_type"] == "ngoi_mem"
    assert isinstance(layout["seats"], list)
    assert len(layout["seats"]) == 16  # 64 seats divided by 4 per row
    assert len(layout["seats"][0]) == 4
    assert isinstance(layout["seatLegend"], list)

@pytest.mark.asyncio
async def test_get_seat_layout_not_found(client):
    """Kiểm tra lấy sơ đồ ghế của toa không tồn tại trả về 404."""
    response = await client.get("/api/v1/seats/layout?trip_id=1&coach_no=99")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_gap_suggestions_success(client):
    """Kiểm tra lấy gợi ý khoảng trống thành công."""
    response = await client.get("/api/v1/seats/gap-suggestions?trip_id=1")
    assert response.status_code == 200
    suggestions = response.json()
    assert isinstance(suggestions, list)

    if len(suggestions) > 0:
        first_sug = suggestions[0]
        assert "route" in first_sug
        assert "seatType" in first_sug
        assert "benefit" in first_sug
        assert "priority" in first_sug
        assert "reason" in first_sug
