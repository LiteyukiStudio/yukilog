from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from yukilog._constants import STRUCTURED_LOG_MARKER

type LogLevel = str | int
type StreamTarget = Literal["stdout", "stderr"]
type Rotation = str | int | None
type Retention = str | int | None


@dataclass(frozen=True, slots=True)
class ConsoleSink:
    """Human-readable console sink settings."""

    level: LogLevel = "INFO"
    target: StreamTarget = "stderr"
    colorize: bool | None = None
    enqueue: bool = False
    backtrace: bool = True
    diagnose: bool = False


@dataclass(frozen=True, slots=True)
class JsonSink:
    """Stable Yukilog JSON Lines sink settings."""

    level: LogLevel = "INFO"
    target: StreamTarget = "stdout"
    marker: str = STRUCTURED_LOG_MARKER
    enqueue: bool = False
    backtrace: bool = True
    diagnose: bool = False


@dataclass(frozen=True, slots=True)
class FileSink:
    """Rotating, human-readable file sink settings."""

    path: str | Path
    level: LogLevel = "DEBUG"
    rotation: Rotation = "10 MB"
    retention: Retention = "7 days"
    compression: str | None = None
    enqueue: bool = True
    backtrace: bool = True
    diagnose: bool = False
    encoding: str = "utf-8"


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Complete application-owned Yukilog sink configuration."""

    console: ConsoleSink | None = field(default_factory=ConsoleSink)
    json: JsonSink | None = None
    files: tuple[FileSink, ...] = ()
    remove_existing: bool = True
