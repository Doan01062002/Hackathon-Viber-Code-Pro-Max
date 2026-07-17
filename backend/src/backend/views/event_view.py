from typing import Any

from pydantic import BaseModel, Field


class EventRequest(BaseModel):
    event_type: str = Field(..., description="Loại sự kiện, ví dụ: booking_created, booking_cancelled")
    trip_id: int = Field(..., description="ID của chuyến tàu liên quan")
    payload: dict[str, Any] = Field(default_factory=dict, description="Metadata đi kèm sự kiện")
