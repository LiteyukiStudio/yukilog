import inspect
import logging
from dataclasses import dataclass
from threading import RLock

from loguru import logger as loguru_logger

from yukilog._constants import CONTEXT_FIELDS
from yukilog._context import complete_context

_STANDARD_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__)


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = inspect.currentframe()
        depth = 0
        while frame is not None and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        record_values = vars(record)
        context_values = {
            field: record_values.get(field)
            for field in CONTEXT_FIELDS
            if field != "component"
        }
        context = complete_context(
            {
                "component": record_values.get("component", record.name),
                **context_values,
            }
        )
        extra = {
            key: value
            for key, value in record_values.items()
            if key not in _STANDARD_RECORD_FIELDS
            and key not in CONTEXT_FIELDS
            and key != "stdlib_logger"
        }
        backend = loguru_logger.bind(**context, stdlib_logger=record.name, **extra)
        backend.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


@dataclass(slots=True)
class _RootLoggingSnapshot:
    handlers: list[logging.Handler]
    level: int


_lock = RLock()
_snapshot: _RootLoggingSnapshot | None = None
_handler: _InterceptHandler | None = None


def intercept_stdlib_logging(*, level: int = logging.NOTSET) -> None:
    """Route propagating standard-library records through Yukilog."""

    global _handler, _snapshot
    with _lock:
        root = logging.getLogger()
        if _handler is not None:
            root.setLevel(level)
            return

        _snapshot = _RootLoggingSnapshot(handlers=list(root.handlers), level=root.level)
        _handler = _InterceptHandler()
        root.handlers[:] = [_handler]
        root.setLevel(level)


def restore_stdlib_logging() -> None:
    """Restore the root logger state captured by the first interception."""

    global _handler, _snapshot
    with _lock:
        if _snapshot is None:
            return
        root = logging.getLogger()
        root.handlers[:] = _snapshot.handlers
        root.setLevel(_snapshot.level)
        _handler = None
        _snapshot = None
