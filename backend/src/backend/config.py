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

    # ai-service — Khối 1-2-3 (forecast/optimize/price), xem ai/ai_service/app.py
    ai_service_url: str = "http://localhost:8001"
    ai_service_timeout_seconds: float = Field(default=10.0, gt=0, le=60)

    # Redis
    redis_url: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
