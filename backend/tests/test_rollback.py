import pytest
from sqlalchemy import text

from backend.database import get_session_factory


@pytest.mark.asyncio
async def test_get_versions_success(client):
    """Kiểm tra việc truy vấn danh sách các phiên bản chạy tối ưu hóa."""
    db = get_session_factory()()
    try:
        # Lấy một segment_id và seat_type hợp lệ của trip 1 để tránh lỗi khóa ngoại
        seg_row = db.execute(text("SELECT id FROM segments WHERE trip_id = 1 LIMIT 1")).fetchone()
        seat_row = db.execute(text("SELECT code FROM seat_types LIMIT 1")).fetchone()
        assert seg_row is not None and seat_row is not None
        seg_id = seg_row[0]
        seat_type = seat_row[0]

        # 1. Thêm một bản ghi bid_price mock
        db.execute(
            text("""
                INSERT INTO bid_prices (segment_id, seat_type, bid_price, remaining_capacity, run_version, is_active, calculated_at)
                VALUES (:seg_id, :seat_type, 15000.00, 10, 'ver-test-rollback-list', FALSE, NOW())
            """),
            {"seg_id": seg_id, "seat_type": seat_type},
        )
        db.commit()

        # 2. Gọi API truy vấn
        response = await client.get("/api/v1/optimize/resolve/versions?trip_id=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        versions = [v["run_version"] for v in data]
        assert "ver-test-rollback-list" in versions

    finally:
        db.rollback()  # Đảm bảo rollback transaction bị lỗi nếu có
        db.execute(text("DELETE FROM bid_prices WHERE run_version = 'ver-test-rollback-list'"))
        db.commit()
        db.close()


@pytest.mark.asyncio
async def test_rollback_success(client):
    """Kiểm tra khôi phục (rollback) thành công về phiên bản cấu hình tối ưu trước đó."""
    db = get_session_factory()()
    try:
        # Lấy segment_id, seat_type và od_product_id hợp lệ của trip 1
        seg_row = db.execute(text("SELECT id FROM segments WHERE trip_id = 1 LIMIT 1")).fetchone()
        seat_row = db.execute(text("SELECT code FROM seat_types LIMIT 1")).fetchone()
        od_row = db.execute(text("SELECT id FROM od_products WHERE trip_id = 1 LIMIT 1")).fetchone()
        assert seg_row is not None and seat_row is not None and od_row is not None
        seg_id = seg_row[0]
        seat_type = seat_row[0]
        od_id = od_row[0]

        # 1. Tạo 2 phiên bản chạy (cũ và mới) cho segment và od_product hợp lệ
        db.execute(
            text("""
                INSERT INTO bid_prices (segment_id, seat_type, bid_price, remaining_capacity, run_version, is_active, calculated_at)
                VALUES
                    (:seg_id, :seat_type, 50000.00, 10, 'ver-rollback-prev', FALSE, NOW() - INTERVAL '1 hour'),
                    (:seg_id, :seat_type, 75000.00, 10, 'ver-rollback-curr', TRUE, NOW())
            """),
            {"seg_id": seg_id, "seat_type": seat_type},
        )
        db.execute(
            text("""
                INSERT INTO quotas (od_product_id, quota, run_version, is_active, calculated_at)
                VALUES
                    (:od_id, 20, 'ver-rollback-prev', FALSE, NOW() - INTERVAL '1 hour'),
                    (:od_id, 15, 'ver-rollback-curr', TRUE, NOW())
            """),
            {"od_id": od_id},
        )
        db.commit()

        # 2. Gọi API thực hiện Rollback về phiên bản cũ ('ver-rollback-prev')
        rollback_data = {"trip_id": 1, "target_version": "ver-rollback-prev"}
        response = await client.post("/api/v1/optimize/resolve/rollback", json=rollback_data)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # 3. Xác minh trong DB: 'ver-rollback-prev' phải chuyển thành TRUE, 'ver-rollback-curr' thành FALSE
        db.expire_all()

        bp_prev = db.execute(
            text("SELECT is_active FROM bid_prices WHERE run_version = 'ver-rollback-prev' LIMIT 1")
        ).fetchone()
        bp_curr = db.execute(
            text("SELECT is_active FROM bid_prices WHERE run_version = 'ver-rollback-curr' LIMIT 1")
        ).fetchone()

        assert bp_prev[0] is True
        assert bp_curr[0] is False

        q_prev = db.execute(
            text("SELECT is_active FROM quotas WHERE run_version = 'ver-rollback-prev' LIMIT 1")
        ).fetchone()
        q_curr = db.execute(
            text("SELECT is_active FROM quotas WHERE run_version = 'ver-rollback-curr' LIMIT 1")
        ).fetchone()

        assert q_prev[0] is True
        assert q_curr[0] is False

    finally:
        db.rollback()
        db.execute(text("DELETE FROM bid_prices WHERE run_version IN ('ver-rollback-prev', 'ver-rollback-curr')"))
        db.execute(text("DELETE FROM quotas WHERE run_version IN ('ver-rollback-prev', 'ver-rollback-curr')"))
        db.commit()
        db.close()


@pytest.mark.asyncio
async def test_rollback_invalid_version(client):
    """Kiểm tra API trả về lỗi 400 khi rollback về phiên bản không tồn tại."""
    rollback_data = {"trip_id": 1, "target_version": "ver-does-not-exist-12345"}
    response = await client.post("/api/v1/optimize/resolve/rollback", json=rollback_data)
    assert response.status_code == 400
    assert "Không tìm thấy phiên bản" in response.json()["detail"]
