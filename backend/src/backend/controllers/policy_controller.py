from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.services.policy_service import PolicyService

router = APIRouter()


class PolicyResponse(BaseModel):
    id: int
    od_product_id: Optional[int]
    name: str
    min_price: float
    max_price: float
    max_step_change: float
    valid_from: Optional[str]
    valid_to: Optional[str]
    status: str
    created_by: Optional[str]
    approved_by: Optional[str]


class PolicyUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Tên chính sách")
    min_price: Optional[float] = Field(None, description="Giá tối thiểu (sàn)")
    max_price: Optional[float] = Field(None, description="Giá tối đa (trần)")
    max_step_change: Optional[float] = Field(None, description="Mức thay đổi giá bước tối đa")
    status: Optional[str] = Field(None, description="Trạng thái chính sách (draft, active, inactive)")


def get_policy_service() -> PolicyService:
    return PolicyService()


def verify_role(allowed_roles: List[str]):
    """FastAPI Dependency để kiểm tra vai trò người dùng trong Header."""
    def check_role(x_user_role: str = Header(..., description="Vai trò của người dùng thực hiện yêu cầu")):
        if x_user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Quyền truy cập bị từ chối: Vai trò '{x_user_role}' không được phép thực hiện hành động này."
            )
        return x_user_role
    return check_role


@router.get("/policy/limits", response_model=List[PolicyResponse])
async def get_policies(
    od_product_id: Optional[int] = Query(None, description="Lọc theo ID sản phẩm OD"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái chính sách"),
    user_role: str = Depends(verify_role(["revenue_manager", "dispatcher", "it_integrator", "evaluator"])),
    service: PolicyService = Depends(get_policy_service),
    db: Session = Depends(get_db),
) -> List[PolicyResponse]:
    """Lấy danh sách các chính sách giới hạn giá (Yêu cầu RBAC: mọi vai trò hợp lệ)."""
    try:
        policies = service.get_policies(db=db, od_product_id=od_product_id, status=status)
        return [PolicyResponse(**p) for p in policies]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


@router.put("/policy/limits/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: int,
    request: PolicyUpdateRequest,
    user_role: str = Depends(verify_role(["revenue_manager", "it_integrator"])),
    service: PolicyService = Depends(get_policy_service),
    db: Session = Depends(get_db),
) -> PolicyResponse:
    """Cập nhật giới hạn chính sách giá (Yêu cầu RBAC: chỉ revenue_manager hoặc it_integrator)."""
    try:
        updated_policy = service.update_policy(
            db=db,
            policy_id=policy_id,
            actor=user_role,
            name=request.name,
            min_price=request.min_price,
            max_price=request.max_price,
            max_step_change=request.max_step_change,
            status=request.status
        )
        return PolicyResponse(**updated_policy)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
