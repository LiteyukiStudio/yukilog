import sys
from pathlib import Path
from threading import RLock
from typing import TextIO

from loguru import logger as loguru_logger

from yukilog._config import ConsoleSink, FileSink, JsonSink, LoggingConfig, StreamTarget
from yukilog._constants import CHILD_RUNTIME_LOG_MARKER
from yukilog._context import prepare_record
from yukilog._serialization import JsonLineSink
from yukilog._stdlib import restore_stdlib_logging

_HUMAN_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[_yukilog_context]}</cyan> | "
    "<level>{message}</level>\n{exception}"
)
_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "{extra[_yukilog_context]} | {message}\n{exception}"
)

_lock = RLock()
_sink_ids: set[int] = set()
_current_config: LoggingConfig | None = None


def configure(config: LoggingConfig | None = None) -> None:
    """Install the requested sinks, replacing the previous Yukilog configuration."""

    global _current_config
    requested = config or LoggingConfig()
    with _lock:
        if requested == _current_config:
            return

        if requested.remove_existing:
            loguru_logger.remove()
            _sink_ids.clear()
        else:
            _remove_installed_sinks()

        try:
            if requested.console is not None:
                _sink_ids.add(_add_console_sink(requested.console))
            if requested.json is not None:
                _sink_ids.add(_add_json_sink(requested.json))
            for file_sink in requested.files:
                _sink_ids.add(_add_file_sink(file_sink))
        except Exception:
            _remove_installed_sinks()
            _current_config = None
            raise

        _current_config = requested


def configure_child_runtime(
    *, level: str | int = "INFO", target: StreamTarget = "stdout", enqueue: bool = False
) -> None:
    """Configure marked JSON Lines output for a supervised child runtime."""

    configure(
        LoggingConfig(
            console=None,
            json=JsonSink(
                level=level,
                target=target,
                marker=CHILD_RUNTIME_LOG_MARKER,
                enqueue=enqueue,
            ),
        )
    )


def shutdown() -> None:
    """Flush and remove Yukilog sinks, then restore standard-library logging."""

    global _current_config
    with _lock:
        loguru_logger.complete()
        _remove_installed_sinks()
        _current_config = None
        restore_stdlib_logging()


def _add_console_sink(config: ConsoleSink) -> int:
    return loguru_logger.add(
        _resolve_stream(config.target),
        level=config.level,
        format=_HUMAN_FORMAT,
        colorize=config.colorize,
        enqueue=config.enqueue,
        backtrace=config.backtrace,
        diagnose=config.diagnose,
        filter=prepare_record,
    )


def _add_json_sink(config: JsonSink) -> int:
    sink = JsonLineSink(_resolve_stream(config.target), config.marker)
    return loguru_logger.add(
        sink,
        level=config.level,
        format="{message}",
        colorize=False,
        enqueue=config.enqueue,
        backtrace=config.backtrace,
        diagnose=config.diagnose,
        filter=prepare_record,
    )


def _add_file_sink(config: FileSink) -> int:
    return loguru_logger.add(
        Path(config.path),
        level=config.level,
        format=_FILE_FORMAT,
        colorize=False,
        rotation=config.rotation,
        retention=config.retention,
        compression=config.compression,
        enqueue=config.enqueue,
        backtrace=config.backtrace,
        diagnose=config.diagnose,
        encoding=config.encoding,
        filter=prepare_record,
    )


def _resolve_stream(target: StreamTarget) -> TextIO:
    return sys.stdout if target == "stdout" else sys.stderr


def _remove_installed_sinks() -> None:
    for sink_id in tuple(_sink_ids):
        try:
            loguru_logger.remove(sink_id)
        except ValueError:
            pass
        finally:
            _sink_ids.discard(sink_id)
