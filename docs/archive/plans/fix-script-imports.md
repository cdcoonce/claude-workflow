# Plan: Fix Script Invocation

> Source PRD: https://github.com/cdcoonce/claude-workflow/issues/19

## Architectural decisions

Durable decisions that apply across all phases:

- **Invocation pattern**: All scripts use `uv run python -m scripts.<module>` (not `uv run python scripts/<module>.py`)
- **Import style**: Package-style imports (`from scripts.build_preset import ...`) are correct and unchanged
- **Scope**: Active files only — archived plans and historical docs are left as-is

---

## Phase 1: Fix script usage strings

**User stories**: 1 (copy-paste commands work), 3 (correct usage output)

### What to build

Update the `__main__` usage strings in all four scripts to show the correct `python -m` invocation. Also fix the module-level docstring in `diff_preset.py` which documents the old style.

### Acceptance criteria

- [ ] `build_preset.py` usage string uses `python -m scripts.build_preset`
- [ ] `smoke_test.py` usage string uses `python -m scripts.smoke_test`
- [ ] `diff_preset.py` docstring and usage string use `python -m scripts.diff_preset`
- [ ] `dev_cycle_validate.py` usage string uses `python -m scripts.dev_cycle_validate`
- [ ] Each script runs successfully via `uv run python -m scripts.<module>`
- [ ] Existing tests pass (`uv run pytest`)

---

## Phase 2: Fix documentation

**User stories**: 1 (CLAUDE.md), 2 (README.md), 4 (skill references)

### What to build

Update all active documentation files that reference the old invocation style. This includes the project's main docs and skill reference files.

### Acceptance criteria

- [ ] `CLAUDE.md` commands section uses `python -m` style
- [ ] `README.md` examples use `python -m` style
- [ ] `core/skills/dev-cycle/references/state-file-schema.md` uses `python -m` style
- [ ] `.claude/skills/dev-cycle/references/state-file-schema.md` uses `python -m` style
- [ ] No active file (outside `docs/archive/` and `docs/superpowers/plans/`) references the old `python scripts/X.py` pattern
