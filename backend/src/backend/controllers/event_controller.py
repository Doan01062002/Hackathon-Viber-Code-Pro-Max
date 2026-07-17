import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.redis_client import get_redis_client
from backend.views.event_view import EventRequest

router = APIRouter()


class EventQueuedResponse(BaseModel):
    status: str = Field(..., description="Trạng thái hàng đợi (queued)")
    event_id: str = Field(..., description="ID của sự kiện được cấp bởi Redis Stream")
    message: str = Field(..., description="Thông điệp kết quả")


@router.post("/events", response_model=EventQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
async def publish_event(request: EventRequest, redis_conn=Depends(get_redis_client)) -> EventQueuedResponse:
    """Nhận sự kiện và đẩy vào Redis Stream 'srrm:event_stream' để worker xử lý bất đồng bộ."""
    try:
        # Chuyển đổi payload thành chuỗi JSON
        payload_str = json.dumps(request.payload)

        # Đẩy vào Redis Stream
        event_id = redis_conn.xadd(
            "srrm:event_stream",
            {"trip_id": str(request.trip_id), "event_type": request.event_type, "payload": payload_str},
        )

        return EventQueuedResponse(
            status="queued", event_id=event_id, message="Sự kiện đã được nhận và đưa vào hàng đợi xử lý."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể đẩy sự kiện vào Redis Stream: {str(e)}",
        )
