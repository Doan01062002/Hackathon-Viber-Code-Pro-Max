"""Controller mỏng expose trực tiếp forecast/optimize của ai-service qua HTTP AIClient.

Khác với optimize_controller (chạy batch, ghi DB, tích hợp ai_service in-process),
controller này chỉ proxy sang microservice ai-service để preview/debug nhanh kết quả
Khối 1 (forecast) và Khối 2 (optimize) mà không đụng tới database.
"""

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.ai_client import AIClient

router = APIRouter(prefix="/ai", tags=["ai"])

# Singleton client — giữ cache bid price/optimization theo service_date giữa các request
_ai_client = AIClient()


def get_ai_client() -> AIClient:
    return _ai_client


class ForecastRequest(BaseModel):
    service_date: str = Field(..., description="Ngày chạy tàu (ISO YYYY-MM-DD)")


class OptimizeRequest(BaseModel):
    service_date: str = Field(..., description="Ngày chạy tàu (ISO YYYY-MM-DD)")


@router.post("/forecast")
async def forecast(request: ForecastRequest) -> dict:
    """Khối 1 — gọi ai-service dự báo nhu cầu (λ̂, p10/p50/p90) cho ngày chạy tàu."""
    try:
        return await get_ai_client().get_forecast(request.service_date)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"ai-service không khả dụng: {exc}")


@router.post("/optimize")
async def optimize(request: OptimizeRequest) -> dict:
    """Khối 2 — gọi ai-service giải DLP bid price (có cache theo service_date)."""
    try:
        return await get_ai_client().get_optimization(request.service_date)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"ai-service không khả dụng: {exc}")
