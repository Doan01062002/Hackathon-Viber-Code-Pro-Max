"""Hợp đồng JSON cho ai-service (đặt trong contracts/ khi triển khai thật)."""

from __future__ import annotations

from pydantic import BaseModel


class ForecastRequest(BaseModel):
    service_date: str  # ISO 8601, ví dụ "2024-02-11"


class ForecastItem(BaseModel):
    od_id: int
    origin: str
    dest: str
    seat_type: str
    lambda_hat: float
    p10: float
    p50: float
    p90: float


class ForecastResponse(BaseModel):
    service_date: str
    model_version: str
    items: list[ForecastItem]


class OptimizeRequest(BaseModel):
    service_date: str


class BidPrice(BaseModel):
    segment_id: int
    seat_type: str
    bid_price: float


class OptimizeResponse(BaseModel):
    service_date: str
    solve_ms: float
    revenue_lp: float
    bid_prices: list[BidPrice]
    n_rejected: int
    n_od: int


class PriceRequest(BaseModel):
    od_id: int
    service_date: str
    min_price: float | None = None
    max_price: float | None = None


class PriceResponse(BaseModel):
    od_id: int
    seat_type: str
    opportunity_cost: float
    proposed_price: float
    final_price: float
    decision: str
    explanation: dict
