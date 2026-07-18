"""Controller mỏng expose forecast/optimize của ai_service qua AIClient.

Khác với optimize_controller (chạy batch, ghi DB), controller này chỉ preview/debug nhanh
kết quả Khối 1 (forecast) và Khối 2 (optimize) mà không đụng tới database.
"""

from ai_service.engine import InvalidRequestError, ModelNotReadyError
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.ai_client import AIClient

router = APIRouter(prefix="/ai", tags=["ai"])

# Singleton client — dùng chung AIEngine (đã nạp model.pkl và cache nghiệm tối ưu).
_ai_client = AIClient()


def get_ai_client() -> AIClient:
    return _ai_client


class ForecastRequest(BaseModel):
    service_date: str = Field(..., description="Ngày chạy tàu (ISO YYYY-MM-DD)")


class OptimizeRequest(BaseModel):
    service_date: str = Field(..., description="Ngày chạy tàu (ISO YYYY-MM-DD)")


@router.post("/forecast")
async def forecast(request: ForecastRequest) -> dict:
    """Khối 1 — dự báo nhu cầu (λ̂, p10/p50/p90) cho ngày chạy tàu."""
    try:
        return await get_ai_client().get_forecast(request.service_date)
    except InvalidRequestError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/optimize")
async def optimize(request: OptimizeRequest) -> dict:
    """Khối 2 — giải DLP bid price (engine cache theo fingerprint của λ̂)."""
    try:
        return await get_ai_client().get_optimization(request.service_date)
    except InvalidRequestError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
