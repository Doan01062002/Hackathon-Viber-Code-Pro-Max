"""Ranh giới backend -> ai cho Khối 1-2-3 (forecast/optimize/price).

Trước đây có hai client HTTP riêng (AIClient + AIPriceClient) gọi sang microservice
ai-service. ai_service giờ là thư viện Python nên gộp lại thành một client duy nhất gọi
thẳng AIEngine — không còn HTTP, không còn retry/timeout mạng.

Các method của AIEngine là đồng bộ và nặng CPU (LightGBM predict, giải LP bằng HiGHS).
Trước đây FastAPI tự đẩy endpoint `def` sang threadpool; giờ không còn, nên mọi lời gọi
ở đây đều bọc `asyncio.to_thread` để không chặn event loop của backend.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_service.engine import AIEngine

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


class AIInvalidRequestError(AIServiceError):
    """Dữ liệu đầu vào của AI không hợp lệ."""


class AIModelNotReadyError(AIServiceError):
    """Model AI chưa sẵn sàng."""


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
        # Không nạp pandas/LightGBM khi FastAPI khởi động. Dashboard chỉ dùng DB nên
        # không phải trả chi phí cold start của AI cho đến request AI đầu tiên.
        self._engine = engine

    def _get_engine(self) -> AIEngine:
        if self._engine is None:
            from ai_service.engine import get_engine

            self._engine = get_engine()
        return self._engine

    async def get_forecast(self, service_date: str) -> dict:
        """Khối 1 — dự báo nhu cầu."""
        from ai_service.engine import InvalidRequestError, ModelNotReadyError
        from ai_service.schemas import ForecastRequest

        try:
            response = await asyncio.to_thread(
                self._get_engine().forecast,
                ForecastRequest(service_date=service_date),
            )
        except InvalidRequestError as exc:
            raise AIInvalidRequestError(str(exc)) from exc
        except ModelNotReadyError as exc:
            raise AIModelNotReadyError(str(exc)) from exc
        return response.model_dump()

    async def get_optimization(self, service_date: str, force_resolve: bool = False) -> dict:
        """Khối 2 — giải DLP bid price.

        Không cache ở lớp này nữa: AIEngine đã cache theo fingerprint của λ̂ nên tự
        invalidate khi model đổi dự báo, chính xác hơn cache theo service_date trước đây.
        """
        from ai_service.engine import InvalidRequestError, ModelNotReadyError
        from ai_service.schemas import OptimizeRequest

        try:
            response = await asyncio.to_thread(
                self._get_engine().optimize,
                OptimizeRequest(service_date=service_date, force_resolve=force_resolve),
            )
        except InvalidRequestError as exc:
            raise AIInvalidRequestError(str(exc)) from exc
        except ModelNotReadyError as exc:
            raise AIModelNotReadyError(str(exc)) from exc
        return response.model_dump()

    async def get_price(
        self, od_id: int, service_date: str, min_price: float | None = None, max_price: float | None = None
    ) -> dict:
        """Khối 3 — định giá, để engine tự giải Khối 2 cho ngày đó."""
        from ai_service.schemas import PriceRequest

        response = await asyncio.to_thread(
            self._get_engine().price,
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
        from ai_service.engine import AIEngineError
        from ai_service.schemas import PriceRequest, SegmentPriceInput

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
            response = await asyncio.to_thread(self._get_engine().price, request)
        except AIEngineError as exc:
            logger.error(f"AI engine tra ve loi khi dinh gia od_product_id={od_product_id}: {exc}")
            raise AIServiceError("AI pricing engine khong tra ve ket qua hop le") from exc

        return AIPriceResult(
            proposed_price=float(response.proposed_price),
            explanation=response.explanation.model_dump(),
        )

    def clear_cache(self) -> None:
        self._get_engine().clear_cache()
