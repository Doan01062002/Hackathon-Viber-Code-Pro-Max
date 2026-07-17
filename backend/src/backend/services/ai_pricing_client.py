from dataclasses import dataclass
from datetime import date

import httpx

from backend.config import get_settings


class AIServiceError(RuntimeError):
    """Raised when the pricing service cannot return a valid quote."""


@dataclass(frozen=True)
class SegmentBidPrice:
    segment_id: int
    bid_price: float


@dataclass(frozen=True)
class AIPriceResult:
    proposed_price: float
    explanation: dict[str, object]


class AIPriceClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: float | None = None) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.ai_service_url).rstrip("/")
        self._timeout_seconds = timeout_seconds or settings.ai_service_timeout_seconds

    async def price(
        self,
        *,
        od_product_id: int,
        service_date: date,
        seat_type: str,
        base_price: float,
        segments: list[SegmentBidPrice],
    ) -> AIPriceResult:
        payload = {
            "od_id": od_product_id,
            "service_date": service_date.isoformat(),
            "seat_type": seat_type,
            "base_price": base_price,
            "segments": [
                {"segment_id": segment.segment_id, "bid_price": segment.bid_price}
                for segment in segments
            ],
        }

        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout_seconds) as client:
                response = await client.post("/internal/price", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AIServiceError("AI pricing service khong kha dung") from exc

        try:
            body = response.json()
            return AIPriceResult(
                proposed_price=float(body["proposed_price"]),
                explanation=dict(body.get("explanation", {})),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AIServiceError("AI pricing service tra ve du lieu khong hop le") from exc
