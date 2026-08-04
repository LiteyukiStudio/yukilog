# Yukilog

Yukilog is the logging boundary shared by Liteyuki applications. It keeps
application code independent from Loguru's sink configuration API while retaining
a deliberately isolated compatibility escape hatch for legacy integrations.

Yukilog requires Python 3.14 or newer. Loguru is its only runtime dependency.

## Usage

Importing Yukilog does not add, remove, or reconfigure any sink. The application
entry point owns configuration:

```python
from yukilog import FileSink, LoggingConfig, configure, get_logger, shutdown

configure(
    LoggingConfig(
        files=(FileSink("logs/app.log", rotation="10 MB", retention="7 days"),),
    )
)

log = get_logger(component="api", runtime="main")
log.info("Listening on {address}", address="127.0.0.1:8000")

with log.contextualize(event_id="evt-42"):
    log.debug("Dispatching event")

shutdown()
```

`configure()` with no arguments installs one colored, human-readable stderr sink.
Repeated calls with an equal configuration are no-ops. A different configuration
replaces sinks previously installed by Yukilog. By default the first call also
removes existing Loguru sinks because configuration is an application-level
operation; set `remove_existing=False` when embedding Yukilog in another host.

Every facade logger carries the stable context fields `component`, `plugin`,
`runtime`, `event_id`, and `bot_id`. Values not known at bind time are `null` in
structured output. Arbitrary additional fields are retained under `extra`.

## Structured output

Use a JSON Lines sink for machine consumers:

```python
from yukilog import JsonSink, LoggingConfig, configure

configure(LoggingConfig(console=None, json=JsonSink()))
```

Supervised child runtimes use the dedicated marker and stdout-only configuration:

```python
from yukilog import configure_child_runtime

configure_child_runtime(level="DEBUG")
```

Each emitted line contains `"_yukilog":"yukilog.child.v1"`. The schema marker is
part of Yukilog's public protocol; Loguru's private serialized record shape is not.

## Standard library logging

`intercept_stdlib_logging()` replaces handlers on the root standard-library logger
and routes propagating records through Yukilog. It is idempotent. `shutdown()` (or
`restore_stdlib_logging()`) restores the root handlers and level captured at the
first interception. Named loggers with `propagate=False` remain application-owned.

## Legacy Loguru compatibility

New code should use `yukilog.Logger`. Code that genuinely requires Loguru-only
methods such as `opt()` must import the escape hatch explicitly:

```python
from yukilog.compat import get_loguru_logger

legacy_logger = get_loguru_logger(plugin="legacy.example")
legacy_logger.opt(colors=True).info("<green>Loaded</green>")
```

The returned object is Loguru-compatible and therefore is not covered by the stable
facade contract. Sink ownership remains with the application entry point.

## Development

```powershell
uv sync
uv run ruff check .
uv run mypy
uv run pytest
uv build
```
