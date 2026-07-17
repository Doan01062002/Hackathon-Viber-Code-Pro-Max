import logging
import threading
import time
from typing import Any

import redis

from backend.config import get_settings

logger = logging.getLogger("srrm.redis")


class MockRedis:
    _instance = None

    def __init__(self):
        self.streams: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        self.lock = threading.Lock()
        logger.info("Initializing in-memory MockRedis instance.")

    @classmethod
    def get_mock_instance(cls) -> "MockRedis":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def xadd(
        self, name: str, fields: dict[str, Any], id: str = "*", maxlen: Any = None, approximate: bool = True
    ) -> str:
        """Thêm một tin nhắn vào stream giả lập."""
        with self.lock:
            if name not in self.streams:
                self.streams[name] = []

            # Tạo unique message ID: timestamp_ms-index
            timestamp_ms = int(time.time() * 1000)
            msg_id = f"{timestamp_ms}-{len(self.streams[name])}"
            self.streams[name].append((msg_id, fields))
            logger.debug(f"MockRedis: Added message {msg_id} to stream '{name}': {fields}")
            return msg_id

    def xread(
        self, streams: dict[str, str], count: Any = None, block: Any = None
    ) -> list[tuple[str, list[tuple[str, dict[str, Any]]]]]:
        """Đọc tin nhắn từ stream giả lập."""
        result = []
        with self.lock:
            for s_name, last_id in streams.items():
                msg_list = self.streams.get(s_name, [])
                unread = []

                if last_id == "$":
                    # Hành vi của Redis $: trả về tin nhắn cuối cùng nếu có
                    if msg_list:
                        unread.append(msg_list[-1])
                else:
                    # Trả về các tin nhắn có ID lớn hơn last_id
                    for msg_id, fields in msg_list:
                        if last_id == "0" or last_id == "0-0" or msg_id > last_id:
                            unread.append((msg_id, fields))

                if unread:
                    result.append((s_name, unread))
        return result

    def ping(self) -> bool:
        return True


def get_redis_client():
    settings = get_settings()
    try:
        # Thử kết nối đến Redis thực tế
        client = redis.Redis.from_url(settings.redis_url, socket_timeout=1.0, decode_responses=True)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Real Redis connection failed: {str(e)}. Falling back to in-memory MockRedis.")
        return MockRedis.get_mock_instance()
