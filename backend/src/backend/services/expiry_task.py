"""Vòng lặp nền giải phóng chỗ giữ quá hạn.

Trước đây việc này chỉ chạy khi ai đó gọi tay POST /booking/release-expired, nghĩa
là ghế của một lần giữ chỗ bỏ dở sẽ bị treo vô thời hạn. Vòng lặp này gọi cùng một
service theo chu kỳ để tồn kho tự trả về.

Chạy tuần tự trong một task asyncio; mỗi vòng mở một session riêng và luôn đóng lại.
"""

import asyncio
import logging
from collections.abc import Callable

from backend.config import get_settings
from backend.database import get_session_factory
from backend.services.booking_service import BookingService

logger = logging.getLogger(__name__)


def release_expired_once(service: BookingService | None = None) -> int:
    """Chạy một lượt giải phóng. Trả về số vé đã nhả.

    Tách khỏi vòng lặp để test được mà không cần asyncio.
    """
    booking_service = service or BookingService()
    session = get_session_factory()()
    try:
        released = booking_service.release_expired_bookings(db=session)
        session.commit()
        return released
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def _loop(interval_seconds: int, runner: Callable[[], int]) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            # Chạy trong thread pool vì service dùng driver DB đồng bộ; gọi thẳng
            # sẽ chặn event loop và làm nghẽn mọi request đang phục vụ.
            released = await asyncio.to_thread(runner)
            if released:
                logger.info("Đã giải phóng %s vé giữ chỗ quá hạn", released)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Một lần lỗi DB không được phép giết vòng lặp — lần sau thử lại.
            logger.exception("Giải phóng vé quá hạn thất bại, sẽ thử lại ở chu kỳ sau")


def start_expiry_task(runner: Callable[[], int] = release_expired_once) -> asyncio.Task | None:
    """Khởi động vòng lặp nếu config bật. Trả về None khi đang tắt."""
    settings = get_settings()
    if not settings.release_expired_enabled:
        logger.info("Bỏ qua vòng lặp giải phóng vé quá hạn (release_expired_enabled=False)")
        return None

    interval = settings.release_expired_interval_seconds
    logger.info("Bật vòng lặp giải phóng vé quá hạn, chu kỳ %ss", interval)
    return asyncio.create_task(_loop(interval, runner))


async def stop_expiry_task(task: asyncio.Task | None) -> None:
    """Hủy vòng lặp và đợi nó dừng hẳn."""
    if task is None:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
