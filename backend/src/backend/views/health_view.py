from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response schema cho GET /health."""

    status: str
    env: str
    database: str
