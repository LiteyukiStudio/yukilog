from __future__ import annotations

from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Self, cast

from loguru import logger as loguru_logger

from yukilog._context import complete_context

if TYPE_CHECKING:
    from loguru import Logger as LoguruLogger


class Logger:
    """Stable application logger facade.

    Sink management and Loguru-specific methods intentionally do not belong here.
    """

    __slots__ = ("_logger",)

    def __init__(self, backend: LoguruLogger) -> None:
        self._logger = backend

    def bind(self, **extra: object) -> Self:
        return type(self)(self._logger.bind(**extra))

    def contextualize(self, **extra: object) -> AbstractContextManager[None]:
        context = self._logger.contextualize(**extra)
        return cast(AbstractContextManager[None], context)

    def trace(self, message: str, *args: object, **kwargs: object) -> None:
        self._log("TRACE", message, *args, **kwargs)

    def debug(self, message: str, *args: object, **kwargs: object) -> None:
        self._log("DEBUG", message, *args, **kwargs)

    def info(self, message: str, *args: object, **kwargs: object) -> None:
        self._log("INFO", message, *args, **kwargs)

    def success(self, message: str, *args: object, **kwargs: object) -> None:
        self._log("SUCCESS", message, *args, **kwargs)

    def warning(self, message: str, *args: object, **kwargs: object) -> None:
        self._log("WARNING", message, *args, **kwargs)

    def error(self, message: str, *args: object, **kwargs: object) -> None:
        self._log("ERROR", message, *args, **kwargs)

    def critical(self, message: str, *args: object, **kwargs: object) -> None:
        self._log("CRITICAL", message, *args, **kwargs)

    def exception(self, message: str, *args: object, **kwargs: object) -> None:
        self._logger.opt(depth=1, exception=True).error(message, *args, **kwargs)

    def _log(self, level: str, message: str, *args: object, **kwargs: object) -> None:
        self._logger.opt(depth=2).log(level, message, *args, **kwargs)


def get_logger(
    *,
    component: str | None = None,
    plugin: str | None = None,
    runtime: str | None = None,
    event_id: str | None = None,
    bot_id: str | None = None,
    **extra: object,
) -> Logger:
    values = complete_context(
        {
            "component": component,
            "plugin": plugin,
            "runtime": runtime,
            "event_id": event_id,
            "bot_id": bot_id,
            **extra,
        }
    )
    return Logger(loguru_logger.bind(**values))
