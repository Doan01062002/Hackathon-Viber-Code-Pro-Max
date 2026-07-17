"""AI module — LangGraph agent.

Interface công khai của module. Backend CHỈ được import từ đây:

    from ai import run_agent, AgentResult

Không import trực tiếp ai.nodes, ai.tools, ai.graph — đó là nội bộ,
có thể đổi bất cứ lúc nào mà không báo trước.
"""

from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from ai.graph import agent, build_graph
from ai.logging import get_ai_logger
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
    logger = get_ai_logger()
    run_id = uuid4().hex
    started_at = perf_counter()
    logger.info(
        "Agent run started",
        extra={"event": "agent.run.started", "run_id": run_id, "query_length": len(query)},
    )

    try:
        state = await agent.ainvoke({"query": query, "metadata": {"run_id": run_id}})
    except Exception as exc:
        logger.error(
            "Agent run failed",
            extra={
                "event": "agent.run.failed",
                "run_id": run_id,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                "error_type": type(exc).__name__,
            },
        )
        raise

    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    if state.get("error"):
        logger.warning(
            "Agent run completed with an error result",
            extra={
                "event": "agent.run.error_result",
                "run_id": run_id,
                "duration_ms": duration_ms,
            },
        )
    else:
        logger.info(
            "Agent run completed",
            extra={
                "event": "agent.run.completed",
                "run_id": run_id,
                "duration_ms": duration_ms,
            },
        )

    return AgentResult(
        response=state.get("response", ""),
        analysis=state.get("analysis", ""),
        error=state.get("error"),
    )
