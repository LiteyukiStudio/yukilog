from typing import Final

STRUCTURED_LOG_MARKER: Final = "yukilog.structured.v1"
CHILD_RUNTIME_LOG_MARKER: Final = "yukilog.child.v1"

CONTEXT_FIELDS: Final = ("component", "plugin", "runtime", "event_id", "bot_id")
