"""Ranh giới backend -> ai cho Khối 1-2-3 (forecast/optimize/price).

Trước đây có hai client HTTP riêng (AIClient + AIPriceClient) gọi sang microservice
ai-service. ai_service giờ là thư viện Python nên gộp lại thành một client duy nhất gọi
thẳng AIEngine — không còn HTTP, không còn retry/timeout mạng.

Các method của AIEngine là đồng bộ và nặng CPU (LightGBM predict, giải LP bằng HiGHS).
Trước đây FastAPI tự đẩy endpoint `def` sang threadpool; giờ không còn, nên mọi lời gọi
ở đây đều bọc `asyncio.to_thread` để không chặn event loop của backend.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import date

from ai_service.engine import AIEngine, AIEngineError, get_engine
from ai_service.schemas import ForecastRequest, OptimizeRequest, PriceRequest, SegmentPriceInput

logger = logging.getLogger(__name__)

# Re-export để controller/service bắt lỗi mà không phải import từ ai_service.
__all__ = [
    "AIClient",
    "AIServiceError",
    "AIPriceResult",
    "SegmentBidPrice",
]


class AIServiceError(RuntimeError):
    """Engine AI không trả về được kết quả hợp lệ."""


@dataclass(frozen=True)
class SegmentBidPrice:
    segment_id: int
    bid_price: float


@dataclass(frozen=True)
class AIPriceResult:
    proposed_price: float
    explanation: dict[str, object]


class AIClient:
    def __init__(self, engine: AIEngine | None = None):
        # Mặc định dùng singleton dùng chung — nạp model.pkl một lần cho cả process.
        self._engine = engine or get_engine()

    async def get_forecast(self, service_date: str) -> dict:
        """Khối 1 — dự báo nhu cầu."""
        response = await asyncio.to_thread(self._engine.forecast, ForecastRequest(service_date=service_date))
        return response.model_dump()

    async def get_optimization(self, service_date: str, force_resolve: bool = False) -> dict:
        """Khối 2 — giải DLP bid price.

        Không cache ở lớp này nữa: AIEngine đã cache theo fingerprint của λ̂ nên tự
        invalidate khi model đổi dự báo, chính xác hơn cache theo service_date trước đây.
        """
        response = await asyncio.to_thread(
            self._engine.optimize, OptimizeRequest(service_date=service_date, force_resolve=force_resolve)
        )
        return response.model_dump()

    async def get_price(
        self, od_id: int, service_date: str, min_price: float | None = None, max_price: float | None = None
    ) -> dict:
        """Khối 3 — định giá, để engine tự giải Khối 2 cho ngày đó."""
        response = await asyncio.to_thread(
            self._engine.price,
            PriceRequest(od_id=od_id, service_date=service_date, min_price=min_price, max_price=max_price),
        )
        return response.model_dump()

    async def price(
        self,
        *,
        od_product_id: int,
        service_date: date,
        seat_type: str,
        base_price: float,
        segments: list[SegmentBidPrice],
    ) -> AIPriceResult:
        """Khối 3 — định giá từ snapshot bid price backend đọc sẵn trong DB (stateless)."""
        request = PriceRequest(
            od_id=od_product_id,
            service_date=service_date.isoformat(),
            seat_type=seat_type,
            base_price=base_price,
            segments=[
                SegmentPriceInput(segment_id=segment.segment_id, bid_price=segment.bid_price) for segment in segments
            ],
        )

        try:
            response = await asyncio.to_thread(self._engine.price, request)
        except AIEngineError as exc:
            logger.error(f"AI engine tra ve loi khi dinh gia od_product_id={od_product_id}: {exc}")
            raise AIServiceError("AI pricing engine khong tra ve ket qua hop le") from exc

        return AIPriceResult(
            proposed_price=float(response.proposed_price),
            explanation=response.explanation.model_dump(),
        )

    def clear_cache(self) -> None:
        self._engine.clear_cache()
