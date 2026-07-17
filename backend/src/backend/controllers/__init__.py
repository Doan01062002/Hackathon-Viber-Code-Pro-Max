"""C trong MVC — router gom lại một chỗ để main.py chỉ gắn một router."""

from fastapi import APIRouter

from backend.controllers.analytics_controller import router as analytics_router
from backend.controllers.booking_controller import router as booking_router
from backend.controllers.event_controller import router as event_router
from backend.controllers.optimize_controller import router as optimize_router
from backend.controllers.pricing_controller import router as pricing_router
from backend.controllers.simulation_controller import router as simulation_router
from backend.controllers.policy_controller import router as policy_router
from backend.controllers.audit_controller import router as audit_router

api_router = APIRouter()
api_router.include_router(analytics_router)
api_router.include_router(pricing_router)
api_router.include_router(booking_router)
api_router.include_router(optimize_router)
api_router.include_router(event_router)
api_router.include_router(simulation_router)
api_router.include_router(policy_router)
api_router.include_router(audit_router)

__all__ = ["api_router"]
