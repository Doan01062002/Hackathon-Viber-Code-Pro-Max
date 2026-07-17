from datetime import date

from pydantic import BaseModel, Field, field_validator


class PricingQuoteRequest(BaseModel):
    origin: str = Field(..., min_length=2, max_length=120, description="Ma hoac ten ga di")
    destination: str = Field(..., min_length=2, max_length=120, description="Ma hoac ten ga den")
    service_date: date = Field(..., description="Ngay tau chay")
    seat_type: str = Field(..., min_length=2, max_length=30, description="Ma loai cho")
    trip_id: int | None = Field(None, gt=0, description="Chuyen tau cu the, neu da biet")

    @field_validator("origin", "destination", "seat_type")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class PricingExplanation(BaseModel):
    base_opportunity_cost: float
    markup_factor: float
    applied_policies: list[str]
    bottleneck_segment_id: int | None = None
    bottleneck_segment: str | None = None
    segment_bid_prices: dict[str, float] = Field(default_factory=dict)


class PricingQuoteResponse(BaseModel):
    quote_id: int
    od_product_id: int
    policy_id: int | None = None
    opportunity_cost: float
    proposed_price: float
    final_price: float
    decision: str
    explanation: PricingExplanation
    expires_at: str
    origin: str | None = None
    destination: str | None = None
    service_date: date | None = None
    seat_type: str | None = None
    availability: int | None = Field(None, ge=0)
