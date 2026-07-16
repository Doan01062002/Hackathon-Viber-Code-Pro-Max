from dataclasses import dataclass

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema — dữ liệu client gửi lên."""

    message: str = Field(..., min_length=1, max_length=5000, description="Tin nhắn từ user")


@dataclass(frozen=True)
class ChatMessage:
    """Domain model — kết quả một lượt chat, độc lập với HTTP.

    Service trả về kiểu này; view lo việc biến nó thành response.
    """

    response: str
    analysis: str = ""
