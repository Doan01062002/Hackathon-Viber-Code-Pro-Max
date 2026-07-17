import pytest
from sqlalchemy import text

from backend.controllers.pricing_controller import get_pricing_service
from backend.database import get_session_factory
from backend.views.pricing_view import PricingExplanation, PricingQuoteResponse


class FakeODPricingService:
    async def create_pricing_quote_from_od(self, request, db):
        return PricingQuoteResponse(
            quote_id=99,
            od_product_id=7,
            opportunity_cost=300_000,
            proposed_price=450_000,
            final_price=450_000,
            decision="accepted",
            explanation=PricingExplanation(
                base_opportunity_cost=300_000,
                markup_factor=1.5,
                applied_policies=[],
                bottleneck_segment_id=12,
                bottleneck_segment="Hue -> Da Nang",
                segment_bid_prices={"12": 300_000},
            ),
            expires_at="2026-07-18T12:15:00+00:00",
            origin="Ha Noi",
            destination="Da Nang",
            service_date="2026-07-19",
            seat_type=request.seat_type,
            availability=18,
        )


@pytest.mark.asyncio
async def test_quote_post_maps_frontend_contract(app, client):
    app.dependency_overrides[get_pricing_service] = lambda: FakeODPricingService()

    response = await client.post(
        "/api/v1/quote",
        json={
            "origin": "HN",
            "destination": "DAN",
            "service_date": "2026-07-19",
            "seat_type": "giuong_nam_k6",
        },
    )

    assert response.status_code == 200
    assert response.json()["quote_id"] == 99
    assert response.json()["availability"] == 18


@pytest.mark.asyncio
async def test_pricing_quote_success(client):
    # Test gọi báo giá thành công
    response = await client.get("/api/v1/pricing/quote?od_product_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["od_product_id"] == 1
    assert "quote_id" in data
    assert "opportunity_cost" in data
    assert "proposed_price" in data
    assert "final_price" in data
    assert data["decision"] == "accepted"
    assert "expires_at" in data
    assert "applied_policies" in data["explanation"]


@pytest.mark.asyncio
async def test_pricing_quote_alias_success(client):
    response = await client.get("/api/v1/quote?od_product_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["od_product_id"] == 1


@pytest.mark.asyncio
async def test_pricing_quote_not_found(client):
    response = await client.get("/api/v1/pricing/quote?od_product_id=999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_policy_guard_min_price(client):
    db = get_session_factory()()
    policy_id = None
    try:
        # Chèn một chính sách sàn cực cao (5,000,000) đang active cho od_product_id = 1
        result = db.execute(
            text("""
            INSERT INTO price_policies (
                od_product_id, name, min_price, max_price, max_step_change, status, valid_from
            ) VALUES (
                1, 'TEST_MIN_PRICE', 5000000.0, 10000000.0, 99999999.0, 'active', CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ) RETURNING id
        """)
        )
        policy_id = result.fetchone()[0]
        db.commit()

        # Gọi API báo giá
        response = await client.get("/api/v1/pricing/quote?od_product_id=1")
        assert response.status_code == 200
        data = response.json()

        # Giá trị final_price phải bị ép sàn lên 5,000,000
        assert float(data["final_price"]) == 5000000.0
        assert "MIN_PRICE_ENFORCED" in data["explanation"]["applied_policies"]
        assert data["policy_id"] == policy_id

    finally:
        if policy_id:
            # Xóa các báo giá phát sinh dùng policy này trước để tránh khóa ngoại
            db.execute(text("DELETE FROM price_quotes WHERE policy_id = :pid"), {"pid": policy_id})
            db.execute(text("DELETE FROM price_policies WHERE id = :pid"), {"pid": policy_id})
            db.commit()
        db.close()


@pytest.mark.asyncio
async def test_policy_guard_max_price(client):
    db = get_session_factory()()
    policy_id = None
    try:
        # Chèn một chính sách trần cực thấp (1,000) đang active cho od_product_id = 1
        result = db.execute(
            text("""
            INSERT INTO price_policies (
                od_product_id, name, min_price, max_price, max_step_change, status, valid_from
            ) VALUES (
                1, 'TEST_MAX_PRICE', 500.0, 1000.0, 99999999.0, 'active', CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ) RETURNING id
        """)
        )
        policy_id = result.fetchone()[0]
        db.commit()

        # Gọi API báo giá
        response = await client.get("/api/v1/pricing/quote?od_product_id=1")
        assert response.status_code == 200
        data = response.json()

        # Giá trị final_price phải bị ép trần xuống 1000
        assert float(data["final_price"]) == 1000.0
        assert "MAX_PRICE_ENFORCED" in data["explanation"]["applied_policies"]
        assert data["policy_id"] == policy_id

    finally:
        if policy_id:
            db.execute(text("DELETE FROM price_quotes WHERE policy_id = :pid"), {"pid": policy_id})
            db.execute(text("DELETE FROM price_policies WHERE id = :pid"), {"pid": policy_id})
            db.commit()
        db.close()


@pytest.mark.asyncio
async def test_policy_guard_max_step_change(client):
    db = get_session_factory()()
    policy_id = None
    quote_ids_to_del = []
    try:
        # 1. Chèn chính sách giới hạn bước nhảy giá là 5,000
        result = db.execute(
            text("""
            INSERT INTO price_policies (
                od_product_id, name, min_price, max_price, max_step_change, status, valid_from
            ) VALUES (
                1, 'TEST_STEP_LIMIT', 10000.0, 9000000.0, 5000.0, 'active', CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ) RETURNING id
        """)
        )
        policy_id = result.fetchone()[0]

        # 2. Chèn một báo giá trước đó có final_price = 10000.0 (rất thấp để ép giá tăng vượt ngưỡng)
        res_quote = db.execute(
            text("""
            INSERT INTO price_quotes (
                od_product_id, policy_id, opportunity_cost, proposed_price, final_price, decision, explanation
            ) VALUES (
                1, :pid, 0.0, 10000.0, 10000.0, 'accepted', '{}'
            ) RETURNING id
        """),
            {"pid": policy_id},
        )
        quote_ids_to_del.append(res_quote.fetchone()[0])
        db.commit()

        # 3. Gọi API báo giá
        # Vì giá đề xuất của sản phẩm 1 (~1,200,000) chênh lệch > 5,000 so với 10,000,
        # nên final_price sẽ bị giới hạn ở 15,000 (10,000 + 5,000)
        response = await client.get("/api/v1/pricing/quote?od_product_id=1")
        assert response.status_code == 200
        data = response.json()

        # Lưu quote mới để xóa sau
        quote_ids_to_del.append(data["quote_id"])

        assert float(data["final_price"]) == 15000.0
        assert "MAX_STEP_CHANGE_CAPPED" in data["explanation"]["applied_policies"]

    finally:
        if quote_ids_to_del:
            db.execute(text("DELETE FROM price_quotes WHERE id = ANY(:ids)"), {"ids": list(quote_ids_to_del)})
        if policy_id:
            db.execute(text("DELETE FROM price_policies WHERE id = :pid"), {"pid": policy_id})
        db.commit()
        db.close()


@pytest.mark.asyncio
async def test_get_all_products_success(client):
    """Kiểm tra việc truy vấn toàn bộ sản phẩm OD thành công."""
    response = await client.get("/api/v1/pricing/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "origin_station_code" in data[0]
    assert "destination_station_code" in data[0]
