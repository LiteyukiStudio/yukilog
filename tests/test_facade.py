import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from yukilog import JsonSink, LoggingConfig, configure, get_logger


def _read_payloads(capsys: pytest.CaptureFixture[str]) -> list[dict[str, object]]:
    return [json.loads(line) for line in capsys.readouterr().out.splitlines()]


def test_all_facade_levels(capsys: pytest.CaptureFixture[str]) -> None:
    configure(LoggingConfig(console=None, json=JsonSink(level="TRACE")))
    log = get_logger()
    log.trace("trace")
    log.debug("debug")
    log.info("info")
    log.success("success")
    log.warning("warning")
    log.error("error")
    log.critical("critical")

    assert [payload["level"] for payload in _read_payloads(capsys)] == [
        "TRACE",
        "DEBUG",
        "INFO",
        "SUCCESS",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ]


def test_bind_returns_a_new_facade(capsys: pytest.CaptureFixture[str]) -> None:
    configure(LoggingConfig(console=None, json=JsonSink()))
    base = get_logger(component="base")
    child = base.bind(plugin="child")
    base.info("base")
    child.info("child")

    first, second = _read_payloads(capsys)
    assert first["plugin"] is None
    assert second["plugin"] == "child"


def test_caller_metadata_points_to_facade_caller(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure(LoggingConfig(console=None, json=JsonSink()))
    get_logger().info("caller")

    payload = _read_payloads(capsys)[0]
    assert payload["function"] == "test_caller_metadata_points_to_facade_caller"


def test_exception_serialization(capsys: pytest.CaptureFixture[str]) -> None:
    configure(LoggingConfig(console=None, json=JsonSink()))
    try:
        raise RuntimeError("broken")
    except RuntimeError:
        get_logger().exception("operation failed")

    exception = _read_payloads(capsys)[0]["exception"]
    assert isinstance(exception, dict)
    assert exception["type"] == "RuntimeError"
    assert exception["message"] == "broken"
    assert "raise RuntimeError" in str(exception["traceback"])


def test_context_is_isolated_between_async_tasks(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure(LoggingConfig(console=None, json=JsonSink()))
    log = get_logger(component="async")

    async def worker(event_id: str) -> None:
        with log.contextualize(event_id=event_id):
            await asyncio.sleep(0)
            log.info("handled")

    async def run_workers() -> None:
        await asyncio.gather(worker("event-a"), worker("event-b"))

    asyncio.run(run_workers())

    payloads = _read_payloads(capsys)
    assert {payload["event_id"] for payload in payloads} == {"event-a", "event-b"}


def test_concurrent_json_output_keeps_complete_lines(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure(LoggingConfig(console=None, json=JsonSink(level="INFO")))
    log = get_logger(component="concurrency")

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda index: log.info("item {index}", index=index), range(100)))

    payloads = _read_payloads(capsys)
    assert len(payloads) == 100
    assert {payload["message"] for payload in payloads} == {
        f"item {index}" for index in range(100)
    }
