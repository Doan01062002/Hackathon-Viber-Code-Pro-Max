import pytest
from sqlalchemy import text

from backend.database import get_session_factory


@pytest.mark.asyncio
async def test_get_audit_logs_rbac_success(client):
    """Kiểm tra truy vấn danh sách audit logs thành công với vai trò hợp lệ."""
    headers = {"x-user-role": "revenue_manager"}
    response = await client.get("/api/v1/audit/logs", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_audit_logs_rbac_denied(client):
    """Kiểm tra truy vấn audit logs bị từ chối với vai trò không hợp lệ."""
    headers = {"x-user-role": "passenger"}
    response = await client.get("/api/v1/audit/logs", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_audit_logs_filtering(client):
    """Kiểm tra việc lọc nhật ký audit log theo actor, action và entity_type."""
    db = get_session_factory()()
    try:
        # 1. Thêm một bản ghi audit log giả lập
        db.execute(
            text("""
                INSERT INTO audit_logs (actor, action, entity_type, entity_id, before_data, after_data)
                VALUES ('test_actor_xyz', 'TEST_ACTION_XYZ', 'test_entity', '999', '{"a": 1}', '{"a": 2}')
            """)
        )
        db.commit()

        # 2. Gọi API lọc theo actor và action vừa tạo
        headers = {"x-user-role": "it_integrator"}
        response = await client.get(
            "/api/v1/audit/logs?actor=test_actor_xyz&action=TEST_ACTION_XYZ",
            headers=headers
        )
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) > 0
        assert logs[0]["actor"] == "test_actor_xyz"
        assert logs[0]["action"] == "TEST_ACTION_XYZ"
        assert logs[0]["before_data"] == {"a": 1}
        assert logs[0]["after_data"] == {"a": 2}

    finally:
        # 3. Dọn dẹp bản ghi test
        db.execute(text("DELETE FROM audit_logs WHERE actor = 'test_actor_xyz'"))
        db.commit()
        db.close()
