import asyncio

import pytest
from sqlalchemy import text

from backend.database import get_session_factory


@pytest.mark.asyncio
async def test_optimize_resolve_success(client):
    db = get_session_factory()()
    run_version = None
    try:
        # 1. Gửi yêu cầu chạy tối ưu hóa bất đồng bộ cho trip 1
        response = await client.post("/api/v1/optimize/resolve", json={"trip_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "running"
        job_id = data["job_id"]

        # 2. Polling truy vấn trạng thái job cho đến khi hoàn thành (tối đa 75 giây)
        success = False
        result_data = None
        for _ in range(75):
            await asyncio.sleep(1.0)
            status_response = await client.get(f"/api/v1/optimize/resolve/jobs/{job_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()
            if status_data["status"] == "completed":
                success = True
                result_data = status_data["result"]
                break
            elif status_data["status"] == "failed":
                pytest.fail(f"Job failed with error: {status_data['error']}")

        assert success, "Job did not complete within timeout"
        assert result_data is not None
        assert result_data["status"] == "success"
        run_version = result_data["run_version"]

        # 3. Xác minh dữ liệu trong DB
        db.expire_all()

        # Kiểm tra demand_forecasts
        fc_rows = db.execute(
            text("""
                SELECT COUNT(*) FROM demand_forecasts
                WHERE od_product_id IN (SELECT id FROM od_products WHERE trip_id = 1)
            """)
        ).fetchone()
        assert fc_rows[0] > 0

        # Kiểm tra bid_prices
        bp_rows = db.execute(
            text("SELECT COUNT(*) FROM bid_prices WHERE run_version = :ver AND is_active = TRUE"), {"ver": run_version}
        ).fetchone()
        assert bp_rows[0] > 0

        # Kiểm tra quotas
        quota_rows = db.execute(
            text("SELECT COUNT(*) FROM quotas WHERE run_version = :ver AND is_active = TRUE"), {"ver": run_version}
        ).fetchone()
        assert quota_rows[0] > 0

        # Kiểm tra price_quotes
        pq_rows = db.execute(
            text("SELECT COUNT(*) FROM price_quotes WHERE run_version = :ver"), {"ver": run_version}
        ).fetchone()
        assert pq_rows[0] > 0

        # Kiểm tra gap_combinations (Khối 2 Lớp B)
        gap_rows = db.execute(
            text("SELECT COUNT(*) FROM gap_combinations WHERE run_version = :ver AND is_active = TRUE"),
            {"ver": run_version},
        ).fetchone()
        assert gap_rows[0] > 0

        # Ghế và OD gợi ý phải cùng loại chỗ — nếu ánh xạ seat_index -> seats.id lệch thì
        # bất biến này gãy trước tiên.
        mismatched = db.execute(
            text("""
                SELECT COUNT(*) FROM gap_combinations g
                JOIN seats s ON g.seat_id = s.id
                JOIN od_products o ON g.suggested_od_product_id = o.id
                WHERE g.run_version = :ver AND s.seat_type <> o.seat_type
            """),
            {"ver": run_version},
        ).fetchone()
        assert mismatched[0] == 0

    finally:
        # Dọn dẹp dữ liệu của run_version này để giữ database sạch
        if run_version:
            db.execute(
                text(
                    "DELETE FROM demand_forecasts WHERE od_product_id IN (SELECT id FROM od_products WHERE trip_id = 1)"
                )
            )
            db.execute(text("DELETE FROM bid_prices WHERE run_version = :ver"), {"ver": run_version})
            db.execute(text("DELETE FROM quotas WHERE run_version = :ver"), {"ver": run_version})
            db.execute(text("DELETE FROM price_quotes WHERE run_version = :ver"), {"ver": run_version})
            db.execute(text("DELETE FROM gap_combinations WHERE run_version = :ver"), {"ver": run_version})
            db.commit()
        db.close()


@pytest.mark.asyncio
async def test_optimize_resolve_invalid_trip(client):
    response = await client.post("/api/v1/optimize/resolve", json={"trip_id": 999999})
    assert response.status_code == 400
    assert "Không tìm thấy" in response.json()["detail"]
