from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from yukilog._constants import CONTEXT_FIELDS

if TYPE_CHECKING:
    from loguru import Record


def complete_context(values: Mapping[str, object] | None = None) -> dict[str, object]:
    if not values:
        return {}
    context = dict(values)
    for field in CONTEXT_FIELDS:
        if context.get(field) is None:
            context.pop(field, None)
    return context


def prepare_record(record: Record) -> bool:
    extra = record["extra"]
    for field in CONTEXT_FIELDS:
        extra.setdefault(field, None)

    labels = [
        f"{field}={extra[field]}"
        for field in ("component", "plugin", "runtime")
        if extra[field] is not None
    ]
    extra["_yukilog_context"] = " ".join(labels) or "-"
    return True
