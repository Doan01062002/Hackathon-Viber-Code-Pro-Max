import pytest
import asyncio
from sqlalchemy import text
from backend.database import get_session_factory


@pytest.mark.asyncio
async def test_end_to_end_integration_flow(client):
    """
    Test luồng tích hợp đầu-cuối (End-to-End Integration Flow):
    1. Gọi tối ưu hóa DLP ngầm (batch job) và đợi hoàn thành (BE-20.2).
    2. Kiểm tra Heatmap tải chặng (BE-20.1).
    3. Cấu hình Policy Guard mới (sàn/trần) (BE-20.4).
    4. Báo giá động OD và xác minh Policy Guard áp dụng chính xác.
    5. Tạo giữ chỗ (Hold Booking) và xác nhận đặt vé thành công (BE-20.1).
    6. Dọn dẹp dữ liệu test.
    """
    db = get_session_factory()()

    # Lấy segment_id, seat_type và od_product_id hợp lệ của trip 1
    seg_row = db.execute(text("SELECT id FROM segments WHERE trip_id = 1 LIMIT 1")).fetchone()
    seat_row = db.execute(text("SELECT code FROM seat_types LIMIT 1")).fetchone()
    od_row = db.execute(text("SELECT id FROM od_products WHERE trip_id = 1 LIMIT 1")).fetchone()
    assert seg_row is not None and seat_row is not None and od_row is not None
    od_id = od_row[0]

    # 0. Dọn dẹp sạch sẽ các dữ liệu chính sách/báo giá cũ liên quan đến od_id này để tránh tranh chấp chính sách
    db.execute(text("DELETE FROM price_quotes WHERE od_product_id = :od_id"), {"od_id": od_id})
    db.execute(text("DELETE FROM price_policies WHERE od_product_id = :od_id"), {"od_id": od_id})
    db.commit()

    run_version = None
    policy_id = None
    booking_id = None
    try:
        # ==========================================
        # BƯỚC 1: Chạy Tối ưu hóa Batch DLP
        # ==========================================
        response = await client.post("/api/v1/optimize/resolve", json={"trip_id": 1})
        assert response.status_code == 200
        job_data = response.json()
        assert "job_id" in job_data
        job_id = job_data["job_id"]

        # Polling đợi hoàn thành
        completed = False
        for _ in range(75):
            await asyncio.sleep(1.0)
            status_res = await client.get(f"/api/v1/optimize/resolve/jobs/{job_id}")
            status_data = status_res.json()
            if status_data["status"] == "completed":
                completed = True
                run_version = status_data["result"]["run_version"]
                break
        assert completed, "Optimization job timed out"

        # ==========================================
        # BƯỚC 2: Kiểm tra Heatmap Tải chặng
        # ==========================================
        response = await client.get("/api/v1/analytics/legs-heatmap?trip_id=1")
        assert response.status_code == 200
        heatmap_data = response.json()
        assert "legs" in heatmap_data
        assert len(heatmap_data["legs"]) > 0

        # ==========================================
        # BƯỚC 3: Cấu hình Policy Guard trần/sàn mới
        # ==========================================
        # Tạo chính sách giá hoạt động với max_step_change cực lớn để không bị giới hạn bước nhảy giá
        res = db.execute(
            text("""
                INSERT INTO price_policies (od_product_id, name, min_price, max_price, max_step_change, valid_from, status)
                VALUES (:od_id, 'Integration Policy Guard', 200000.00, 800000.00, 99999999.00, NOW() - INTERVAL '1 hour', 'active')
                RETURNING id
            """),
            {"od_id": od_id},
        )
        policy_id = res.fetchone()[0]
        db.commit()

        # ==========================================
        # BƯỚC 4: Báo giá động và kiểm tra Policy Guard
        # ==========================================
        response = await client.get(f"/api/v1/pricing/quote?od_product_id={od_id}")
        assert response.status_code == 200
        quote_data = response.json()
        assert quote_data["policy_id"] == policy_id
        assert quote_data["final_price"] >= 200000.00
        assert quote_data["final_price"] <= 800000.00

        # ==========================================
        # BƯỚC 5: Tạo Booking giữ chỗ & xác nhận đặt chỗ
        # ==========================================
        hold_data = {"od_product_id": od_id, "channel": "web"}
        response = await client.post("/api/v1/booking", json=hold_data)
        assert response.status_code == 201
        booking_data = response.json()
        booking_id = booking_data["booking_id"]
        assert booking_data["status"] == "held"

        # Xác nhận đặt vé (Confirm)
        response = await client.post(f"/api/v1/booking/{booking_id}/confirm")
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    finally:
        # Dọn dẹp dữ liệu tích hợp rác
        if booking_id:
            # Lấy seat_type và hoàn trả tồn kho chặng trước khi xóa để không làm hụt tồn kho của DB seeded
            prod_row = db.execute(
                text("SELECT seat_type FROM od_products WHERE id = :od_id"), {"od_id": od_id}
            ).fetchone()
            if prod_row:
                seat_type = prod_row[0]
                seg_rows = db.execute(
                    text("SELECT segment_id FROM od_product_segments WHERE od_product_id = :od_id"), {"od_id": od_id}
                ).fetchall()
                for r in seg_rows:
                    db.execute(
                        text("""
                            UPDATE segment_inventory
                            SET remaining = remaining + 1
                            WHERE segment_id = :sid AND seat_type = :st
                        """),
                        {"sid": r[0], "st": seat_type},
                    )
            db.execute(text("DELETE FROM bookings WHERE id = :bid"), {"bid": booking_id})
        if policy_id:
            db.execute(text("DELETE FROM price_quotes WHERE policy_id = :pid"), {"pid": policy_id})
            db.execute(text("DELETE FROM price_policies WHERE id = :pid"), {"pid": policy_id})
        if run_version:
            db.execute(text("DELETE FROM bid_prices WHERE run_version = :ver"), {"ver": run_version})
            db.execute(text("DELETE FROM quotas WHERE run_version = :ver"), {"ver": run_version})
            db.execute(text("DELETE FROM price_quotes WHERE run_version = :ver"), {"ver": run_version})
        db.commit()
        db.close()
