"""AI module — LangGraph agent.

Interface công khai của module. Backend CHỈ được import từ đây:

    from ai import run_agent, AgentResult

Không import trực tiếp ai.nodes, ai.tools, ai.graph — đó là nội bộ,
có thể đổi bất cứ lúc nào mà không báo trước.
"""

from dataclasses import dataclass

from ai.graph import agent, build_graph
from ai.state import AgentState

__all__ = ["AgentResult", "run_agent", "build_graph", "AgentState"]


@dataclass(frozen=True)
class AgentResult:
    """Kết quả agent trả về. Kiểu dữ liệu thuần Python — không dính HTTP."""

    response: str
    analysis: str = ""
    error: str | None = None


async def run_agent(query: str) -> AgentResult:
    """Chạy agent với một query của user.

    Đây là điểm vào chính của module AI.

    Args:
        query: Câu hỏi/tin nhắn từ user

    Returns:
        AgentResult chứa response và analysis
    """
    state = await agent.ainvoke({"query": query})
    return AgentResult(
        response=state.get("response", ""),
        analysis=state.get("analysis", ""),
        error=state.get("error"),
    )
