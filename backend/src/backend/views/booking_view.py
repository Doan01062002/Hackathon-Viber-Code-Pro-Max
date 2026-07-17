from pydantic import BaseModel, Field
from typing import Optional

class BookingCreateRequest(BaseModel):
    od_product_id: int = Field(..., description="ID của sản phẩm OD")
    quote_id: Optional[int] = Field(None, description="ID của báo giá đã tạo (nếu có)")
    channel: Optional[str] = Field("web", description="Kênh bán vé")

class BookingResponse(BaseModel):
    booking_id: int = Field(..., description="ID của booking")
    booking_code: str = Field(..., description="Mã đặt vé duy nhất")
    od_product_id: int = Field(..., description="ID của sản phẩm OD")
    seat_id: Optional[int] = Field(None, description="ID của ghế vật lý được gán (nếu có)")
    status: str = Field(..., description="Trạng thái đặt vé (held, confirmed, cancelled, refunded)")
    booked_price: float = Field(..., description="Giá vé đặt")
    booked_at: str = Field(..., description="Thời điểm đặt vé (ISO format)")
    expires_at: Optional[str] = Field(None, description="Thời điểm hết hạn giữ chỗ (ISO format)")

class BookingConfirmResponse(BaseModel):
    booking_id: int = Field(..., description="ID của booking")
    booking_code: str = Field(..., description="Mã đặt vé")
    status: str = Field(..., description="Trạng thái đặt vé")
    seat_id: int = Field(..., description="ID của ghế vật lý được gán")
    coach_no: str = Field(..., description="Số toa tàu")
    seat_no: str = Field(..., description="Số ghế")
