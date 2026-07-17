import pytest
from sqlalchemy import text

from backend.database import get_session_factory


@pytest.mark.asyncio
async def test_get_policies_rbac_success(client):
    """Kiểm tra việc lấy chính sách thành công khi gửi header x-user-role hợp lệ."""
    headers = {"x-user-role": "revenue_manager"}
    response = await client.get("/api/v1/policy/limits", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_policies_rbac_denied(client):
    """Kiểm tra việc lấy chính sách bị từ chối khi gửi header x-user-role không hợp lệ hoặc thiếu."""
    # 1. Gửi vai trò không được phép
    headers = {"x-user-role": "passenger"}
    response = await client.get("/api/v1/policy/limits", headers=headers)
    assert response.status_code == 403
    assert "Quyền truy cập bị từ chối" in response.json()["detail"]

    # 2. Thiếu Header x-user-role
    response = await client.get("/api/v1/policy/limits")
    assert response.status_code == 422  # Validation Error của FastAPI


@pytest.mark.asyncio
async def test_update_policy_rbac_success(client):
    """Kiểm tra cập nhật chính sách thành công với vai trò được phép (revenue_manager), lưu audit log."""
    db = get_session_factory()()
    policy_id = None
    try:
        # 1. Tạo chính sách nháp
        res = db.execute(
            text("""
                INSERT INTO price_policies (od_product_id, name, min_price, max_price, max_step_change, valid_from, status)
                VALUES (1, 'Draft Policy For Update', 100000.00, 500000.00, 50000.00, NOW(), 'draft')
                RETURNING id
            """)
        )
        policy_id = res.fetchone()[0]
        db.commit()

        # 2. Gửi yêu cầu cập nhật hợp lệ
        headers = {"x-user-role": "revenue_manager"}
        update_data = {
            "name": "Updated Policy Name",
            "min_price": 120000.00,
            "max_price": 480000.00,
            "max_step_change": 40000.00,
            "status": "active"
        }
        response = await client.put(f"/api/v1/policy/limits/{policy_id}", json=update_data, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Policy Name"
        assert data["min_price"] == 120000.00
        assert data["max_price"] == 480000.00
        assert data["status"] == "active"

        # 3. Xác minh audit log được tạo tự động
        db.expire_all()
        audit_row = db.execute(
            text("SELECT COUNT(*) FROM audit_logs WHERE actor = 'revenue_manager' AND action = 'UPDATE_POLICY' AND entity_id = :pid"),
            {"pid": str(policy_id)}
        ).fetchone()
        assert audit_row[0] > 0

    finally:
        # Dọn dẹp chính sách và audit log nháp
        if policy_id:
            db.execute(text("DELETE FROM audit_logs WHERE entity_id = :pid"), {"pid": str(policy_id)})
            db.execute(text("DELETE FROM price_policies WHERE id = :pid"), {"pid": policy_id})
            db.commit()
        db.close()


@pytest.mark.asyncio
async def test_update_policy_rbac_denied(client):
    """Kiểm tra việc cập nhật chính sách bị chặn đối với các vai trò không được phép sửa (như evaluator)."""
    db = get_session_factory()()
    policy_id = None
    try:
        # 1. Tạo chính sách nháp
        res = db.execute(
            text("""
                INSERT INTO price_policies (od_product_id, name, min_price, max_price, max_step_change, valid_from, status)
                VALUES (1, 'Draft Policy Denied Test', 100000.00, 500000.00, 50000.00, NOW(), 'draft')
                RETURNING id
            """)
        )
        policy_id = res.fetchone()[0]
        db.commit()

        # 2. Gửi vai trò không hợp lệ (evaluator)
        headers = {"x-user-role": "evaluator"}
        update_data = {"min_price": 150000.00}
        response = await client.put(f"/api/v1/policy/limits/{policy_id}", json=update_data, headers=headers)
        assert response.status_code == 403

    finally:
        if policy_id:
            db.execute(text("DELETE FROM price_policies WHERE id = :pid"), {"pid": policy_id})
            db.commit()
        db.close()


@pytest.mark.asyncio
async def test_update_policy_invalid_constraints(client):
    """Kiểm tra việc cập nhật chính sách trả về lỗi 400 khi vi phạm ràng buộc sàn > trần."""
    db = get_session_factory()()
    policy_id = None
    try:
        # 1. Tạo chính sách nháp
        res = db.execute(
            text("""
                INSERT INTO price_policies (od_product_id, name, min_price, max_price, max_step_change, valid_from, status)
                VALUES (1, 'Draft Policy Constraint Test', 100000.00, 500000.00, 50000.00, NOW(), 'draft')
                RETURNING id
            """)
        )
        policy_id = res.fetchone()[0]
        db.commit()

        # 2. Gửi yêu cầu cập nhật vi phạm min_price > max_price (sàn lớn hơn trần)
        headers = {"x-user-role": "revenue_manager"}
        update_data = {
            "min_price": 600000.00,
            "max_price": 400000.00
        }
        response = await client.put(f"/api/v1/policy/limits/{policy_id}", json=update_data, headers=headers)
        assert response.status_code == 400
        assert "không được nhỏ hơn" in response.json()["detail"]

    finally:
        if policy_id:
            db.execute(text("DELETE FROM price_policies WHERE id = :pid"), {"pid": policy_id})
            db.commit()
        db.close()
