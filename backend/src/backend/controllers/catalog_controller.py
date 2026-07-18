from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import get_db

router = APIRouter(prefix="/catalog", tags=["catalog"])


class StationResponse(BaseModel):
    id: int
    code: str
    name: str
    display_order: int | None


class SeatTypeResponse(BaseModel):
    code: str
    name: str


class CatalogResponse(BaseModel):
    stations: list[StationResponse]
    seat_types: list[SeatTypeResponse]
    service_date_min: date | None
    service_date_max: date | None


@router.get("", response_model=CatalogResponse)
async def get_catalog(db: Session = Depends(get_db)) -> CatalogResponse:
    """Return the small reference dataset needed by booking forms."""
    try:
        stations = db.execute(
            text("""
                SELECT id, code, name, display_order
                FROM stations
                ORDER BY display_order NULLS LAST, name
            """)
        ).mappings().all()
        seat_types = db.execute(
            text("""
                SELECT code, name
                FROM seat_types
                WHERE is_active = TRUE
                ORDER BY name
            """)
        ).mappings().all()
        date_range = db.execute(
            text("""
                SELECT MIN(service_date) AS service_date_min,
                       MAX(service_date) AS service_date_max
                FROM trips
                WHERE status <> 'cancelled'
            """)
        ).mappings().one()

        return CatalogResponse(
            stations=[StationResponse(**row) for row in stations],
            seat_types=[SeatTypeResponse(**row) for row in seat_types],
            service_date_min=date_range["service_date_min"],
            service_date_max=date_range["service_date_max"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Khong the tai danh muc: {exc}") from exc
