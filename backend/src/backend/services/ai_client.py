import httpx
import asyncio
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self, base_url: Optional[str] = None):
        # Đọc base_url từ biến môi trường hoặc mặc định là http://localhost:8001
        self.base_url = base_url or os.getenv("AI_SERVICE_URL", "http://localhost:8001")
        # In-memory cache cho bid prices/optimization theo service_date
        self._opt_cache: Dict[str, Dict[str, Any]] = {}

    async def _post_with_retry(self, path: str, payload: dict, retries: int = 3, backoff: float = 0.5) -> dict:
        url = f"{self.base_url.rstrip('/')}{path}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            for attempt in range(retries + 1):
                try:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    return response.json()
                except (httpx.HTTPError, httpx.RequestError) as e:
                    if attempt == retries:
                        logger.error(f"Failed to call AI Service at {url} after {retries} retries: {str(e)}")
                        raise e
                    sleep_time = backoff * (2 ** attempt)
                    logger.warning(f"Error calling {url}: {str(e)}. Retrying in {sleep_time}s...")
                    await asyncio.sleep(sleep_time)
            raise httpx.HTTPError("Max retries exceeded")

    async def get_forecast(self, service_date: str) -> dict:
        """Gọi API dự báo nhu cầu từ ai-service."""
        return await self._post_with_retry("/internal/forecast", {"service_date": service_date})

    async def get_optimization(self, service_date: str) -> dict:
        """Gọi API tối ưu hóa chặng (DLP) từ ai-service. Có cơ chế cache bid price."""
        if service_date in self._opt_cache:
            logger.info(f"[CACHE HIT] Lấy kết quả tối ưu của ngày {service_date} từ cache.")
            return self._opt_cache[service_date]
            
        res = await self._post_with_retry("/internal/optimize", {"service_date": service_date})
        self._opt_cache[service_date] = res
        return res

    async def get_price(self, od_id: int, service_date: str, min_price: Optional[float] = None, max_price: Optional[float] = None) -> dict:
        """Gọi API định giá tối ưu từ ai-service."""
        payload = {
            "od_id": od_id,
            "service_date": service_date,
            "min_price": min_price,
            "max_price": max_price
        }
        return await self._post_with_retry("/internal/price", payload)

    def clear_cache(self):
        """Xóa sạch cache tối ưu."""
        self._opt_cache.clear()
