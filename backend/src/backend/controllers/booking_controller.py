from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.booking_service import BookingService
from backend.views.booking_view import (
    BookingConfirmResponse,
    BookingCreateRequest,
    BookingDetailResponse,
    BookingOptionsResponse,
    BookingResponse,
    BookingSearchItem,
    BookingSeatPlanResponse,
)

router = APIRouter()


def get_booking_service() -> BookingService:
    return BookingService()


@router.get("/booking/options", response_model=BookingOptionsResponse)
async def get_booking_options(
    origin: str = Query(..., min_length=2, max_length=120),
    destination: str | None = Query(None, min_length=2, max_length=120),
    service: BookingService = Depends(get_booking_service),
    db: Session = Depends(get_db),
) -> BookingOptionsResponse:
    try:
        return service.get_booking_options(origin, destination, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.get("/booking/search", response_model=list[BookingSearchItem])
async def search_booking_products(
    origin: str = Query(..., min_length=2, max_length=120),
    destination: str = Query(..., min_length=2, max_length=120),
    service_date: date = Query(...),
    seat_type: str | None = Query(None, min_length=2, max_length=30),
    service: BookingService = Depends(get_booking_service),
    db: Session = Depends(get_db),
) -> list[BookingSearchItem]:
    try:
        return service.search_products(origin, destination, service_date, seat_type, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.get("/booking/products/{od_product_id}/seats", response_model=BookingSeatPlanResponse)
async def get_booking_seat_plan(
    od_product_id: int,
    service: BookingService = Depends(get_booking_service),
    db: Session = Depends(get_db),
) -> BookingSeatPlanResponse:
    try:
        return service.get_seat_plan(od_product_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.get("/booking/code/{booking_code}", response_model=BookingDetailResponse)
async def get_booking_detail(
    booking_code: str,
    service: BookingService = Depends(get_booking_service),
    db: Session = Depends(get_db),
) -> BookingDetailResponse:
    try:
        return service.get_booking_detail(booking_code, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.post("/booking", response_model=BookingResponse, status_code=201)
async def create_booking_hold_standard(
    request: BookingCreateRequest,
    service: BookingService = Depends(get_booking_service),
    db: Session = Depends(get_db),
) -> BookingResponse:
    try:
        return service.create_booking_hold(request=request, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.post("/booking/{booking_id}/confirm", response_model=BookingConfirmResponse)
async def confirm_booking(
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
    db: Session = Depends(get_db),
) -> BookingConfirmResponse:
    try:
        return service.confirm_booking(booking_id=booking_id, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.post("/booking/release-expired")
async def release_expired_bookings(
    service: BookingService = Depends(get_booking_service),
    db: Session = Depends(get_db),
):
    try:
        count = service.release_expired_bookings(db=db)
        return {"status": "success", "released_count": count}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc
