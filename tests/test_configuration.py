import json
import subprocess
import sys
from pathlib import Path

import pytest

from yukilog import (
    CHILD_RUNTIME_LOG_MARKER,
    ConsoleSink,
    FileSink,
    JsonSink,
    LoggingConfig,
    configure,
    configure_child_runtime,
    decode_child_runtime_line,
    get_logger,
    shutdown,
)


def test_import_does_not_change_loguru_handlers() -> None:
    code = """
from loguru import logger
before = tuple(logger._core.handlers)
import yukilog
after = tuple(logger._core.handlers)
assert before == after, (before, after)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_default_configuration_is_human_readable(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure()
    get_logger(component="api").info("Listening on {port}", port=8080)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "INFO" in captured.err
    assert "component=api" in captured.err
    assert "Listening on 8080" in captured.err


def test_equal_configuration_is_idempotent(capsys: pytest.CaptureFixture[str]) -> None:
    config = LoggingConfig(console=None, json=JsonSink())
    configure(config)
    configure(config)
    get_logger().info("once")

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["message"] == "once"


def test_new_configuration_replaces_previous_sinks(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure(LoggingConfig(console=ConsoleSink(target="stdout")))
    configure(LoggingConfig(console=None, json=JsonSink()))
    get_logger().info("one output")

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["message"] == "one output"


def test_json_contains_stable_context_and_extra(capsys: pytest.CaptureFixture[str]) -> None:
    configure(LoggingConfig(console=None, json=JsonSink()))
    log = get_logger(
        component="events", plugin="demo", runtime="worker", request_id=7, optional=None
    )
    with log.contextualize(event_id="evt-1", bot_id="bot-2"):
        log.info("handled")

    payload = json.loads(capsys.readouterr().out)
    assert payload["component"] == "events"
    assert payload["plugin"] == "demo"
    assert payload["runtime"] == "worker"
    assert payload["event_id"] == "evt-1"
    assert payload["bot_id"] == "bot-2"
    assert payload["extra"] == {"request_id": 7, "optional": None}


def test_child_runtime_lines_have_public_marker(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_child_runtime()
    get_logger(runtime="nonebot").warning("bridge lag")

    line = capsys.readouterr().out.strip()
    payload = decode_child_runtime_line(line)
    assert payload is not None
    assert payload["_yukilog"] == CHILD_RUNTIME_LOG_MARKER
    assert payload["runtime"] == "nonebot"


@pytest.mark.parametrize(
    "line",
    ["plain output", "{}", '{"_yukilog":"different"}', "[1,2,3]"],
)
def test_child_runtime_decoder_rejects_unmarked_lines(line: str) -> None:
    assert decode_child_runtime_line(line) is None


def test_file_sink_writes_and_flushes(tmp_path: Path) -> None:
    path = tmp_path / "logs" / "app.log"
    configure(
        LoggingConfig(
            console=None,
            files=(FileSink(path, enqueue=False, rotation=None, retention=None),),
        )
    )
    get_logger(plugin="sample").success("loaded")
    shutdown()

    content = path.read_text(encoding="utf-8")
    assert "SUCCESS" in content
    assert "plugin=sample" in content
    assert "loaded" in content


def test_configuration_failure_leaves_no_partial_sink(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(ValueError):
        configure(LoggingConfig(console=ConsoleSink(level="NOT_A_LEVEL")))

    configure(LoggingConfig(console=None, json=JsonSink()))
    get_logger().info("recovered")
    assert json.loads(capsys.readouterr().out)["message"] == "recovered"


def test_shutdown_is_idempotent() -> None:
    configure()
    shutdown()
    shutdown()
