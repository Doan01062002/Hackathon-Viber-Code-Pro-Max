from dataclasses import dataclass


@dataclass(frozen=True)
class AgentResult:
    """Kết quả agent trả về."""

    response: str
    analysis: str = ""
    error: str | None = None


async def run_agent(query: str) -> AgentResult:
    """Chạy agent với một query của user."""
    return AgentResult(response=f"echo: {query}", analysis="Mock analysis", error=None)
