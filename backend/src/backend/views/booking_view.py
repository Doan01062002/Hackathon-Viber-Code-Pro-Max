from datetime import date, datetime

from pydantic import BaseModel, Field


class BookingCreateRequest(BaseModel):
    od_product_id: int = Field(..., gt=0, description="ID san pham OD")
    seat_id: int | None = Field(None, gt=0, description="ID ghe user chon, neu co")
    quote_id: int | None = Field(None, gt=0, description="ID bao gia, neu co")
    channel: str | None = Field("web", max_length=30, description="Kenh ban ve")


class BookingResponse(BaseModel):
    booking_id: int
    booking_code: str
    od_product_id: int
    seat_id: int | None = None
    status: str
    booked_price: float
    booked_at: str
    expires_at: str | None = None


class BookingConfirmResponse(BaseModel):
    booking_id: int
    booking_code: str
    status: str
    seat_id: int
    coach_no: str
    seat_no: str


class BookingSearchItem(BaseModel):
    od_product_id: int
    trip_id: int
    train_code: str
    origin_code: str
    origin_name: str
    destination_code: str
    destination_name: str
    service_date: date
    departure_at: datetime
    arrival_at: datetime
    seat_type: str
    seat_type_name: str
    base_price: float
    availability: int


class BookingDestinationOption(BaseModel):
    code: str
    name: str


class BookingOptionsResponse(BaseModel):
    destinations: list[BookingDestinationOption]
    departure_dates: list[date]
    return_dates: list[date]


class BookingSeatItem(BaseModel):
    seat_id: int
    seat_no: str
    status: str


class BookingCoachItem(BaseModel):
    coach_no: str
    seat_type: str
    total_seats: int
    available_seats: int
    seats: list[BookingSeatItem]


class BookingSegmentItem(BaseModel):
    segment_id: int
    sequence_no: int
    origin_code: str
    origin_name: str
    destination_code: str
    destination_name: str
    departure_at: datetime
    arrival_at: datetime
    distance_km: float
    capacity: int
    remaining: int
    load_pct: float


class BookingSeatPlanResponse(BaseModel):
    od_product_id: int
    trip_id: int
    train_code: str
    origin_code: str
    origin_name: str
    destination_code: str
    destination_name: str
    service_date: date
    seat_type: str
    coaches: list[BookingCoachItem]
    segments: list[BookingSegmentItem]


class BookingDetailResponse(BaseModel):
    booking_id: int
    booking_code: str
    status: str
    booked_price: float
    booked_at: datetime
    expires_at: datetime | None
    trip_id: int
    train_code: str
    service_date: date
    departure_at: datetime
    arrival_at: datetime
    origin_code: str
    origin_name: str
    destination_code: str
    destination_name: str
    seat_type: str
    coach_no: str | None
    seat_no: str | None
