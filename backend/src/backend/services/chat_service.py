from ai import run_agent
from backend.models.chat import ChatMessage


class AgentError(Exception):
    """Agent chạy lỗi. Controller bắt cái này và đổi thành HTTP 502."""


class ChatService:
    """Nghiệp vụ chat: gọi AI agent, trả về domain model.

    Đây là ranh giới giữa backend và ai — nơi duy nhất `import ai` xuất hiện.
    Controller không biết agent tồn tại; nó chỉ biết ChatService.
    """

    async def send_message(self, message: str) -> ChatMessage:
        try:
            result = await run_agent(message)
        except Exception as e:
            raise AgentError(f"Agent thất bại: {e}") from e

        if result.error:
            raise AgentError(result.error)

        return ChatMessage(response=result.response, analysis=result.analysis)
