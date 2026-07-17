"""C trong MVC — router gom lại một chỗ để main.py chỉ gắn một router."""

from fastapi import APIRouter

from backend.controllers.chat_controller import router as chat_router
from backend.controllers.analytics_controller import router as analytics_router
from backend.controllers.pricing_controller import router as pricing_router
from backend.controllers.booking_controller import router as booking_router
from backend.controllers.optimize_controller import router as optimize_router

api_router = APIRouter()
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(analytics_router)
api_router.include_router(pricing_router)
api_router.include_router(booking_router)
api_router.include_router(optimize_router)

__all__ = ["api_router"]
