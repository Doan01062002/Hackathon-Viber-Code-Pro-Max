from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.services.simulation_service import SimulationService

router = APIRouter()


class SimulationCompareResponse(BaseModel):
    trip_id: int = Field(..., description="ID của chuyến tàu")
    historical_revenue: float = Field(..., description="Doanh thu thực tế lịch sử")
    simulated_revenue: float = Field(..., description="Doanh thu mô phỏng của AI")
    revenue_lift_pct: float = Field(..., description="Tỷ lệ tăng trưởng doanh thu (%)")
    historical_passenger_km: float = Field(..., description="Sản lượng khách-km thực tế lịch sử")
    simulated_passenger_km: float = Field(..., description="Sản lượng khách-km mô phỏng của AI")
    passenger_km_lift_pct: float = Field(..., description="Tỷ lệ tăng trưởng sản lượng khách-km (%)")


def get_simulation_service() -> SimulationService:
    return SimulationService()


@router.get("/simulation/compare", response_model=SimulationCompareResponse)
async def compare_policy(
    trip_id: int = Query(..., description="ID của chuyến tàu cần mô phỏng"),
    policy_id: Optional[int] = Query(None, description="ID chính sách giá tùy chọn để áp dụng"),
    service: SimulationService = Depends(get_simulation_service),
    db: Session = Depends(get_db),
) -> SimulationCompareResponse:
    """So sánh doanh thu và sản lượng khách-km thực tế lịch sử (bảng bookings)
    với kịch bản giá mô phỏng của AI (bảng price_quotes).
    """
    try:
        res = service.compare_policy(db=db, trip_id=trip_id, policy_id=policy_id)
        return SimulationCompareResponse(**res)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
