from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.ai_pricing_client import AIServiceError
from backend.services.pricing_service import PricingService
from backend.views.pricing_view import PricingQuoteRequest, PricingQuoteResponse

router = APIRouter()


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


@router.post("/quote", response_model=PricingQuoteResponse)
async def create_pricing_quote_from_od(
    request: PricingQuoteRequest,
    service: PricingService = Depends(get_pricing_service),
    db: Session = Depends(get_db),
) -> PricingQuoteResponse:
    """Map an OD request to segments and return an AI-generated price quote."""
    try:
        return await service.create_pricing_quote_from_od(request=request, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc
