from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class AuditService:
    def get_audit_logs(
        self,
        db: Session,
        actor: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Truy vấn danh sách nhật ký kiểm toán (audit logs) từ DB."""
        query = "SELECT id, actor, action, entity_type, entity_id, before_data, after_data, created_at FROM audit_logs WHERE 1=1"
        params = {"limit": limit, "offset": offset}

        if actor:
            query += " AND actor = :actor"
            params["actor"] = actor

        if action:
            query += " AND action = :action"
            params["action"] = action

        if entity_type:
            query += " AND entity_type = :entity_type"
            params["entity_type"] = entity_type

        query += " ORDER BY id DESC LIMIT :limit OFFSET :offset"

        rows = db.execute(text(query), params).fetchall()
        result = []
        for r in rows:
            result.append(
                {
                    "id": r[0],
                    "actor": r[1],
                    "action": r[2],
                    "entity_type": r[3],
                    "entity_id": r[4],
                    "before_data": r[5],  # SQLAlchemy sẽ tự động trả về kiểu dict cho JSONB
                    "after_data": r[6],
                    "created_at": r[7].isoformat() if r[7] else None,
                }
            )
        return result
