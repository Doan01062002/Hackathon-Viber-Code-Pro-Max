from datetime import date, datetime

from pydantic import BaseModel, Field


class CombinedJourneyLegOption(BaseModel):
    sequence_no: int
    gap_combination_id: int
    od_product_id: int
    origin_code: str
    origin_name: str
    destination_code: str
    destination_name: str
    departure_at: datetime
    arrival_at: datetime
    seat_id: int
    coach_no: str
    seat_no: str
    seat_type: str
    seat_type_name: str
    estimated_price: float
    keep_previous_seat: bool


class CombinedJourneyOption(BaseModel):
    option_key: str
    trip_id: int
    train_code: str
    service_date: date
    origin_code: str
    origin_name: str
    destination_code: str
    destination_name: str
    transfer_count: int
    seat_change_count: int
    estimated_total_price: float
    legs: list[CombinedJourneyLegOption]


class CombinedJourneyOptionsResponse(BaseModel):
    origin_code: str
    destination_code: str
    service_date: date
    options: list[CombinedJourneyOption]


class CombinedBookingCreateRequest(BaseModel):
    gap_combination_ids: list[int] = Field(..., min_length=2, max_length=4)
    channel: str | None = Field("web", max_length=30)


class CombinedBookingLegResponse(BaseModel):
    sequence_no: int
    gap_combination_id: int
    booking_id: int
    booking_code: str
    od_product_id: int
    status: str
    origin_code: str
    origin_name: str
    destination_code: str
    destination_name: str
    departure_at: datetime
    arrival_at: datetime
    seat_id: int
    coach_no: str
    seat_no: str
    seat_type: str
    seat_type_name: str
    booked_price: float
    keep_previous_seat: bool


class CombinedBookingResponse(BaseModel):
    booking_group_id: int
    group_code: str
    status: str
    channel: str | None
    trip_id: int
    train_code: str
    service_date: date
    origin_code: str
    origin_name: str
    destination_code: str
    destination_name: str
    transfer_count: int
    total_price: float
    booked_at: datetime
    expires_at: datetime | None
    legs: list[CombinedBookingLegResponse]
