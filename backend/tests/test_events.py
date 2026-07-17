import asyncio

import pytest
from sqlalchemy import text

from backend.database import get_session_factory
from backend.redis_client import get_redis_client


@pytest.mark.asyncio
async def test_publish_event_success(client):
    # 1. Gửi sự kiện qua API
    payload = {"event_type": "booking_created", "trip_id": 1, "payload": {"booking_id": 100, "seats": ["A1"]}}

    response = await client.post("/api/v1/events", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert "event_id" in data

    # 2. Xác minh tin nhắn có trong Redis Stream
    redis_conn = get_redis_client()
    # Đọc từ đầu stream (0-0)
    streams = redis_conn.xread({"srrm:event_stream": "0-0"})
    assert len(streams) > 0

    stream_name, messages = streams[0]
    assert stream_name == "srrm:event_stream"

    # Tìm tin nhắn tương ứng với event_id vừa nhận
    target_msg = next((msg for msg in messages if msg[0] == data["event_id"]), None)
    assert target_msg is not None
    assert target_msg[1]["event_type"] == "booking_created"
    assert target_msg[1]["trip_id"] == "1"


@pytest.mark.asyncio
async def test_worker_debounce_re_solve(client):
    import pandas as pd
    from ai_service.forecasting import Forecaster

    # Sao lưu predict gốc và monkeypatch để tránh deadlock trong thread
    original_predict = Forecaster.predict

    def mock_predict(self, df):
        out = pd.DataFrame(index=df.index)
        if "od_id" in df.columns:
            out["od_id"] = df["od_id"]
        if "seat_type" in df.columns:
            out["seat_type"] = df["seat_type"]
        out["lambda_hat"] = 5.0
        out["p10"] = 4.0
        out["p50"] = 5.0
        out["p90"] = 6.0
        return out

    Forecaster.predict = mock_predict

    # Clear MockRedis stream to avoid event pollution from other tests
    redis_conn = get_redis_client()
    if hasattr(redis_conn, "streams"):
        redis_conn.streams.clear()

    from backend.worker import EventWorker

    worker = EventWorker(debounce_seconds=1.0)
    worker.start()

    # Chờ 0.2s cho worker khởi động
    await asyncio.sleep(0.2)

    db = get_session_factory()()

    # Dọn dẹp bất kỳ dữ liệu cũ nào của trip 2 từ các phiên chạy trước để tránh nhiễu test
    db.execute(
        text("DELETE FROM demand_forecasts WHERE od_product_id IN (SELECT id FROM od_products WHERE trip_id = 2)")
    )
    db.execute(
        text("""
        DELETE FROM bid_prices WHERE run_version IN (
            SELECT DISTINCT q.run_version FROM quotas q
            JOIN od_products p ON q.od_product_id = p.id
            WHERE p.trip_id = 2
        )
    """)
    )
    db.execute(
        text("""
        DELETE FROM price_quotes WHERE run_version IN (
            SELECT DISTINCT q.run_version FROM quotas q
            JOIN od_products p ON q.od_product_id = p.id
            WHERE p.trip_id = 2
        )
    """)
    )
    db.execute(
        text("""
        DELETE FROM quotas WHERE od_product_id IN (
            SELECT id FROM od_products WHERE trip_id = 2
        )
    """)
    )
    db.commit()

    # Lấy phiên bản chạy active hiện tại cho trip 2 (nếu có)
    initial_version_row = db.execute(
        text("""
            SELECT q.run_version FROM quotas q
            JOIN od_products p ON q.od_product_id = p.id
            WHERE p.trip_id = 2 AND q.is_active = TRUE
            LIMIT 1
        """)
    ).fetchone()
    initial_version = initial_version_row[0] if initial_version_row else None

    try:
        # Gửi liên tiếp 3 sự kiện cho chuyến tàu 2 trong khoảng thời gian rất ngắn
        payload1 = {"event_type": "booking_created", "trip_id": 2, "payload": {"id": 101}}
        payload2 = {"event_type": "booking_created", "trip_id": 2, "payload": {"id": 102}}
        payload3 = {"event_type": "booking_cancelled", "trip_id": 2, "payload": {"id": 101}}

        # Gửi sự kiện 1
        resp1 = await client.post("/api/v1/events", json=payload1)
        assert resp1.status_code == 202

        # Chờ 0.2s rồi gửi sự kiện 2
        await asyncio.sleep(0.2)
        resp2 = await client.post("/api/v1/events", json=payload2)
        assert resp2.status_code == 202

        # Chờ 0.2s rồi gửi sự kiện 3
        await asyncio.sleep(0.2)
        resp3 = await client.post("/api/v1/events", json=payload3)
        assert resp3.status_code == 202

        # Với debounce 1s, Worker sẽ hoãn chạy tối ưu hóa đến giây thứ 1.4.
        # Chờ đợi re-solve hoàn thành bằng cơ chế polling (max 90 giây)
        print("Waiting for worker to process debounced events...")
        success = False
        for i in range(90):
            await asyncio.sleep(1.0)
            db.expire_all()
            new_version_row = db.execute(
                text("""
                    SELECT q.run_version FROM quotas q
                    JOIN od_products p ON q.od_product_id = p.id
                    WHERE p.trip_id = 2 AND q.is_active = TRUE
                    LIMIT 1
                """)
            ).fetchone()
            new_version = new_version_row[0] if new_version_row else None
            if new_version and new_version != initial_version:
                success = True
                print(f"Re-solve detected after {i + 1} seconds! New version: {new_version}")
                break

        assert success, "Re-solve did not complete within timeout"

        # 2. Đếm số lượng run_version được tạo ra cho trip 2 (chỉ được là 1 phiên bản mới duy nhất)
        # do cơ chế debounce gom 3 sự kiện lại làm 1
        versions_created = db.execute(
            text("""
                SELECT DISTINCT q.run_version FROM quotas q
                JOIN od_products p ON q.od_product_id = p.id
                WHERE p.trip_id = 2 AND q.run_version != :init
            """),
            {"init": initial_version or ""},
        ).fetchall()

        # Nếu database ban đầu trống, tổng số phiên bản mới phải là 1.
        # Nếu có chạy trước đó, số phiên bản khác initial_version cũng phải tăng lên đúng 1 bản ghi mới.
        # Ta dọn dẹp các phiên bản mới tạo sau test.
        assert len(versions_created) == 1

    finally:
        # Dọn dẹp dữ liệu của các run_version mới tạo trong quá trình test
        db.expire_all()
        new_versions = db.execute(
            text("""
                SELECT DISTINCT q.run_version FROM quotas q
                JOIN od_products p ON q.od_product_id = p.id
                WHERE p.trip_id = 2 AND q.run_version != :init
            """),
            {"init": initial_version or ""},
        ).fetchall()

        for row in new_versions:
            ver = row[0]
            db.execute(
                text(
                    "DELETE FROM demand_forecasts WHERE od_product_id IN (SELECT id FROM od_products WHERE trip_id = 2)"
                )
            )
            db.execute(text("DELETE FROM bid_prices WHERE run_version = :v"), {"v": ver})
            db.execute(text("DELETE FROM quotas WHERE run_version = :v"), {"v": ver})
            db.execute(text("DELETE FROM price_quotes WHERE run_version = :v"), {"v": ver})

        db.commit()
        db.close()

        try:
            worker.stop()
        except Exception:
            pass

        Forecaster.predict = original_predict
