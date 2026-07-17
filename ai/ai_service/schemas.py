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
    force_resolve: bool = False  # bỏ qua cache, ép giải lại từ đầu dù input không đổi


class BidPrice(BaseModel):
    segment_id: int  # chỉ số chặng cục bộ 0-based (chặng thứ segment_id: ga segment_id -> segment_id+1)
    seat_type: str
    bid_price: float


class Quota(BaseModel):
    origin_idx: int  # vị trí ga đi 0-based trong mạng 20 ga cố định (ai_service/config.py)
    dest_idx: int  # vị trí ga đến 0-based
    seat_type: str
    quota: float


class OptimizeResponse(BaseModel):
    service_date: str
    run_version: str  # mã phiên — backend dùng khi swap is_active trong bid_prices/quotas
    warm_started: bool  # True nếu trả từ cache (input không đổi từ lần giải trước)
    solve_ms: float
    revenue_lp: float
    bid_prices: list[BidPrice]
    quotas: list[Quota]
    n_rejected: int
    n_od: int


class PriceRequest(BaseModel):
    od_id: int
    service_date: str
    min_price: float | None = None
    max_price: float | None = None


class PriceExplanation(BaseModel):
    bottleneck_segment: int | None
    segment_pi: dict[int, float]
    elasticity: float
    base_price: float


class PriceResponse(BaseModel):
    od_id: int
    seat_type: str
    opportunity_cost: float
    proposed_price: float
    final_price: float
    decision: str
    explanation: PriceExplanation
