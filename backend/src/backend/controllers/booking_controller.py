from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.booking_service import BookingService
from backend.services.combined_booking_service import CombinedBookingService
from backend.views.booking_view import (
    BookingConfirmResponse,
    BookingCreateRequest,
    BookingDetailResponse,
    BookingOptionsResponse,
    BookingResponse,
    BookingSearchItem,
    BookingSeatPlanResponse,
)
from backend.views.combined_booking_view import (
    CombinedBookingCreateRequest,
    CombinedBookingResponse,
    CombinedCancelResponse,
    CombinedJourneyOptionsResponse,
)

router = APIRouter()


def get_booking_service() -> BookingService:
    return BookingService()


def get_combined_booking_service() -> CombinedBookingService:
    return CombinedBookingService()


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


@router.get("/booking/combined-options", response_model=CombinedJourneyOptionsResponse)
async def get_combined_booking_options(
    origin: str = Query(..., min_length=2, max_length=120),
    destination: str = Query(..., min_length=2, max_length=120),
    service_date: date = Query(...),
    seat_type: str | None = Query(None, min_length=2, max_length=30),
    max_transfers: int = Query(2, ge=1, le=3),
    service: CombinedBookingService = Depends(get_combined_booking_service),
    db: Session = Depends(get_db),
) -> CombinedJourneyOptionsResponse:
    try:
        return service.search_options(
            origin=origin,
            destination=destination,
            service_date=service_date,
            seat_type=seat_type,
            max_transfers=max_transfers,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.post("/booking/combined", response_model=CombinedBookingResponse, status_code=201)
async def create_combined_booking_hold(
    request: CombinedBookingCreateRequest,
    service: CombinedBookingService = Depends(get_combined_booking_service),
    db: Session = Depends(get_db),
) -> CombinedBookingResponse:
    try:
        return service.create_hold(request=request, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.get("/booking/combined/{group_code}", response_model=CombinedBookingResponse)
async def get_combined_booking_detail(
    group_code: str,
    service: CombinedBookingService = Depends(get_combined_booking_service),
    db: Session = Depends(get_db),
) -> CombinedBookingResponse:
    try:
        return service.get_detail(group_code=group_code, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.post("/booking/combined/{group_code}/confirm", response_model=CombinedBookingResponse)
async def confirm_combined_booking(
    group_code: str,
    service: CombinedBookingService = Depends(get_combined_booking_service),
    db: Session = Depends(get_db),
) -> CombinedBookingResponse:
    try:
        return service.confirm(group_code=group_code, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.post("/booking/combined/{group_code}/cancel", response_model=CombinedCancelResponse)
async def cancel_combined_booking(
    group_code: str,
    service: CombinedBookingService = Depends(get_combined_booking_service),
    db: Session = Depends(get_db),
) -> CombinedCancelResponse:
    """Hủy toàn bộ nhóm vé và tính tiền hoàn theo chính sách."""
    try:
        return service.cancel_group(group_code=group_code, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi he thong: {exc}") from exc


@router.post(
    "/booking/combined/{group_code}/legs/{sequence_no}/refund",
    response_model=CombinedCancelResponse,
)
async def refund_combined_booking_leg(
    group_code: str,
    sequence_no: int,
    service: CombinedBookingService = Depends(get_combined_booking_service),
    db: Session = Depends(get_db),
) -> CombinedCancelResponse:
    """Hoàn một chặng; các chặng còn lại của nhóm vẫn giữ nguyên hiệu lực."""
    try:
        return service.cancel_group(group_code=group_code, db=db, sequence_no=sequence_no)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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
