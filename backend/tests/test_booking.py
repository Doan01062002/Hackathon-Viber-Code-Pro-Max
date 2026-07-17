import pytest
from sqlalchemy import text
from backend.database import get_session_factory

@pytest.mark.asyncio
async def test_create_booking_hold_success(client):
    # 1. Đo lường tồn kho trước khi đặt vé
    db = get_session_factory()()
    try:
        # Lấy một chặng của sản phẩm 1
        seg_row = db.execute(text("""
            SELECT si.segment_id, si.remaining, odp.seat_type
            FROM od_product_segments ops
            JOIN od_products odp ON ops.od_product_id = odp.id
            JOIN segment_inventory si ON (ops.segment_id = si.segment_id AND odp.seat_type = si.seat_type)
            WHERE ops.od_product_id = 1
            LIMIT 1
        """)).fetchone()
        assert seg_row is not None
        seg_id, initial_remaining, seat_type = seg_row

        # 2. Thực hiện đặt vé giữ chỗ (Hold)
        response = await client.post("/api/v1/booking", json={
            "od_product_id": 1,
            "channel": "web"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "held"
        assert data["od_product_id"] == 1
        assert data["seat_id"] is None
        assert "booking_code" in data
        booking_id = data["booking_id"]

        # 3. Đo lường tồn kho sau khi giữ chỗ (phải giảm đi 1)
        db.expire_all()
        after_row = db.execute(
            text("SELECT remaining FROM segment_inventory WHERE segment_id = :sid AND seat_type = :st"),
            {"sid": seg_id, "st": seat_type}
        ).fetchone()
        assert after_row[0] == initial_remaining - 1

    finally:
        # Dọn dẹp dữ liệu để khôi phục tồn kho gốc
        if 'booking_id' in locals():
            # Hoàn trả tồn kho trước
            seg_rows = db.execute(
                text("SELECT segment_id FROM od_product_segments WHERE od_product_id = 1")
            ).fetchall()
            for r in seg_rows:
                db.execute(text("""
                    UPDATE segment_inventory 
                    SET remaining = remaining + 1 
                    WHERE segment_id = :sid AND seat_type = :st
                """), {"sid": r[0], "st": seat_type})
            
            # Xóa booking
            db.execute(text("DELETE FROM bookings WHERE id = :bid"), {"bid": booking_id})
            db.commit()
        db.close()


@pytest.mark.asyncio
async def test_confirm_booking_success(client):
    db = get_session_factory()()
    booking_id = None
    try:
        # 1. Tạo một giữ chỗ trước
        response = await client.post("/api/v1/booking", json={
            "od_product_id": 1
        })
        assert response.status_code == 201
        booking_id = response.json()["booking_id"]

        # 2. Xác nhận đặt vé
        confirm_resp = await client.post(f"/api/v1/booking/{booking_id}/confirm")
        assert confirm_resp.status_code == 200
        confirm_data = confirm_resp.json()
        assert confirm_data["status"] == "confirmed"
        assert confirm_data["seat_id"] is not None
        assert "coach_no" in confirm_data
        assert "seat_no" in confirm_data

        # Kiểm tra trạng thái booking trong DB
        db.expire_all()
        status_row = db.execute(
            text("SELECT status, seat_id FROM bookings WHERE id = :bid"),
            {"bid": booking_id}
        ).fetchone()
        assert status_row[0] == "confirmed"
        assert status_row[1] == confirm_data["seat_id"]

    finally:
        if booking_id:
            # Hoàn trả tồn kho (vì confirm không đổi tồn kho chặng thêm lần nữa, chỉ gán ghế)
            prod_row = db.execute(text("SELECT seat_type FROM od_products WHERE id = 1")).fetchone()
            seat_type = prod_row[0]
            seg_rows = db.execute(
                text("SELECT segment_id FROM od_product_segments WHERE od_product_id = 1")
            ).fetchall()
            for r in seg_rows:
                db.execute(text("""
                    UPDATE segment_inventory 
                    SET remaining = remaining + 1 
                    WHERE segment_id = :sid AND seat_type = :st
                """), {"sid": r[0], "st": seat_type})
            
            db.execute(text("DELETE FROM bookings WHERE id = :bid"), {"bid": booking_id})
            db.commit()
        db.close()


@pytest.mark.asyncio
async def test_booking_quota_exceeded(client):
    db = get_session_factory()()
    quota_id = None
    try:
        # Cài đặt hạn ngạch (quota = 0) cho sản phẩm 1
        res = db.execute(text("""
            INSERT INTO quotas (
                od_product_id, quota, calculated_at, run_version, is_active
            ) VALUES (
                1, 0, CURRENT_TIMESTAMP, 'TEST_QUOTA', TRUE
            ) RETURNING id
        """))
        quota_id = res.fetchone()[0]
        db.commit()

        # Thử đặt vé giữ chỗ
        response = await client.post("/api/v1/booking", json={
            "od_product_id": 1
        })
        # Phải trả về lỗi 400 do vượt quá quota
        assert response.status_code == 400
        assert "vượt quá hạn ngạch" in response.json()["detail"]

    finally:
        if quota_id:
            db.execute(text("DELETE FROM quotas WHERE id = :qid"), {"qid": quota_id})
            db.commit()
        db.close()


@pytest.mark.asyncio
async def test_release_expired_bookings(client):
    db = get_session_factory()()
    booking_id = None
    try:
        # 1. Chèn một booking giả lập đã hết hạn giữ chỗ (status = held, expires_at = 1 phút trước)
        # Giả lập tồn kho đã bị trừ đi 1 cho chặng
        prod_row = db.execute(text("SELECT seat_type FROM od_products WHERE id = 1")).fetchone()
        seat_type = prod_row[0]
        
        seg_rows = db.execute(
            text("SELECT segment_id FROM od_product_segments WHERE od_product_id = 1")
        ).fetchall()
        
        # Đọc tồn kho chặng trước khi trừ
        seg_id = seg_rows[0][0]
        before_val = db.execute(
            text("SELECT remaining FROM segment_inventory WHERE segment_id = :sid AND seat_type = :st"),
            {"sid": seg_id, "st": seat_type}
        ).fetchone()[0]

        # Trừ tồn kho chặng
        for r in seg_rows:
            db.execute(text("""
                UPDATE segment_inventory 
                SET remaining = remaining - 1 
                WHERE segment_id = :sid AND seat_type = :st
            """), {"sid": r[0], "st": seat_type})
        
        # Chèn booking hết hạn
        res = db.execute(text("""
            INSERT INTO bookings (
                booking_code, od_product_id, seat_id, status, channel, booked_price, booked_at, expires_at
            ) VALUES (
                'BK-EXPIRED', 1, NULL, 'held', 'web', 58000.0, CURRENT_TIMESTAMP - INTERVAL '20 minutes', CURRENT_TIMESTAMP - INTERVAL '5 minutes'
            ) RETURNING id
        """))
        booking_id = res.fetchone()[0]
        db.commit()

        # 2. Gọi API giải phóng giữ chỗ hết hạn
        response = await client.post("/api/v1/booking/release-expired")
        assert response.status_code == 200
        assert response.json()["released_count"] >= 1

        # 3. Xác minh tồn kho đã được cộng trả lại và status chuyển sang cancelled
        db.expire_all()
        status_row = db.execute(text("SELECT status FROM bookings WHERE id = :bid"), {"bid": booking_id}).fetchone()
        assert status_row[0] == "cancelled"

        after_val = db.execute(
            text("SELECT remaining FROM segment_inventory WHERE segment_id = :sid AND seat_type = :st"),
            {"sid": seg_id, "st": seat_type}
        ).fetchone()[0]
        assert after_val >= before_val

    finally:
        if booking_id:
            db.execute(text("DELETE FROM bookings WHERE id = :bid"), {"bid": booking_id})
            db.commit()
        db.close()
