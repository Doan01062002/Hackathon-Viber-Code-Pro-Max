"""V trong MVC — response schema, tức thứ client thực sự nhìn thấy.

Với REST API thì response body chính là "view": controller khai báo
các schema ở đây trong response_model.
"""

from backend.views.chat_view import ChatResponse, StatusResponse
from backend.views.health_view import HealthResponse

__all__ = ["ChatResponse", "StatusResponse", "HealthResponse"]
