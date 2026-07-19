from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Config riêng của backend: app, HTTP, database.

    Config LLM/vector store thuộc về module ai (xem ai.config.AISettings).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "Viber Coding Pro Max"
    app_env: Literal["development", "production", "test"] = "development"
    app_port: int = Field(default=8000, ge=1, le=65535)
    app_host: str = "0.0.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "sqlite:///./data/app.db"

    # Khối 1-2-3 (forecast/optimize/price) chạy in-process qua ai_service.engine.AIEngine
    # (xem backend/services/ai_client.py) — không còn URL/timeout vì không còn gọi mạng.

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Tự động giải phóng chỗ giữ quá hạn.
    # Tắt trong test và trong môi trường serverless (mỗi request một tiến trình,
    # vòng lặp nền không sống đủ lâu để có tác dụng) — ở đó dùng cron gọi
    # POST /api/v1/booking/release-expired thay thế.
    release_expired_enabled: bool = True
    release_expired_interval_seconds: int = Field(default=60, ge=10, le=3600)


@lru_cache
def get_settings() -> Settings:
    return Settings()
