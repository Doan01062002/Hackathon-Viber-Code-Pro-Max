import pytest
from sqlalchemy import text

from backend.database import get_session_factory


@pytest.mark.asyncio
async def test_simulation_compare_success(client):
    """Kiểm tra API so sánh kịch bản mô phỏng chạy thành công cho chuyến tàu hợp lệ."""
    response = await client.get("/api/v1/simulation/compare?trip_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == 1
    assert "historical_revenue" in data
    assert "simulated_revenue" in data
    assert "revenue_lift_pct" in data
    assert "historical_passenger_km" in data
    assert "simulated_passenger_km" in data
    assert "passenger_km_lift_pct" in data

    # Đảm bảo các kiểu dữ liệu và giá trị hợp lý
    assert isinstance(data["historical_revenue"], (int, float))
    assert isinstance(data["simulated_revenue"], (int, float))
    assert isinstance(data["revenue_lift_pct"], (int, float))


@pytest.mark.asyncio
async def test_simulation_compare_invalid_trip(client):
    """Kiểm tra API trả về lỗi 400 khi chuyến tàu không tồn tại."""
    response = await client.get("/api/v1/simulation/compare?trip_id=999999")
    assert response.status_code == 400
    assert "Không tìm thấy" in response.json()["detail"]


@pytest.mark.asyncio
async def test_simulation_compare_with_policy(client):
    """Kiểm tra API so sánh mô phỏng khi truyền thêm ID chính sách giá (policy_id)."""
    db = get_session_factory()()
    policy_id = None
    try:
        # 1. Tạo một chính sách giá nháp để chạy thử nghiệm
        res = db.execute(
            text("""
                INSERT INTO price_policies (od_product_id, name, min_price, max_price, max_step_change, valid_from, status)
                VALUES (1, 'Test Simulation Policy', 100000.00, 900000.00, 50000.00, NOW(), 'active')
                RETURNING id
            """)
        )
        policy_id = res.fetchone()[0]
        db.commit()

        # 2. Gọi API với policy_id vừa tạo
        response = await client.get(f"/api/v1/simulation/compare?trip_id=1&policy_id={policy_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["trip_id"] == 1
        assert "simulated_revenue" in data
        assert "revenue_lift_pct" in data

    finally:
        # 3. Dọn dẹp chính sách giá nháp
        if policy_id:
            db.execute(text("DELETE FROM price_policies WHERE id = :pid"), {"pid": policy_id})
            db.commit()
        db.close()
