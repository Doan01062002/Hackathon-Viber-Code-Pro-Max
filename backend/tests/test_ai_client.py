from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.services.ai_client import AIClient


@pytest.mark.asyncio
async def test_ai_client_success():
    """Kiểm tra gọi API thành công qua AIClient."""
    client = AIClient(base_url="http://mock-ai-service:8001")

    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success", "items": []}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        res = await client.get_forecast("2026-07-20")
        assert res["status"] == "success"
        mock_post.assert_called_once_with(
            "http://mock-ai-service:8001/internal/forecast", json={"service_date": "2026-07-20"}
        )


@pytest.mark.asyncio
async def test_ai_client_caching():
    """Kiểm tra cơ chế cache kết quả tối ưu hóa (DLP) theo service_date."""
    client = AIClient(base_url="http://mock-ai-service:8001")

    mock_response = MagicMock()
    mock_response.json.return_value = {"solve_ms": 12.5, "bid_prices": []}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        # Gọi lần 1 -> Phải gọi HTTP POST
        res1 = await client.get_optimization("2026-07-20")
        assert res1["solve_ms"] == 12.5

        # Gọi lần 2 -> Lấy từ cache, không gọi HTTP POST nữa
        res2 = await client.get_optimization("2026-07-20")
        assert res2["solve_ms"] == 12.5

        assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_ai_client_retries_and_fails():
    """Kiểm tra cơ chế retry và ném ra lỗi sau khi thử lại hết số lần tối đa."""
    client = AIClient(base_url="http://mock-ai-service:8001")

    # Giả lập httpx ném ra lỗi kết nối
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        with pytest.raises(httpx.ConnectError):
            # Cấu hình backoff thấp (0.01s) để chạy test cực nhanh
            await client._post_with_retry("/internal/forecast", {"service_date": "2026-07-20"}, retries=3, backoff=0.01)

        # Thử lần đầu + 3 lần retry = 4 lượt gọi tất cả
        assert mock_post.call_count == 4


@pytest.mark.asyncio
async def test_ai_client_retries_then_succeeds():
    """Kiểm tra cơ chế retry khôi phục thành công khi lỗi tạm thời xảy ra ở lượt đầu."""
    client = AIClient(base_url="http://mock-ai-service:8001")

    mock_success_response = MagicMock()
    mock_success_response.json.return_value = {"status": "ok"}
    mock_success_response.raise_for_status = MagicMock()

    # Lượt 1: ném lỗi, Lượt 2: thành công
    side_effects = [httpx.ConnectError("Temporary error"), mock_success_response]

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = side_effects
        res = await client._post_with_retry(
            "/internal/forecast", {"service_date": "2026-07-20"}, retries=2, backoff=0.01
        )
        assert res["status"] == "ok"
        assert mock_post.call_count == 2
