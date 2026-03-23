# Claude Workflow — Project Context

Template factory that produces ready-to-copy Claude Code configurations (`.claude/` directories + `CLAUDE.md` files) for new projects.

## Tech Stack

- **Python >=3.12** — all scripts use stdlib only (no runtime dependencies)
- **uv** — package manager and task runner
- **hatchling** — build backend (packages only `scripts/`)
- **pytest** — test framework (81 tests across 5 modules)

## Project Layout

```text
core/                        Universal components shared by all presets
  skills/                    17 universal skills (tdd, commit, dev-cycle, etc.)
  docs/                      Methodology docs (tdd, root-cause-tracing, etc.)
  hooks/                     File protection hook (protect-files.py)
  agents/                    2 universal agents (tdd-implementer, code-reviewer)
  CLAUDE-base.md             Base CLAUDE.md content concatenated into output
  settings-base.json         Base hooks config merged into output
  agent-role-defaults.json   Role → skill mapping (implementer, reviewer)
presets/                     5 named project configurations
  python-api/                Lambda, FastAPI, Flask
  full-stack/                React/Next.js + Python
  data-pipeline/             Data engineering workflows
  analysis/                  Data analysis & Jupyter
  claude-tooling/            Claude Code toolkit development
  <each contains>            manifest.json, CLAUDE-preset.md, settings-preset.json, skills/, hooks/, agents/
scripts/                     Python build/test/validation tooling
  build_preset.py            Assemble core + preset into dist/ (11-step pipeline)
  diff_preset.py             Compare project .claude/ against freshly-built preset
  smoke_test.py              Validate internal consistency of built output
  dev_cycle_validate.py      Parse/validate dev-cycle state files
tests/                       pytest suite (conftest.py + 5 test modules)
dist/                        Build output (gitignored)
docs/                        Plans and archives for this metaproject
```

## Data Flow

```text
core/skills,docs,hooks,agents ─┐
                                ├─→ build_preset() ─→ dist/<preset>/
presets/<name>/manifest.json ──┘        │                 ├── .claude/  (skills, docs, hooks, agents, settings.json)
                                        │                 └── CLAUDE.md
                                        │
                                   smoke_test() ─→ validates internal consistency
                                        │
                              (copy to new project)
                                        │
                                   diff_preset() ─→ detects drift from baseline
```

## Key Architecture Patterns

- **Manifest-driven composition** (`presets/*/manifest.json`): Each preset declares what core components to include, what to exclude, and what preset-specific overrides to layer on.
- **Override semantics** (`build_preset.py`): Preset skills/agents with the same name as core ones replace them; settings arrays append rather than replace.
- **Fail-fast validation** (`build_preset.py:_validate_manifest()`): All manifest references checked before any files are copied; errors aggregated, not one-at-a-time.
- **Path containment safety** (`build_preset.py`): Exclusion paths resolved and verified to stay within output directory, preventing `../../` escapes.
- **Template versioning** (`.template-version`): Output tagged with `git describe --tags --always` to enable drift detection.

## Test Markers

- `uv run pytest` — run all 81 tests
- `uv run pytest --cov=scripts --cov-report=term-missing` — run with coverage over `scripts/`
- No custom pytest markers defined

## Custom Exceptions

- `BuildValidationError` (`build_preset.py`) — manifest references invalid files
- `SmokeTestFailure` (`smoke_test.py`) — internal consistency check failures
