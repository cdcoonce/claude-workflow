# Plan: Rename code-review to daa-code-review

> Source PRD: https://github.com/cdcoonce/claude-workflow/issues/8

## Architectural decisions

Durable decisions that apply across all phases:

- **Skill directory**: `core/skills/code-review/` → `core/skills/daa-code-review/`
- **Skill name**: SKILL.md frontmatter `name:` field becomes `daa-code-review`
- **Output path**: `docs/code_reviews/` remains unchanged
- **Cleanup**: `.claude/.claude/` nested directory is deleted entirely
- **Rebuild**: `.claude/skills/` hierarchy rebuilt separately via `build_preset.py` after rename

### Exclusion list (do NOT rename)

These matches contain "code-review" or "code_review" but must NOT be changed:

- `code_review` as a dev-cycle pipeline phase name (e.g., in state file tables, phase transition docs)
- `docs/code_reviews/` output directory path
- `code-reviewer` subagent role name in `subagent-development.md`
- `core/CLAUDE-base.md` line 42 — already reads `/daa-code-review` (no change needed)

---

## Phase 1: Rename core skill directory & frontmatter

**User stories**: 1, 5

### What to build

Rename the `core/skills/code-review/` directory to `core/skills/daa-code-review/` and update the `name:` field in its SKILL.md frontmatter from `code-review` to `daa-code-review`.

### Acceptance criteria

- [ ] Directory `core/skills/daa-code-review/` exists with all original contents
- [ ] Directory `core/skills/code-review/` no longer exists
- [ ] SKILL.md frontmatter `name:` field reads `daa-code-review`
- [ ] All internal references within the skill's own files still resolve correctly

---

## Phase 2: Update cross-repo references

**User stories**: 2, 3

### What to build

Update every file outside the skill directory that references the old `code-review` name to use `daa-code-review`. Key files:

- `core/skills/dev-cycle/SKILL.md` — Phase 6 delegation
- `core/docs/subagent-development.md` — code-reviewer references
- `README.md` — skill inventory table and architecture diagram
- `.claude/skills/dev-cycle/SKILL.md` — active local copy of dev-cycle

### Acceptance criteria

- [ ] `core/skills/dev-cycle/SKILL.md` references `daa-code-review` in Phase 6
- [ ] `core/docs/subagent-development.md` references updated
- [ ] `README.md` skill table and Mermaid diagram use `daa-code-review`
- [ ] `.claude/skills/dev-cycle/SKILL.md` references updated
- [ ] No remaining references to the old `code-review` skill name (excluding `code_review` as a dev-cycle phase name and `docs/code_reviews/` output path)

---

## Phase 3: Update tests & cleanup

**User stories**: 4, 5

### What to build

Update test files that reference the old skill name, delete the erroneous `.claude/.claude/` directory, and verify everything passes.

### Acceptance criteria

- [ ] `tests/conftest.py` references `daa-code-review` instead of `code-review`
- [ ] `tests/test_build.py` references `daa-code-review` instead of `code-review`
- [ ] `.claude/.claude/` directory is deleted
- [ ] `uv run pytest` passes with no failures
- [ ] `uv run python scripts/smoke_test.py python-api` passes
