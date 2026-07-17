import pytest

from ai import run_agent
from ai.graph import agent


@pytest.mark.asyncio
async def test_agent_basic_flow():
    result = await agent.ainvoke({"query": "Hello"})
    assert "response" in result


@pytest.mark.asyncio
async def test_agent_state_structure():
    result = await agent.ainvoke({"query": "Test query"})
    assert isinstance(result, dict)
    assert "query" in result


@pytest.mark.asyncio
async def test_run_agent_public_api():
    """Interface công khai trả về AgentResult, không phải dict state."""
    result = await run_agent("Hello")
    assert result.response
    assert result.error is None
