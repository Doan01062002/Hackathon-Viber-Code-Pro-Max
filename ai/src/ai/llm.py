from langchain_openai import ChatOpenAI

from ai.config import get_ai_settings


def get_llm() -> ChatOpenAI:
    settings = get_ai_settings()
    return ChatOpenAI(
        model=settings.model_name,
        api_key=settings.openai_api_key,
        temperature=settings.llm_temperature,
    )
