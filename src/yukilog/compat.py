"""Explicit Loguru compatibility escape hatch for legacy integrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger as loguru_logger

from yukilog._context import complete_context

if TYPE_CHECKING:
    from loguru import Logger as LoguruLogger


def get_loguru_logger(
    *,
    component: str | None = None,
    plugin: str | None = None,
    runtime: str | None = None,
    event_id: str | None = None,
    bot_id: str | None = None,
    **extra: object,
) -> LoguruLogger:
    """Return a bound native Loguru logger for compatibility-only code."""

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
    return loguru_logger.bind(**values)
