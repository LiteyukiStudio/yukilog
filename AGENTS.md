# Yukilog Agent Guide

## Project Role

Yukilog is the small logging boundary shared by Liteyuki applications. Its
runtime dependency budget is intentionally one package: Loguru. The public
facade must remain independent from Loguru sink configuration and private
record internals.

## Branches And Pull Requests

- `main` is the integration branch. Work on a topic branch created from the
  current `main`; never develop directly on `main`.
- Open a pull request back to `main` for every change. Keep the PR focused and
  explain compatibility, serialization, and sink-lifecycle impact.
- Do not rewrite or reset a dirty worktree. Preserve unrelated user changes.

## Commit Format

Use one Gitmoji followed by a short imperative description:

```text
✨ add contextual logger facade
🐛 preserve stdlib logging context
✅ cover child-runtime serialization
📝 document sink ownership
🔖 release 1.0.0
```

Keep each commit coherent. Do not combine unrelated refactors, generated
lockfile churn, and release metadata unless they are required by the same
change. The subject should be short enough to scan in `git log` and should not
end with a period.

## Development Contract

- Target CPython 3.14+ and manage dependencies with uv.
- Use `uv_build`; keep `py.typed`, strict Mypy, Ruff, and tests green.
- Imports must not add, remove, or reconfigure Loguru sinks. Application entry
  points own sink configuration explicitly.
- Keep `Logger`, `get_logger`, configuration dataclasses, and structured marker
  values stable. Additive changes are preferred; breaking changes require an
  explicit version decision and migration notes.
- Structured JSON Lines are a protocol surface. Preserve the marker and stable
  fields (`component`, `plugin`, `runtime`, `event_id`, `bot_id`) and keep child
  log decoding tolerant of unknown extra fields.
- Loguru-only behavior such as `opt()` belongs in the explicit
  `yukilog.compat` escape hatch, not in the stable facade.
- Standard-library interception must be reversible and must preserve useful
  context without taking ownership of non-propagating named loggers.
- Prefer the standard library and existing local helpers. Do not add a runtime
  dependency for convenience, typing-only functionality, or an unmeasured
  optimization.

## Required Verification

Run these commands from the repository root before requesting review:

```powershell
uv sync --locked
uv run ruff check .
uv run mypy
uv run pytest
uv build
git diff --check
```

When changing the public facade, configuration, child markers, or stdlib
interception, add a focused regression test and update `README.md`. Do not
commit `dist/`, coverage output, virtual environments, or local benchmark
artifacts.
