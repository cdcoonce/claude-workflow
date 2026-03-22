# Plan: Fix schema_version Validator/Spec Mismatch

**PRD:** [Issue #24](https://github.com/cdcoonce/claude-workflow/issues/24)

## Problem

`scripts/dev_cycle_validate.py` requires `schema_version` as a mandatory field, but two archived state files (`fix-script-imports.state.md`, `update-write-a-skill.state.md`) predate the schema standardization and lack this field. Running the validator against these files fails.

The state file schema reference (`state-file-schema.md`) already includes `schema_version` in its template — so new files are fine. The gap is backward compatibility in the validator.

## Approach: Option C (from issue #24)

Both add `schema_version` to legacy files AND make the validator more tolerant:

### Slice 1: Make validator default `schema_version` when missing

**Files:** `scripts/dev_cycle_validate.py`, `tests/test_dev_cycle_validate.py`

- In `parse_state_file()`, if `schema_version` is not present in frontmatter, default to `1` and emit a warning (not an error)
- Remove `schema_version` from `REQUIRED_FIELDS` tuple
- Add `warnings: list[str]` field to `ValidationResult` dataclass for non-blocking issues
- In `parse_state_file()`, default `raw_fields["schema_version"] = "1"` when missing (before `StateFile` constructor)
- In `_validate_parsed_state()` or `validate_state_file()`, add warning when schema_version was defaulted
- CLI prints warnings but exits 0 when only warnings (no errors)
- New test: `test_parse_missing_schema_version_defaults_to_1`
- New test: `test_missing_schema_version_produces_warning`
- Existing tests remain unchanged (still valid)

**Acceptance criteria:**

- Validator passes on files missing `schema_version` (with warning)
- Validator still fails on files missing other required fields
- Existing tests still pass

### Slice 2: Add `schema_version` to legacy archived state files

**Files:** `docs/archive/dev-cycle/fix-script-imports.state.md`, `docs/archive/dev-cycle/update-write-a-skill.state.md`

- Add `schema_version: 1` to the YAML frontmatter of both files
- Validate both files pass after the change

**Acceptance criteria:**

- Both files include `schema_version: 1`
- `uv run python -m scripts.dev_cycle_validate docs/archive/dev-cycle/` passes clean (no warnings)

## Out of Scope

- Migrating legacy files to the new table format (different artifact/phase table structures)
- Adding `updated` field to legacy files
- Removing the extra `slug` field from legacy files
