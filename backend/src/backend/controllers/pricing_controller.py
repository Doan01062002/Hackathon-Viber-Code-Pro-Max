from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.pricing_service import PricingService
from backend.views.pricing_view import PricingQuoteResponse

router = APIRouter()


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
