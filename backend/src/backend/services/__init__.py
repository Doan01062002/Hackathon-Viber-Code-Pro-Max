"""Business logic — tầng duy nhất được phép import module ai."""

from backend.services.chat_service import ChatService

__all__ = ["ChatService"]
