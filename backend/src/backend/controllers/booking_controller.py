from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.booking_service import BookingService
from backend.views.booking_view import BookingConfirmResponse, BookingCreateRequest, BookingResponse

router = APIRouter()


def get_booking_service() -> BookingService:
    return BookingService()


@router.post("/booking", response_model=BookingResponse, status_code=201)
async def create_booking_hold_standard(
    request: BookingCreateRequest,
    service: BookingService = Depends(get_booking_service),
    db: Session = Depends(get_db),
) -> BookingResponse:
    """Tạo yêu cầu giữ chỗ (booking hold) cho sản phẩm OD."""
    try:
        return service.create_booking_hold(request=request, db=db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


@router.post("/booking/{booking_id}/confirm", response_model=BookingConfirmResponse)
async def confirm_booking(
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
    db: Session = Depends(get_db),
) -> BookingConfirmResponse:
    """Xác nhận đặt vé thành công và tự động gán ghế vật lý phù hợp."""
    try:
        return service.confirm_booking(booking_id=booking_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


@router.post("/booking/release-expired")
async def release_expired_bookings(
    service: BookingService = Depends(get_booking_service),
    db: Session = Depends(get_db),
):
    """Quét và giải phóng các giữ chỗ (booking hold) đã hết hạn."""
    try:
        count = service.release_expired_bookings(db=db)
        return {"status": "success", "released_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
