from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.ai_pricing_client import AIServiceError
from backend.services.pricing_service import PricingService
from backend.views.pricing_view import (
    PricingQuoteODResponse,
    PricingQuoteRequest,
    PricingQuoteResponse,
)

router = APIRouter()


class ProductItemResponse(BaseModel):
    id: int
    trip_id: int
    origin_station_code: str
    destination_station_code: str
    seat_type: str
    base_price: float


@router.get("/pricing/products", response_model=list[ProductItemResponse])
async def get_all_products(db: Session = Depends(get_db)) -> list[ProductItemResponse]:
    """Lấy danh sách tất cả các sản phẩm OD phục vụ báo giá."""
    try:
        query = text("""
            SELECT
                od.id,
                od.trip_id,
                s_orig.code AS origin_station_code,
                s_dest.code AS destination_station_code,
                od.seat_type,
                od.base_price
            FROM od_products od
            JOIN stations s_orig ON od.origin_station_id = s_orig.id
            JOIN stations s_dest ON od.destination_station_id = s_dest.id
            ORDER BY od.id
        """)
        rows = db.execute(query).mappings().all()
        return [ProductItemResponse(**r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


def get_pricing_service() -> PricingService:
    return PricingService()


def _legacy_quote(od_product_id: int, service: PricingService, db: Session) -> PricingQuoteResponse:
    try:
        return service.create_pricing_quote(od_product_id=od_product_id, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.get("/pricing/quote", response_model=PricingQuoteResponse)
async def get_pricing_quote_standard(
    od_product_id: int = Query(..., description="ID cua san pham OD"),
    service: PricingService = Depends(get_pricing_service),
    db: Session = Depends(get_db),
) -> PricingQuoteResponse:
    """Backward-compatible quote endpoint by OD product id."""
    return _legacy_quote(od_product_id, service, db)


@router.get("/quote", response_model=PricingQuoteResponse)
async def get_pricing_quote_alias(
    od_product_id: int = Query(..., description="ID cua san pham OD"),
    service: PricingService = Depends(get_pricing_service),
    db: Session = Depends(get_db),
) -> PricingQuoteResponse:
    """Backward-compatible alias for callers that already know od_product_id."""
    return _legacy_quote(od_product_id, service, db)


@router.post("/quote", response_model=PricingQuoteODResponse)
async def create_pricing_quote_from_od(
    request: PricingQuoteRequest,
    service: PricingService = Depends(get_pricing_service),
    db: Session = Depends(get_db),
) -> PricingQuoteODResponse:
    """Map an OD request to segments and return an AI-generated price quote."""
    try:
        return await service.create_pricing_quote_from_od(request=request, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc
