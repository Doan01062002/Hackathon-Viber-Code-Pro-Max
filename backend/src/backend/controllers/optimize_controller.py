from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.optimize_service import OptimizeService

router = APIRouter()

class OptimizeRequest(BaseModel):
    trip_id: int = Field(..., description="ID của chuyến tàu cần chạy tối ưu hóa")

class OptimizeResponse(BaseModel):
    status: str = Field(..., description="Trạng thái xử lý (success / error)")
    resolved_at: str = Field(..., description="Thời điểm hoàn thành giải tối ưu")
    run_version: str = Field(..., description="Phiên bản chạy (run_version) mới được kích hoạt")
    quotas_updated_count: int = Field(..., description="Số lượng bản ghi quotas đã được tạo mới")
    bid_prices_updated_count: int = Field(..., description="Số lượng bản ghi bid_prices đã được tạo mới")
    message: str = Field(..., description="Thông điệp kết quả")

def get_optimize_service() -> OptimizeService:
    return OptimizeService()

@router.post("/optimize/resolve", response_model=OptimizeResponse)
async def resolve_optimization_batch(
    request: OptimizeRequest,
    service: OptimizeService = Depends(get_optimize_service),
    db: Session = Depends(get_db),
) -> OptimizeResponse:
    """Chạy quy trình dự báo (Forecasting) -> tối ưu phân bổ (DLP) -> định giá động (Pricing)
    và kích hoạt hoán đổi nguyên tử (atomic swap) phiên bản hoạt động.
    """
    try:
        res = service.run_optimization_batch(trip_id=request.trip_id, db=db)
        return OptimizeResponse(**res)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
