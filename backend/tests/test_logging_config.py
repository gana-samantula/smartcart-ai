"""Structured logging output."""

import json
import logging

from app.core.logging_config import JsonFormatter


def test_formatter_emits_single_line_json_with_extra_fields() -> None:
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    record.request_id = "abc123"

    line = JsonFormatter().format(record)
    payload = json.loads(line)

    assert "\n" not in line
    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["request_id"] == "abc123"
    assert "timestamp" in payload
