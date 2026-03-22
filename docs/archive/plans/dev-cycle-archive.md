# Plan: Dev-Cycle Archive on Completion

> Source PRD: [#6](https://github.com/cdcoonce/claude-workflow/issues/6)

## Architectural decisions

- **Archive paths**: `docs/archive/dev-cycle/` for state files, `docs/archive/plans/` for plan files
- **Trigger**: Automatic as final step of Phase 7 and on feature abandonment
- **Mechanism**: `git mv` to preserve history; `mkdir -p` to create archive dirs if needed
- **Terminal states**: `completed` and `abandoned` both trigger archival
- **Files modified**: `core/skills/dev-cycle/SKILL.md`, `core/skills/dev-cycle/references/phase-transitions.md`, `core/skills/dev-cycle/references/state-file-schema.md`

---

## Phase 1: Add archival instructions to dev-cycle skill

**User stories**: 1, 2, 3, 4, 5, 6, 7

### What to build

Add archival behavior to three skill files:

1. **SKILL.md** — Add an "Archival" section after Phase 7 describing the archive step. Update Phase 7 to include archival as the final action. Update Feature Abandonment reference to mention archival.

2. **phase-transitions.md** — Update the "Code Review → PR" transition to include the archival step after setting `status: completed`. Update "Feature Abandonment" to include archival.

3. **state-file-schema.md** — Document the archive paths and add a note about where terminal-state files end up.

### Acceptance criteria

- [ ] SKILL.md Phase 7 includes archival as the final step after PR URL is recorded
- [ ] SKILL.md has an "Archival" section documenting the archive process
- [ ] SKILL.md Feature Abandonment reference mentions archival
- [ ] phase-transitions.md Code Review → PR includes `git mv` steps for both state and plan files
- [ ] phase-transitions.md Feature Abandonment includes archival steps
- [ ] state-file-schema.md documents archive paths (`docs/archive/dev-cycle/`, `docs/archive/plans/`)
- [ ] Archive directories are created with `mkdir -p` before moving
- [ ] `git mv` is specified (not plain `mv`) to preserve history
- [ ] Re-entry logic in SKILL.md is unaffected (still scans `docs/dev-cycle/` for active work)
