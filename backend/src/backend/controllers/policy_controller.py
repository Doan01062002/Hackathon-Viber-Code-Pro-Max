from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.policy_service import PolicyService

router = APIRouter()


class PolicyResponse(BaseModel):
    id: int
    od_product_id: int | None
    name: str
    min_price: float
    max_price: float
    max_step_change: float
    valid_from: str | None
    valid_to: str | None
    status: str
    created_by: str | None
    approved_by: str | None


class PolicyUpdateRequest(BaseModel):
    name: str | None = Field(None, description="Tên chính sách")
    min_price: float | None = Field(None, description="Giá tối thiểu (sàn)")
    max_price: float | None = Field(None, description="Giá tối đa (trần)")
    max_step_change: float | None = Field(None, description="Mức thay đổi giá bước tối đa")
    status: str | None = Field(None, description="Trạng thái chính sách (draft, active, inactive)")


def get_policy_service() -> PolicyService:
    return PolicyService()


def verify_role(allowed_roles: list[str]):
    """FastAPI Dependency để kiểm tra vai trò người dùng trong Header."""

    def check_role(x_user_role: str = Header(..., description="Vai trò của người dùng thực hiện yêu cầu")):
        if x_user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Quyền truy cập bị từ chối: Vai trò '{x_user_role}' không được phép thực hiện hành động này.",
            )
        return x_user_role

    return check_role


@router.get("/policy/limits", response_model=list[PolicyResponse])
async def get_policies(
    od_product_id: int | None = Query(None, description="Lọc theo ID sản phẩm OD"),
    status: str | None = Query(None, description="Lọc theo trạng thái chính sách"),
    user_role: str = Depends(verify_role(["revenue_manager", "dispatcher", "it_integrator", "evaluator"])),
    service: PolicyService = Depends(get_policy_service),
    db: Session = Depends(get_db),
) -> list[PolicyResponse]:
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
            status=request.status,
        )
        return PolicyResponse(**updated_policy)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
