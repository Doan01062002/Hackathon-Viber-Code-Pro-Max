import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.controllers.chat_controller import get_chat_service
from backend.database import get_database_status
from backend.main import create_app
from backend.models.chat import ChatMessage


class FakeChatService:
    """Service giả — test controller mà không gọi AI agent thật."""

    async def send_message(self, message: str) -> ChatMessage:
        return ChatMessage(response=f"echo: {message}", analysis="fake")


@pytest.fixture
def app():
    app = create_app()
    app.dependency_overrides[get_chat_service] = FakeChatService
    app.dependency_overrides[get_database_status] = lambda: "ok"
    return app


@pytest_asyncio.fixture
async def client(app):
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
