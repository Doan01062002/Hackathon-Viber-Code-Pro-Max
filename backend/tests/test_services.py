import pytest

from backend.services.chat_service import AgentError, ChatService


@pytest.mark.asyncio
async def test_send_message_returns_domain_model():
    """Service trả về ChatMessage, không phải dict state của agent."""
    message = await ChatService().send_message("Hello")
    assert message.response
    assert isinstance(message.analysis, str)


@pytest.mark.asyncio
async def test_send_message_wraps_agent_failure(monkeypatch):
    async def boom(query: str):
        raise RuntimeError("LLM down")

    monkeypatch.setattr("backend.services.chat_service.run_agent", boom)

    with pytest.raises(AgentError):
        await ChatService().send_message("Hello")
