import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class PolicyService:
    def get_policies(
        self, db: Session, od_product_id: int | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        """Lấy danh sách các chính sách giá."""
        query = "SELECT id, od_product_id, name, min_price, max_price, max_step_change, valid_from, valid_to, status, created_by, approved_by, created_at, updated_at FROM price_policies WHERE 1=1"
        params = {}

        if od_product_id is not None:
            query += " AND od_product_id = :od_product_id"
            params["od_product_id"] = od_product_id

        if status is not None:
            query += " AND status = :status"
            params["status"] = status

        query += " ORDER BY id DESC"

        rows = db.execute(text(query), params).fetchall()
        result = []
        for r in rows:
            result.append(
                {
                    "id": r[0],
                    "od_product_id": r[1],
                    "name": r[2],
                    "min_price": float(r[3]),
                    "max_price": float(r[4]),
                    "max_step_change": float(r[5]),
                    "valid_from": r[6].isoformat() if r[6] else None,
                    "valid_to": r[7].isoformat() if r[7] else None,
                    "status": r[8],
                    "created_by": r[9],
                    "approved_by": r[10],
                    "created_at": r[11].isoformat() if r[11] else None,
                    "updated_at": r[12].isoformat() if r[12] else None,
                }
            )
        return result

    def update_policy(
        self,
        db: Session,
        policy_id: int,
        actor: str,
        name: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        max_step_change: float | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Cập nhật chính sách giá và ghi audit log."""
        # 1. Tìm chính sách hiện tại
        row = db.execute(
            text("""
                SELECT id, od_product_id, name, min_price, max_price, max_step_change, valid_from, valid_to, status, created_by, approved_by
                FROM price_policies WHERE id = :policy_id
            """),
            {"policy_id": policy_id},
        ).fetchone()

        if not row:
            raise ValueError(f"Không tìm thấy chính sách giá với ID {policy_id}")

        before_data = {
            "id": row[0],
            "od_product_id": row[1],
            "name": row[2],
            "min_price": float(row[3]),
            "max_price": float(row[4]),
            "max_step_change": float(row[5]),
            "valid_from": row[6].isoformat() if row[6] else None,
            "valid_to": row[7].isoformat() if row[7] else None,
            "status": row[8],
            "created_by": row[9],
            "approved_by": row[10],
        }

        # 2. Chuẩn bị giá trị cập nhật mới
        new_name = name if name is not None else row[2]
        new_min_price = min_price if min_price is not None else float(row[3])
        new_max_price = max_price if max_price is not None else float(row[4])
        new_max_step_change = max_step_change if max_step_change is not None else float(row[5])
        new_status = status if status is not None else row[8]

        # Kiểm tra ràng buộc max_price >= min_price
        if new_max_price < new_min_price:
            raise ValueError("Giá trị trần (max_price) không được nhỏ hơn giá trị sàn (min_price)")

        if new_status not in ("draft", "active", "inactive"):
            raise ValueError("Trạng thái chính sách không hợp lệ (phải là 'draft', 'active', hoặc 'inactive')")

        # 3. Cập nhật vào DB
        db.execute(
            text("""
                UPDATE price_policies
                SET name = :name,
                    min_price = :min_price,
                    max_price = :max_price,
                    max_step_change = :max_step_change,
                    status = :status,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :policy_id
            """),
            {
                "policy_id": policy_id,
                "name": new_name,
                "min_price": new_min_price,
                "max_price": new_max_price,
                "max_step_change": new_max_step_change,
                "status": new_status,
            },
        )

        after_data = before_data.copy()
        after_data.update(
            {
                "name": new_name,
                "min_price": new_min_price,
                "max_price": new_max_price,
                "max_step_change": new_max_step_change,
                "status": new_status,
            }
        )

        # 4. Ghi audit log thay đổi
        db.execute(
            text("""
                INSERT INTO audit_logs (actor, action, entity_type, entity_id, before_data, after_data)
                VALUES (:actor, :action, :entity_type, :entity_id, :before_data, :after_data)
            """),
            {
                "actor": actor,
                "action": "UPDATE_POLICY",
                "entity_type": "price_policy",
                "entity_id": str(policy_id),
                "before_data": json.dumps(before_data),
                "after_data": json.dumps(after_data),
            },
        )

        db.commit()

        # Trả về kết quả mới cập nhật
        return after_data
