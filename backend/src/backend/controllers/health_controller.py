from typing import Annotated

from fastapi import APIRouter, Depends

from backend.config import get_settings
from backend.database import get_database_status
from backend.views.health_view import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(
    database: Annotated[str, Depends(get_database_status)],
) -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", env=settings.app_env, database=database)
