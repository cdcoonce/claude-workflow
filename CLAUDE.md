# Claude Workflow Template System

This file is auto-loaded every conversation. It defines how Claude should work in this repo.

## What This Repo Is

A template system for Claude Code plugin configurations. It builds self-contained plugin directories (with `.claude-plugin/plugin.json`, skills, agents, hooks, and settings) for new projects.

See [.claude/docs/project.md](.claude/docs/project.md) for detailed project context (tech stack, data flow, architecture patterns).

## Architecture

- `core/` — Universal skills (17), methodology docs (4), file protection hook, agents (2)
- `presets/` — Named project type configurations (python-api, data-pipeline, full-stack, claude-tooling, analysis)
- `scripts/` — Python build/smoke-test/marketplace tooling
- `dist/` — Build output (gitignored)

## Commands

- Build a preset: `uv run python -m scripts.build_preset <preset_name>`
- Build marketplace index: `uv run python -m scripts.build_marketplace`
- Smoke test: `uv run python -m scripts.smoke_test <preset_name>`
- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=scripts --cov-report=term-missing`

## Code Style

- Descriptive variable names (`private_key_bytes` not `pkb`)
- SOLID, DRY, YAGNI — simplicity over complexity
- Type hints on all function signatures
- Numpy-style docstrings for public functions

### Frontmatter/YAML parsing

Prefer a real YAML parser (e.g. `PyYAML`) over hand-rolled line-based parsing
whenever one is available. When a dependency-free, line-based parser is
unavoidable (e.g. `scripts/smoke_test.py::_parse_frontmatter`, or any
frontmatter validation logic added to the daa-code-review skill), it must
correctly handle:

- **Block scalars** — `>` (folded) and `|` (literal), including chomping
  (`-`, `+`) and explicit indentation indicators (e.g. `>-`, `|2`). The
  indicator character itself must never be stored as the parsed value.
- **Quoted values** — surrounding `'single'` or `"double"` quotes must be
  stripped from scalar values.
- **Comments** — full-line and inline `#` comments must be stripped, without
  treating a `#` inside a quoted value or a folded block-scalar line as a
  comment.

Any change that adds or modifies a hand-rolled frontmatter parser must
include a folded/block-scalar test case (e.g. `description: >` followed by
wrapped, colon-containing lines) exercising these behaviors.

Context: in PR #105, `_parse_frontmatter`'s original block-scalar handling
stored the literal `>` indicator as the value instead of the folded text,
and a folded line containing a colon was misparsed as a nested sub-key — a
follow-up commit was required to fix both.

## Planning

Write plans to `docs/plans/{file_name}.md`. Archive completed plans to `docs/archive/`.

## Skills

Skills live in `core/skills/` (universal) and `presets/*/skills/` (preset-specific).
See core CLAUDE.md for skill trigger conditions.

## Agents

Agents are specialized role definitions (`AGENT.md` with YAML frontmatter) that give subagents domain expertise. Each agent is self-contained -- skills are declared directly in the agent's frontmatter via `skills.add`/`skills.remove`.

- `core/agents/` — Universal agents: `tdd-implementer` (implementer), `code-reviewer` (reviewer), `skill-analyst` (analyst), `qa-tester` (qa-tester), `skill-writer` (skill-writer), `strategy` (strategy)
- `presets/*/agents/` — Preset-specific agents (e.g., `api-builder`, `security-reviewer`)

### Agent file format

```yaml
---
name: agent-name # Must match directory name
description: one-liner # Used for convention-based matching
role: implementer # implementer | reviewer | analyst | qa-tester | skill-writer | strategy
skills:
  add: [tdd, commit]
  remove: []
---
```

### Manifest fields

- `core.agents` — `"all"` (default) or list of agent names to include
- `preset_agents` — List of preset-specific agent names (default `[]`)
- Exclusion format: `agents/<name>`
- Preset agent with same name as core agent replaces it (override semantics)
