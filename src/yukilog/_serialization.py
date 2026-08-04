from __future__ import annotations

import json
import traceback
from datetime import UTC
from threading import Lock
from typing import TYPE_CHECKING, TextIO, cast

from yukilog._constants import CHILD_RUNTIME_LOG_MARKER, CONTEXT_FIELDS

if TYPE_CHECKING:
    from loguru import Message, Record, RecordException


class JsonLineSink:
    __slots__ = ("_marker", "_stream", "_write_lock")

    def __init__(self, stream: TextIO, marker: str) -> None:
        self._stream = stream
        self._marker = marker
        self._write_lock = Lock()

    def __call__(self, message: Message) -> None:
        payload = record_to_payload(message.record, marker=self._marker)
        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
        with self._write_lock:
            self._stream.write(f"{line}\n")
            self._stream.flush()


def record_to_payload(record: Record, *, marker: str) -> dict[str, object]:
    extra = dict(record["extra"])
    extra.pop("_yukilog_context", None)
    context = {field: extra.pop(field, None) for field in CONTEXT_FIELDS}

    level = record["level"]
    process = record["process"]
    thread = record["thread"]
    timestamp = record["time"].astimezone(UTC).isoformat().replace("+00:00", "Z")

    payload: dict[str, object] = {
        "_yukilog": marker,
        "timestamp": timestamp,
        "level": str(level.name),
        "level_no": int(level.no),
        "message": str(record["message"]),
        "module": str(record["module"]),
        "function": str(record["function"]),
        "line": int(record["line"]),
        "process": {"id": int(process.id), "name": str(process.name)},
        "thread": {"id": int(thread.id), "name": str(thread.name)},
        **context,
        "extra": extra,
        "exception": _serialize_exception(record.get("exception")),
    }
    return payload


def decode_child_runtime_line(line: str) -> dict[str, object] | None:
    try:
        value = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(value, dict) or value.get("_yukilog") != CHILD_RUNTIME_LOG_MARKER:
        return None
    return cast(dict[str, object], value)


def _serialize_exception(exception: RecordException | None) -> dict[str, object] | None:
    if exception is None:
        return None
    exception_type = exception.type
    exception_value = exception.value
    return {
        "type": getattr(exception_type, "__name__", str(exception_type)),
        "message": str(exception_value),
        "traceback": "".join(traceback.format_exception(exception_value)),
    }
