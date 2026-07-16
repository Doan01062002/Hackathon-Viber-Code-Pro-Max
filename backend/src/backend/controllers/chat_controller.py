from fastapi import APIRouter, Depends, HTTPException

from backend.models.chat import ChatRequest
from backend.services.chat_service import AgentError, ChatService
from backend.views.chat_view import ChatResponse, StatusResponse

router = APIRouter()


def get_chat_service() -> ChatService:
    """Dependency — test có thể override bằng service giả."""
    return ChatService()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Chat với AI agent."""
    try:
        message = await service.send_message(request.message)
    except AgentError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return ChatResponse.from_domain(message)


@router.get("/status", response_model=StatusResponse)
async def agent_status() -> StatusResponse:
    """Kiểm tra trạng thái agent."""
    return StatusResponse(status="ready", agent="LangGraph Agent v1.0")
