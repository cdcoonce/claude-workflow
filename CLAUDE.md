# Claude Workflow Template System

This file is auto-loaded every conversation. It defines how Claude should work in this repo.

## What This Repo Is

A template system for Claude Code configurations. It produces ready-to-copy `.claude/` directories + `CLAUDE.md` files for new projects.

## Architecture

- `core/` — Universal skills (17), methodology docs (4), file protection hook
- `presets/` — Named project type configurations (python-api, data-pipeline, full-stack, claude-tooling, analysis)
- `scripts/` — Python build/diff/smoke-test tooling
- `dist/` — Build output (gitignored)

## Commands

- Build a preset: `uv run python -m scripts.build_preset <preset_name>`
- Diff a project: `uv run python -m scripts.diff_preset <preset_name> <project_path>`
- Smoke test: `uv run python -m scripts.smoke_test <preset_name>`
- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=scripts --cov-report=term-missing`

## Methodology

### TDD — Test-Driven Development

Write the test first. Watch it fail. Write minimal code to pass.
Full process: [core/docs/tdd.md](core/docs/tdd.md)

### Root Cause Tracing

Never fix at the symptom. Trace backward to the original trigger.
Full process: [core/docs/root-cause-tracing.md](core/docs/root-cause-tracing.md)

### Subagent-Driven Development

Dispatch a fresh subagent per task with code review between each.
Full process: [core/docs/subagent-development.md](core/docs/subagent-development.md)

### Parallel Agent Dispatch

When 3+ unrelated failures need investigation, dispatch one agent per problem domain.
Full process: [core/docs/parallel-agents.md](core/docs/parallel-agents.md)

## Code Style

- Descriptive variable names (`private_key_bytes` not `pkb`)
- SOLID, DRY, YAGNI — simplicity over complexity
- Type hints on all function signatures
- Numpy-style docstrings for public functions

## Planning

Write plans to `docs/plans/{file_name}.md`. Archive completed plans to `docs/archive/`.

## Skills

Skills live in `core/skills/` (universal) and `presets/*/skills/` (preset-specific).
See core CLAUDE.md for skill trigger conditions.
