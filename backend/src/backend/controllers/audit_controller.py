from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from backend.database import get_db
from backend.services.audit_service import AuditService
from backend.controllers.policy_controller import verify_role

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: int = Field(..., description="ID của bản ghi audit log")
    actor: str = Field(..., description="Người thực hiện hành động")
    action: str = Field(..., description="Hành động được thực hiện")
    entity_type: str = Field(..., description="Loại đối tượng chịu tác động")
    entity_id: Optional[str] = Field(None, description="ID của đối tượng chịu tác động")
    before_data: Optional[Dict[str, Any]] = Field(None, description="Dữ liệu trước thay đổi")
    after_data: Optional[Dict[str, Any]] = Field(None, description="Dữ liệu sau thay đổi")
    created_at: str = Field(..., description="Thời điểm ghi log")


def get_audit_service() -> AuditService:
    return AuditService()


@router.get("/audit/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    actor: Optional[str] = Query(None, description="Lọc theo người thực hiện"),
    action: Optional[str] = Query(None, description="Lọc theo hành động"),
    entity_type: Optional[str] = Query(None, description="Lọc theo loại đối tượng"),
    limit: int = Query(100, ge=1, le=1000, description="Số lượng bản ghi tối đa trả về"),
    offset: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua"),
    user_role: str = Depends(verify_role(["revenue_manager", "it_integrator", "evaluator", "dispatcher"])),
    service: AuditService = Depends(get_audit_service),
    db: Session = Depends(get_db),
) -> List[AuditLogResponse]:
    """Truy vấn danh sách nhật ký kiểm toán hệ thống (Yêu cầu RBAC: mọi vai trò hợp lệ)."""
    try:
        logs = service.get_audit_logs(
            db=db,
            actor=actor,
            action=action,
            entity_type=entity_type,
            limit=limit,
            offset=offset
        )
        return [AuditLogResponse(**log) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
