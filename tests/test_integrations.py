import json
import logging

import pytest

from yukilog import (
    JsonSink,
    LoggingConfig,
    configure,
    intercept_stdlib_logging,
    restore_stdlib_logging,
)
from yukilog.compat import get_loguru_logger


def test_stdlib_interception_and_restore(capsys: pytest.CaptureFixture[str]) -> None:
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level
    configure(LoggingConfig(console=None, json=JsonSink()))

    intercept_stdlib_logging(level=logging.DEBUG)
    intercept_stdlib_logging(level=logging.INFO)
    logging.getLogger("dependency").warning(
        "deprecated",
        extra={"event_id": "event-1", "dependency_version": "2.0"},
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["component"] == "dependency"
    assert payload["event_id"] == "event-1"
    assert payload["extra"]["dependency_version"] == "2.0"
    assert payload["message"] == "deprecated"

    restore_stdlib_logging()
    assert root.handlers == original_handlers
    assert root.level == original_level


def test_loguru_compatibility_escape_hatch(capsys: pytest.CaptureFixture[str]) -> None:
    configure(LoggingConfig(console=None, json=JsonSink()))
    legacy = get_loguru_logger(plugin="legacy")
    legacy.opt(colors=True).info("<green>loaded</green>")

    payload = json.loads(capsys.readouterr().out)
    assert payload["plugin"] == "legacy"
    assert payload["message"] == "loaded"
