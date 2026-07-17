from pydantic import BaseModel, Field

from backend.models.chat import ChatMessage


class ChatResponse(BaseModel):
    """Response schema cho POST /chat."""

    response: str = Field(..., description="Phản hồi từ agent")
    analysis: str = Field(default="", description="Phân tích nội bộ")

    @classmethod
    def from_domain(cls, message: ChatMessage) -> "ChatResponse":
        """Domain model -> view. Controller không cần biết cách map."""
        return cls(response=message.response, analysis=message.analysis)


class StatusResponse(BaseModel):
    """Response schema cho GET /status."""

    status: str
    agent: str
