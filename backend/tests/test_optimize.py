import pytest
from sqlalchemy import text
from backend.database import get_session_factory

@pytest.mark.asyncio
async def test_optimize_resolve_success(client):
    db = get_session_factory()()
    run_version = None
    try:
        # 1. Gọi API chạy tối ưu hóa cho trip 1
        response = await client.post("/api/v1/optimize/resolve", json={
            "trip_id": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "run_version" in data
        assert data["quotas_updated_count"] > 0
        assert data["bid_prices_updated_count"] > 0
        run_version = data["run_version"]

        # 2. Xác minh dữ liệu trong DB
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
            text("SELECT COUNT(*) FROM bid_prices WHERE run_version = :ver AND is_active = TRUE"),
            {"ver": run_version}
        ).fetchone()
        assert bp_rows[0] > 0

        # Kiểm tra quotas
        quota_rows = db.execute(
            text("SELECT COUNT(*) FROM quotas WHERE run_version = :ver AND is_active = TRUE"),
            {"ver": run_version}
        ).fetchone()
        assert quota_rows[0] > 0

        # Kiểm tra price_quotes
        pq_rows = db.execute(
            text("SELECT COUNT(*) FROM price_quotes WHERE run_version = :ver"),
            {"ver": run_version}
        ).fetchone()
        assert pq_rows[0] > 0

    finally:
        # Dọn dẹp dữ liệu của run_version này để giữ database sạch
        if run_version:
            db.execute(
                text("DELETE FROM demand_forecasts WHERE od_product_id IN (SELECT id FROM od_products WHERE trip_id = 1)")
            )
            db.execute(text("DELETE FROM bid_prices WHERE run_version = :ver"), {"ver": run_version})
            db.execute(text("DELETE FROM quotas WHERE run_version = :ver"), {"ver": run_version})
            db.execute(text("DELETE FROM price_quotes WHERE run_version = :ver"), {"ver": run_version})
            db.commit()
        db.close()


@pytest.mark.asyncio
async def test_optimize_resolve_invalid_trip(client):
    response = await client.post("/api/v1/optimize/resolve", json={
        "trip_id": 999999
    })
    assert response.status_code == 400
    assert "Không tìm thấy" in response.json()["detail"]
