
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.analytics_service import AnalyticsService
from backend.views.analytics_view import ForecastResponse, LegHeatmapResponse

router = APIRouter()


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


# --- 1. Legs Heatmap Endpoints (Alias segments/load & analytics/legs-heatmap) ---


@router.get("/analytics/legs-heatmap", response_model=LegHeatmapResponse)
async def get_legs_heatmap_standard(
    trip_id: int = Query(..., description="ID của chuyến tàu"),
    service: AnalyticsService = Depends(get_analytics_service),
    db: Session = Depends(get_db),
) -> LegHeatmapResponse:
    """Lấy biểu đồ nhiệt tải chặng của chuyến tàu (Legs Heatmap)."""
    try:
        return service.get_legs_heatmap(trip_id=trip_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


@router.get("/segments/load", response_model=LegHeatmapResponse)
async def get_legs_heatmap_alias(
    trip_id: int = Query(..., description="ID của chuyến tàu"),
    service: AnalyticsService = Depends(get_analytics_service),
    db: Session = Depends(get_db),
) -> LegHeatmapResponse:
    """Alias cho API lấy biểu đồ nhiệt tải chặng (segments/load)."""
    try:
        return service.get_legs_heatmap(trip_id=trip_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


# --- 2. Forecast Endpoints (Alias forecast & analytics/forecast) ---


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast_standard(
    trip_id: int = Query(..., description="ID của chuyến tàu"),
    seat_type: str | None = Query(None, description="Lọc theo loại chỗ (ngoi_mem hoặc giuong_nam_k6)"),
    service: AnalyticsService = Depends(get_analytics_service),
    db: Session = Depends(get_db),
) -> ForecastResponse:
    """Lấy dữ liệu dự báo nhu cầu và biểu đồ tiến độ đặt vé lũy kế (Booking Curve)."""
    try:
        return service.get_forecast_data(trip_id=trip_id, seat_type=seat_type, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


@router.get("/analytics/forecast", response_model=ForecastResponse)
async def get_forecast_alias(
    trip_id: int = Query(..., description="ID của chuyến tàu"),
    seat_type: str | None = Query(None, description="Lọc theo loại chỗ (ngoi_mem hoặc giuong_nam_k6)"),
    service: AnalyticsService = Depends(get_analytics_service),
    db: Session = Depends(get_db),
) -> ForecastResponse:
    """Alias cho API lấy dữ liệu dự báo nhu cầu (analytics/forecast)."""
    try:
        return service.get_forecast_data(trip_id=trip_id, seat_type=seat_type, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
