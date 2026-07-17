import json
import logging
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import ValidationError

import ai
from ai.config import AISettings
from ai.logging import LOGGER_NAME, JsonFormatter, configure_ai_logging


def test_json_formatter_includes_structured_context():
    record = logging.LogRecord(
        name=LOGGER_NAME,
        level=logging.INFO,
        pathname=__file__,
        lineno=12,
        msg="Agent run completed",
        args=(),
        exc_info=None,
    )
    record.event = "agent.run.completed"
    record.run_id = "run-123"
    record.duration_ms = 12.5

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["event"] == "agent.run.completed"
    assert payload["run_id"] == "run-123"
    assert payload["duration_ms"] == 12.5


def test_configure_ai_logging_is_idempotent():
    settings = AISettings(ai_log_level="DEBUG", ai_log_format="text")

    logger = configure_ai_logging(settings)
    configured_handlers = list(logger.handlers)
    logger = configure_ai_logging(settings)

    assert logger.level == logging.DEBUG
    assert logger.handlers == configured_handlers
    assert logger.propagate is False


def test_ai_log_config_rejects_invalid_values():
    with pytest.raises(ValidationError):
        AISettings(ai_log_level="VERBOSE")


@pytest.mark.asyncio
async def test_run_agent_emits_lifecycle_events_without_query_content(monkeypatch):
    logger = Mock()
    fake_agent = Mock(ainvoke=AsyncMock(return_value={"response": "ok", "analysis": "done"}))
    monkeypatch.setattr(ai, "get_ai_logger", lambda: logger)
    monkeypatch.setattr(ai, "agent", fake_agent)

    await ai.run_agent("sensitive customer message")

    started = logger.info.call_args_list[0]
    completed = logger.info.call_args_list[1]
    assert started.kwargs["extra"]["event"] == "agent.run.started"
    assert started.kwargs["extra"]["query_length"] == 26
    assert completed.kwargs["extra"]["event"] == "agent.run.completed"
    assert started.kwargs["extra"]["run_id"] == completed.kwargs["extra"]["run_id"]
    assert "sensitive customer message" not in str(logger.mock_calls)


@pytest.mark.asyncio
async def test_run_agent_logs_failure_type_and_reraises(monkeypatch):
    logger = Mock()
    fake_agent = Mock(ainvoke=AsyncMock(side_effect=RuntimeError("provider unavailable")))
    monkeypatch.setattr(ai, "get_ai_logger", lambda: logger)
    monkeypatch.setattr(ai, "agent", fake_agent)

    with pytest.raises(RuntimeError, match="provider unavailable"):
        await ai.run_agent("query")

    failure = logger.error.call_args
    assert failure.kwargs["extra"]["event"] == "agent.run.failed"
    assert failure.kwargs["extra"]["error_type"] == "RuntimeError"
