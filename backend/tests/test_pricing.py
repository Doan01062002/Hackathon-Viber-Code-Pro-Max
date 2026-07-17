import pytest
from sqlalchemy import text
from backend.database import get_session_factory

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
        result = db.execute(text("""
            INSERT INTO price_policies (
                od_product_id, name, min_price, max_price, max_step_change, status, valid_from
            ) VALUES (
                1, 'TEST_MIN_PRICE', 5000000.0, 10000000.0, 99999999.0, 'active', CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ) RETURNING id
        """))
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
        result = db.execute(text("""
            INSERT INTO price_policies (
                od_product_id, name, min_price, max_price, max_step_change, status, valid_from
            ) VALUES (
                1, 'TEST_MAX_PRICE', 500.0, 1000.0, 99999999.0, 'active', CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ) RETURNING id
        """))
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
        result = db.execute(text("""
            INSERT INTO price_policies (
                od_product_id, name, min_price, max_price, max_step_change, status, valid_from
            ) VALUES (
                1, 'TEST_STEP_LIMIT', 10000.0, 9000000.0, 5000.0, 'active', CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ) RETURNING id
        """))
        policy_id = result.fetchone()[0]
        
        # 2. Chèn một báo giá trước đó có final_price = 10000.0 (rất thấp để ép giá tăng vượt ngưỡng)
        res_quote = db.execute(text("""
            INSERT INTO price_quotes (
                od_product_id, policy_id, opportunity_cost, proposed_price, final_price, decision, explanation
            ) VALUES (
                1, :pid, 0.0, 10000.0, 10000.0, 'accepted', '{}'
            ) RETURNING id
        """), {"pid": policy_id})
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
