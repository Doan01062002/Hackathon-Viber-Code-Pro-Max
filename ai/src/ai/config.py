from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """Config riêng của module AI: LLM và vector store.

    Không chứa config app/HTTP — phần đó thuộc về backend.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    openai_api_key: str = ""
    model_name: str = "gpt-4o-mini"
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    # Observability
    ai_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    ai_log_format: Literal["json", "text"] = "json"

    # Vector Store
    chroma_persist_dir: str = "./data/chroma"


@lru_cache
def get_ai_settings() -> AISettings:
    return AISettings()
