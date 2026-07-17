from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.pricing_service import PricingService
from backend.views.pricing_view import PricingQuoteResponse

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


@router.get("/pricing/quote", response_model=PricingQuoteResponse)
async def get_pricing_quote_standard(
    od_product_id: int = Query(..., description="ID của sản phẩm OD"),
    service: PricingService = Depends(get_pricing_service),
    db: Session = Depends(get_db),
) -> PricingQuoteResponse:
    """Yêu cầu báo giá vé động cho sản phẩm OD, tự động lưu vết vào price_quotes."""
    try:
        return service.create_pricing_quote(od_product_id=od_product_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


@router.get("/quote", response_model=PricingQuoteResponse)
async def get_pricing_quote_alias(
    od_product_id: int = Query(..., description="ID của sản phẩm OD"),
    service: PricingService = Depends(get_pricing_service),
    db: Session = Depends(get_db),
) -> PricingQuoteResponse:
    """Alias cho API báo giá vé động (quote)."""
    try:
        return service.create_pricing_quote(od_product_id=od_product_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
