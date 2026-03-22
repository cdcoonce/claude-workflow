# Dev Cycle Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `/dev-cycle` skill — a 7-phase orchestrator that tracks feature development from brainstorm through PR, with a Python state file validator as its testable backbone.

**Architecture:** Prompt-based skill (`core/skills/dev-cycle/`) delegates to existing skills via a glue layer. A markdown state file in `docs/dev-cycle/` tracks progress across conversations. `scripts/dev_cycle_validate.py` provides programmatic validation of state files.

**Tech Stack:** Python 3.12+, pytest, YAML frontmatter parsing (no external deps — use regex), markdown skill files.

**Spec:** `docs/superpowers/specs/2026-03-22-dev-cycle-design.md`

---

## File Structure

```
Files to CREATE:
  scripts/dev_cycle_validate.py          — State file parser + validator (main testable code)
  tests/test_dev_cycle_validate.py       — Tests for the validator
  core/skills/dev-cycle/SKILL.md         — Main skill: orchestration logic, re-entry, phase dispatch
  core/skills/dev-cycle/references/phase-transitions.md   — Glue layer specs per transition
  core/skills/dev-cycle/references/state-file-schema.md   — State file format + rules

Files to MODIFY:
  core/skills/prd-to-plan/SKILL.md:3,8,60  — Change ./plans/ to docs/plans/
  core/CLAUDE-base.md:88-89                 — Add /dev-cycle skill registration
```

---

## Task 1: Fix `prd-to-plan` output path

**Files:**

- Modify: `core/skills/prd-to-plan/SKILL.md:3,8,60`

This is the prerequisite fix identified in the CEO review. The `prd-to-plan` skill currently outputs to `./plans/` but the canonical path is `docs/plans/`.

- [ ] **Step 1: Update the description (line 3)**

Change:

```
saved as a local Markdown file in ./plans/
```

to:

```
saved as a local Markdown file in docs/plans/
```

- [ ] **Step 2: Update the process header (line 8)**

Change:

```
Output is a Markdown file in `./plans/`.
```

to:

```
Output is a Markdown file in `docs/plans/`.
```

- [ ] **Step 3: Update step 6 output instructions (line 60)**

Change:

```
Create `./plans/` if it doesn't exist. Write the plan as a Markdown file named after the feature (e.g. `./plans/user-onboarding.md`).
```

to:

```
Create `docs/plans/` if it doesn't exist. Write the plan as a Markdown file named after the feature (e.g. `docs/plans/user-onboarding.md`).
```

- [ ] **Step 4: Commit**

```bash
git add core/skills/prd-to-plan/SKILL.md
git commit -m "fix: update prd-to-plan output path from ./plans/ to docs/plans/"
```

---

## Task 2: State file validator — data models and parsing (TDD)

**Files:**

- Create: `scripts/dev_cycle_validate.py`
- Create: `tests/test_dev_cycle_validate.py`

This is the core testable deliverable. We build it incrementally via TDD cycles. This first task covers the data model and YAML frontmatter parsing.

- [ ] **Step 1: Write the failing test — parse valid state file frontmatter**

```python
# tests/test_dev_cycle_validate.py
"""Tests for dev_cycle_validate — state file parser and validator."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.dev_cycle_validate import StateFile, parse_state_file


class TestParseStateFile:
    """Tests for YAML frontmatter parsing."""

    def test_parse_valid_state_file(self, tmp_path: Path) -> None:
        content = """\
---
schema_version: 1
feature: dark-mode-toggle
status: in_progress
current_phase: plan
created: 2026-03-21
updated: 2026-03-21
branch: feat/dark-mode-toggle
---

## Artifacts

| Phase       | Status      | Artifact                               |
| ----------- | ----------- | -------------------------------------- |
| brainstorm  | completed   | https://github.com/user/repo/issues/42 |
| plan        | in_progress | docs/plans/dark-mode-toggle.md         |
| ceo_review  | pending     | —                                      |

## Log

- 2026-03-21 10:15 — Brainstorm complete.
"""
        state_file = tmp_path / "dark-mode-toggle.md"
        state_file.write_text(content)

        result = parse_state_file(state_file)

        assert result.schema_version == 1
        assert result.feature == "dark-mode-toggle"
        assert result.status == "in_progress"
        assert result.current_phase == "plan"
        assert result.branch == "feat/dark-mode-toggle"
        assert result.path == state_file

    def test_parse_missing_frontmatter_raises(self, tmp_path: Path) -> None:
        state_file = tmp_path / "bad.md"
        state_file.write_text("# No frontmatter here\n")

        with pytest.raises(ValueError, match="frontmatter"):
            parse_state_file(state_file)

    def test_parse_missing_required_field_raises(self, tmp_path: Path) -> None:
        content = """\
---
schema_version: 1
feature: dark-mode-toggle
---
"""
        state_file = tmp_path / "incomplete.md"
        state_file.write_text(content)

        with pytest.raises(ValueError, match="status"):
            parse_state_file(state_file)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dev_cycle_validate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.dev_cycle_validate'`

- [ ] **Step 3: Write minimal implementation — StateFile dataclass and parser**

```python
# scripts/dev_cycle_validate.py
"""Dev cycle state file parser and validator.

Parses YAML frontmatter from dev-cycle state files and validates
schema integrity, phase transitions, and artifact completeness.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

VALID_PHASES = (
    "brainstorm", "plan", "ceo_review", "issues",
    "implement", "code_review", "pr",
)
VALID_STATUSES = ("not_started", "in_progress", "completed", "abandoned")
VALID_ARTIFACT_STATUSES = ("pending", "in_progress", "completed", "blocked")
CURRENT_SCHEMA_VERSION = 1

_FRONTMATTER_RE = re.compile(r"\A---\n(.+?)\n---", re.DOTALL)
_FIELD_RE = re.compile(r"^(\w+):\s*(.+?)(?:\s*#.*)?$", re.MULTILINE)

REQUIRED_FIELDS = ("schema_version", "feature", "status", "current_phase")


@dataclass
class StateFile:
    """Parsed representation of a dev-cycle state file."""

    schema_version: int
    feature: str
    status: str
    current_phase: str
    created: str = ""
    updated: str = ""
    branch: str = ""
    path: Path = field(default_factory=lambda: Path())


def parse_state_file(path: Path) -> StateFile:
    """Parse a dev-cycle state file and return a StateFile object.

    Parameters
    ----------
    path : Path
        Path to the state file.

    Returns
    -------
    StateFile
        Parsed state file data.

    Raises
    ------
    ValueError
        If the file has no frontmatter or is missing required fields.
    """
    text = path.read_text()
    match = _FRONTMATTER_RE.search(text)
    if not match:
        raise ValueError(f"No YAML frontmatter found in {path.name}")

    raw_fields: dict[str, str] = {}
    for field_match in _FIELD_RE.finditer(match.group(1)):
        raw_fields[field_match.group(1)] = field_match.group(2).strip()

    for req in REQUIRED_FIELDS:
        if req not in raw_fields:
            raise ValueError(
                f"Missing required field '{req}' in {path.name}"
            )

    return StateFile(
        schema_version=int(raw_fields["schema_version"]),
        feature=raw_fields["feature"],
        status=raw_fields["status"],
        current_phase=raw_fields["current_phase"],
        created=raw_fields.get("created", ""),
        updated=raw_fields.get("updated", ""),
        branch=raw_fields.get("branch", ""),
        path=path,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dev_cycle_validate.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/dev_cycle_validate.py tests/test_dev_cycle_validate.py
git commit -m "feat(dev-cycle): add state file parser with TDD tests"
```

---

## Task 3: State file validator — field validation (TDD)

**Files:**

- Modify: `scripts/dev_cycle_validate.py`
- Modify: `tests/test_dev_cycle_validate.py`

Add validation for field values: schema_version, status, current_phase.

- [ ] **Step 1: Write failing tests — validate field values**

Append to `tests/test_dev_cycle_validate.py`:

```python
from scripts.dev_cycle_validate import ValidationResult, validate_state_file


class TestValidateStateFile:
    """Tests for field value validation."""

    def _write_state_file(
        self, tmp_path: Path, **overrides: str
    ) -> Path:
        """Helper: write a valid state file, then override specific fields."""
        defaults = {
            "schema_version": "1",
            "feature": "test-feature",
            "status": "in_progress",
            "current_phase": "plan",
            "created": "2026-03-21",
            "updated": "2026-03-21",
            "branch": "",
        }
        defaults.update(overrides)
        fields = "\n".join(f"{k}: {v}" for k, v in defaults.items() if v)
        content = f"---\n{fields}\n---\n\n## Artifacts\n\n## Log\n"
        path = tmp_path / f"{defaults['feature']}.md"
        path.write_text(content)
        return path

    def test_valid_file_passes(self, tmp_path: Path) -> None:
        path = self._write_state_file(tmp_path)
        result = validate_state_file(path)
        assert result.passed

    def test_invalid_status_fails(self, tmp_path: Path) -> None:
        path = self._write_state_file(tmp_path, status="bogus")
        result = validate_state_file(path)
        assert not result.passed
        assert any("status" in e for e in result.errors)

    def test_invalid_phase_fails(self, tmp_path: Path) -> None:
        path = self._write_state_file(tmp_path, current_phase="testing")
        result = validate_state_file(path)
        assert not result.passed
        assert any("current_phase" in e for e in result.errors)

    def test_unsupported_schema_version_fails(self, tmp_path: Path) -> None:
        path = self._write_state_file(tmp_path, schema_version="99")
        result = validate_state_file(path)
        assert not result.passed
        assert any("schema_version" in e for e in result.errors)

    def test_feature_slug_mismatch_fails(self, tmp_path: Path) -> None:
        """Feature slug must match the filename."""
        path = self._write_state_file(tmp_path, feature="wrong-name")
        # File is named 'wrong-name.md' by the helper, so rename it
        renamed = tmp_path / "different-name.md"
        path.rename(renamed)
        result = validate_state_file(renamed)
        assert not result.passed
        assert any("filename" in e for e in result.errors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_dev_cycle_validate.py::TestValidateStateFile -v`
Expected: FAIL — `ImportError: cannot import name 'ValidationResult'`

- [ ] **Step 3: Implement ValidationResult and validate_state_file**

Add to `scripts/dev_cycle_validate.py`:

```python
@dataclass
class ValidationResult:
    """Result of validating a state file."""

    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def validate_state_file(path: Path) -> ValidationResult:
    """Validate a single dev-cycle state file.

    Parameters
    ----------
    path : Path
        Path to the state file.

    Returns
    -------
    ValidationResult
        Validation result with any errors found.
    """
    errors: list[str] = []

    try:
        state = parse_state_file(path)
    except ValueError as exc:
        return ValidationResult(errors=[str(exc)])

    if state.schema_version > CURRENT_SCHEMA_VERSION:
        errors.append(
            f"Unsupported schema_version {state.schema_version} "
            f"in {path.name} (max supported: {CURRENT_SCHEMA_VERSION})"
        )

    if state.status not in VALID_STATUSES:
        errors.append(
            f"Invalid status '{state.status}' in {path.name}. "
            f"Valid values: {', '.join(VALID_STATUSES)}"
        )

    if state.current_phase not in VALID_PHASES:
        errors.append(
            f"Invalid current_phase '{state.current_phase}' in {path.name}. "
            f"Valid values: {', '.join(VALID_PHASES)}"
        )

    expected_slug = path.stem
    if state.feature != expected_slug:
        errors.append(
            f"Feature slug '{state.feature}' does not match "
            f"filename '{expected_slug}' in {path.name}"
        )

    return ValidationResult(errors=errors)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_dev_cycle_validate.py -v`
Expected: 8 PASSED (3 from Task 2 + 5 new)

- [ ] **Step 5: Commit**

```bash
git add scripts/dev_cycle_validate.py tests/test_dev_cycle_validate.py
git commit -m "feat(dev-cycle): add state file field validation"
```

---

## Task 4: State file validator — artifact completeness + slug collisions (TDD)

**Files:**

- Modify: `scripts/dev_cycle_validate.py`
- Modify: `tests/test_dev_cycle_validate.py`

- [ ] **Step 1: Write failing tests — artifact completeness and slug collisions**

Append to `tests/test_dev_cycle_validate.py`:

```python
from scripts.dev_cycle_validate import validate_directory


class TestArtifactCompleteness:
    """Completed phases must have non-empty artifacts."""

    def test_completed_phase_without_artifact_fails(
        self, tmp_path: Path
    ) -> None:
        content = """\
---
schema_version: 1
feature: test-feature
status: in_progress
current_phase: plan
created: 2026-03-21
updated: 2026-03-21
---

## Artifacts

| Phase       | Status      | Artifact |
| ----------- | ----------- | -------- |
| brainstorm  | completed   | —        |
| plan        | in_progress | —        |

## Log
"""
        path = tmp_path / "test-feature.md"
        path.write_text(content)
        result = validate_state_file(path)
        assert not result.passed
        assert any("brainstorm" in e and "artifact" in e.lower() for e in result.errors)

    def test_completed_phase_with_artifact_passes(
        self, tmp_path: Path
    ) -> None:
        content = """\
---
schema_version: 1
feature: test-feature
status: in_progress
current_phase: plan
created: 2026-03-21
updated: 2026-03-21
---

## Artifacts

| Phase       | Status      | Artifact                               |
| ----------- | ----------- | -------------------------------------- |
| brainstorm  | completed   | https://github.com/user/repo/issues/42 |
| plan        | in_progress | docs/plans/test-feature.md             |

## Log
"""
        path = tmp_path / "test-feature.md"
        path.write_text(content)
        result = validate_state_file(path)
        assert result.passed


class TestValidateDirectory:
    """Tests for scanning docs/dev-cycle/ for slug collisions."""

    def test_no_collisions_passes(self, tmp_path: Path) -> None:
        dev_cycle = tmp_path / "docs" / "dev-cycle"
        dev_cycle.mkdir(parents=True)
        for name in ("feature-a", "feature-b"):
            (dev_cycle / f"{name}.md").write_text(
                f"---\nschema_version: 1\nfeature: {name}\n"
                f"status: in_progress\ncurrent_phase: brainstorm\n"
                f"created: 2026-03-21\nupdated: 2026-03-21\n---\n\n"
                f"## Artifacts\n\n## Log\n"
            )
        result = validate_directory(dev_cycle)
        assert result.passed

    def test_detects_slug_collision(self, tmp_path: Path) -> None:
        """Two files with the same feature slug is a collision."""
        dev_cycle = tmp_path / "docs" / "dev-cycle"
        dev_cycle.mkdir(parents=True)
        for filename in ("feature-a.md", "feature-a-copy.md"):
            (dev_cycle / filename).write_text(
                "---\nschema_version: 1\nfeature: feature-a\n"
                "status: in_progress\ncurrent_phase: brainstorm\n"
                "created: 2026-03-21\nupdated: 2026-03-21\n---\n\n"
                "## Artifacts\n\n## Log\n"
            )
        result = validate_directory(dev_cycle)
        assert not result.passed
        assert any("collision" in e.lower() or "duplicate" in e.lower() for e in result.errors)

    def test_empty_directory_passes(self, tmp_path: Path) -> None:
        dev_cycle = tmp_path / "docs" / "dev-cycle"
        dev_cycle.mkdir(parents=True)
        result = validate_directory(dev_cycle)
        assert result.passed
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_dev_cycle_validate.py::TestArtifactCompleteness tests/test_dev_cycle_validate.py::TestValidateDirectory -v`
Expected: FAIL — missing `validate_directory` import and artifact parsing

- [ ] **Step 3: Implement artifact parsing and directory validation**

Add artifact parsing to `parse_state_file` — extend the `StateFile` dataclass:

```python
@dataclass
class ArtifactRow:
    """A single row from the Artifacts table."""

    phase: str
    status: str
    artifact: str


# Add to StateFile dataclass:
    artifacts: list[ArtifactRow] = field(default_factory=list)
```

Add `_parse_artifacts` helper and artifact table parsing regex:

```python
_ARTIFACT_ROW_RE = re.compile(
    r"^\|\s*(\w+)\s*\|\s*(\w+)\s*\|\s*(.+?)\s*\|$", re.MULTILINE
)


def _parse_artifacts(text: str) -> list[ArtifactRow]:
    """Parse the Artifacts markdown table from state file body."""
    rows: list[ArtifactRow] = []
    for match in _ARTIFACT_ROW_RE.finditer(text):
        phase, status, artifact = match.group(1), match.group(2), match.group(3).strip()
        # Skip table header and separator rows
        if phase in ("Phase", "---") or status in ("Status", "---"):
            continue
        if phase not in VALID_PHASES:
            continue
        rows.append(ArtifactRow(phase=phase, status=status, artifact=artifact))
    return rows
```

Call `_parse_artifacts(text)` in `parse_state_file` and assign to `state.artifacts`.

Add artifact completeness check in `validate_state_file`:

```python
    # Artifact completeness: completed phases must have non-placeholder artifacts
    for row in state.artifacts:
        if row.status == "completed" and row.artifact in ("—", "—", "-", ""):
            errors.append(
                f"Phase '{row.phase}' is completed but has no artifact "
                f"in {path.name}"
            )
```

Add `validate_directory`:

```python
def validate_directory(directory: Path) -> ValidationResult:
    """Validate all state files in a dev-cycle directory.

    Parameters
    ----------
    directory : Path
        Path to the docs/dev-cycle/ directory.

    Returns
    -------
    ValidationResult
        Combined validation result for all files.
    """
    errors: list[str] = []
    slugs: dict[str, list[str]] = {}

    state_files = sorted(directory.glob("*.md"))
    for path in state_files:
        # Validate each file individually
        file_result = validate_state_file(path)
        errors.extend(file_result.errors)

        # Track slugs for collision detection
        try:
            state = parse_state_file(path)
            slugs.setdefault(state.feature, []).append(path.name)
        except ValueError:
            pass  # Already captured in file_result.errors

    # Check for slug collisions
    for slug, filenames in slugs.items():
        if len(filenames) > 1:
            errors.append(
                f"Duplicate feature slug '{slug}' found in files: "
                f"{', '.join(filenames)}"
            )

    return ValidationResult(errors=errors)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_dev_cycle_validate.py -v`
Expected: ALL PASSED (8 prior + 5 new = 13)

- [ ] **Step 5: Commit**

```bash
git add scripts/dev_cycle_validate.py tests/test_dev_cycle_validate.py
git commit -m "feat(dev-cycle): add artifact completeness and slug collision validation"
```

---

## Task 5: State file validator — CLI entry point (TDD)

**Files:**

- Modify: `scripts/dev_cycle_validate.py`
- Modify: `tests/test_dev_cycle_validate.py`

Add a `__main__` CLI so it can be run as `uv run python scripts/dev_cycle_validate.py docs/dev-cycle/`.

- [ ] **Step 1: Write failing test — CLI invocation**

Append to `tests/test_dev_cycle_validate.py`:

```python
import subprocess


class TestCLI:
    """Tests for the command-line interface."""

    def test_cli_reports_valid_directory(self, tmp_path: Path) -> None:
        dev_cycle = tmp_path / "docs" / "dev-cycle"
        dev_cycle.mkdir(parents=True)
        (dev_cycle / "feat-a.md").write_text(
            "---\nschema_version: 1\nfeature: feat-a\n"
            "status: in_progress\ncurrent_phase: brainstorm\n"
            "created: 2026-03-21\nupdated: 2026-03-21\n---\n\n"
            "## Artifacts\n\n## Log\n"
        )
        result = subprocess.run(
            ["uv", "run", "python", "scripts/dev_cycle_validate.py", str(dev_cycle)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "PASS" in result.stdout

    def test_cli_reports_errors(self, tmp_path: Path) -> None:
        dev_cycle = tmp_path / "docs" / "dev-cycle"
        dev_cycle.mkdir(parents=True)
        (dev_cycle / "bad.md").write_text(
            "---\nschema_version: 1\nfeature: bad\n"
            "status: bogus\ncurrent_phase: brainstorm\n"
            "created: 2026-03-21\nupdated: 2026-03-21\n---\n\n"
            "## Artifacts\n\n## Log\n"
        )
        result = subprocess.run(
            ["uv", "run", "python", "scripts/dev_cycle_validate.py", str(dev_cycle)],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "FAIL" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_dev_cycle_validate.py::TestCLI -v`
Expected: FAIL — CLI doesn't produce expected output

- [ ] **Step 3: Add CLI entry point**

Add to the bottom of `scripts/dev_cycle_validate.py`:

```python
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: uv run python scripts/dev_cycle_validate.py <dev-cycle-directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory")
        sys.exit(1)

    result = validate_directory(directory)
    if result.passed:
        state_count = len(list(directory.glob("*.md")))
        print(f"PASS: {state_count} state file(s) validated successfully")
    else:
        print(f"FAIL: {len(result.errors)} error(s) found:")
        for error in result.errors:
            print(f"  - {error}")
        sys.exit(1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_dev_cycle_validate.py -v`
Expected: ALL PASSED (13 prior + 2 new = 15)

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `uv run pytest --tb=short`
Expected: All tests pass (existing + new)

- [ ] **Step 6: Commit**

```bash
git add scripts/dev_cycle_validate.py tests/test_dev_cycle_validate.py
git commit -m "feat(dev-cycle): add CLI entry point for state file validator"
```

---

## Task 6: Create state file schema reference

**Files:**

- Create: `core/skills/dev-cycle/references/state-file-schema.md`

This is a markdown reference file — no code, no tests. It codifies the state file format from the spec so the skill can reference it.

- [ ] **Step 1: Create the directory**

```bash
mkdir -p core/skills/dev-cycle/references
```

- [ ] **Step 2: Write the schema reference**

Create `core/skills/dev-cycle/references/state-file-schema.md` with the following content. This is pulled directly from the spec's State File section (lines 45-116) but formatted as a reference document:

````markdown
# State File Schema (v1)

## Location

`docs/dev-cycle/{feature-slug}.md`

## Template

## \```markdown

schema_version: 1
feature: {feature-slug}
status: not_started
current_phase: brainstorm
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
branch:

---

## Artifacts

| Phase       | Status  | Artifact |
| ----------- | ------- | -------- |
| brainstorm  | pending | —        |
| plan        | pending | —        |
| ceo_review  | pending | —        |
| issues      | pending | —        |
| implement   | pending | —        |
| code_review | pending | —        |
| pr          | pending | —        |

## Issues

| Plan Slice | GitHub Issue | Status |
| ---------- | ------------ | ------ |

## Log

\```

## Field Definitions

- **schema_version:** `1` (integer). Increment on breaking format changes.
- **feature:** Kebab-case slug. Must match filename. On collision with existing slug, suffix with `-2`, `-3`, etc.
- **status:** `not_started` | `in_progress` | `completed` | `abandoned`
- **current_phase:** `brainstorm` | `plan` | `ceo_review` | `issues` | `implement` | `code_review` | `pr`
- **created/updated:** ISO date (YYYY-MM-DD).
- **branch:** Git branch name. Empty until Phase 5. Format: `feat/{feature-slug}`.

## Artifact Status Values

`pending` | `in_progress` | `completed` | `blocked`

Completed phases MUST have a non-empty artifact (not `—`).

## Issues Table

Populated incrementally during Phase 4. Each row maps a plan slice to a GitHub issue URL. On retry, the orchestrator skips slices that already have a recorded issue URL.

## Phase Transition Rules

Forward only, in strict order:

\```text
brainstorm → plan → ceo_review → issues → implement → code_review → pr
\```

### Backwards Transitions (exceptions)

- `implement → plan` — approach is wrong, plan needs rework
- `code_review → plan` — architectural issues found

When a backwards transition occurs:

1. Log the reason
2. Present code handling options to user (keep/revert/new branch)
3. Reset phases from `plan` onward to `pending`
4. Re-enter Phase 2

All other backwards transitions are not supported.

## Validation

Run `uv run python scripts/dev_cycle_validate.py docs/dev-cycle/` to validate all state files.
````

- [ ] **Step 3: Commit**

```bash
git add core/skills/dev-cycle/references/state-file-schema.md
git commit -m "feat(dev-cycle): add state file schema reference"
```

---

## Task 7: Create phase transitions reference

**Files:**

- Create: `core/skills/dev-cycle/references/phase-transitions.md`

This is the glue layer spec — validation rules, handoff context, and failure recovery per transition. Pulled from the spec's Glue Layer and Failure & Recovery sections.

- [ ] **Step 1: Write the phase transitions reference**

Create `core/skills/dev-cycle/references/phase-transitions.md`:

```markdown
# Phase Transitions

Each transition follows: validate artifact → update state → prepare context → invoke next phase.

See the 7-Phase Pipeline table in SKILL.md for delegation targets. This document specifies validation, handoff, and recovery details only.

---

## Brainstorm → Plan

- **Validate:** GitHub issue URL (PRD) is present and accessible via `gh issue view`
- **Handoff:** Pass issue URL to `prd-to-plan`, which reads the PRD and breaks it into vertical slices
- **Record:** Plan file path in artifacts table
- **Failure:** If `gh` is not authenticated or issue is 404, set phase to `blocked`, suggest resolution

## Plan → CEO Review

- **Validate:** Plan file exists at recorded path and is non-empty
- **Handoff:** Pass plan file path to `plan-ceo-review`, recommend HOLD SCOPE mode
- **Record:** Review outcome in log. Plan file on disk reflects revisions (skill edits it in place)
- **Failure:** If plan file is missing, set phase to `blocked`

## CEO Review → Issues

- **Validate:** Plan has been reviewed and user approved. Plan file on disk reflects all revisions.
- **Handoff:** Orchestrator reads the plan's vertical slices and creates one GitHub issue per slice using `gh issue create`. Each issue:
  - References the PRD issue number
  - Includes acceptance criteria from the plan
  - Is created in dependency order so blockers can be referenced by number
- **Record:** Each issue URL is recorded individually in the Issues table as it's created (not batched)
- **Partial completion:** On retry, skip slices that already have a recorded issue URL in the Issues table
- **Failure:** If `gh issue create` fails mid-batch, the Issues table reflects which were created. Retry resumes from next uncreated slice.

## Issues → Implement

- **Validate:** All GitHub issues created and URLs recorded in Issues table
- **Branch creation:**
  - Create `feat/{feature-slug}` from current HEAD
  - If branch already exists and belongs to this feature (per state file): check it out
  - If branch exists but is unrecognized: error, ask user to resolve
- **Handoff:** Load plan file. Dispatch one subagent per issue following `subagent-development` methodology, each invoking `tdd`. Code review between each dispatch.
- **State updates:** After each subagent completes:
  - Log dispatch and result: `"Subagent completed for issue #N: pass/fail"`
  - Log code review result: `"Code review after issue #N: clean/blocking"`
  - Update Issues table status
- **Failure:** Context window exhaustion mid-dispatch is recoverable — Issues table shows which issues are complete. Resume dispatches remaining issues.

## Implement → Code Review

- **Validate:** All implementation issues resolved, tests passing (`uv run pytest` or project test command)
- **Handoff:** Invoke `code-review` against all changed files on the feature branch
- **Gate:** If blocking issues → fix, re-run review. Loop until clean.
- **Failure:** If code review finds architectural issues requiring plan rework, trigger backwards transition to `plan` (see Backwards Transitions below)

## Code Review → PR

- **Validate:** Code review passed with no blocking issues
- **Conflict check:** Before PR creation:
  - Check for conflicts with default branch (via `gh repo view --json defaultBranchRef`)
  - If conflicts exist: rebase or merge default branch, resolve conflicts
  - If a PR already exists for this branch: update it instead of creating duplicate
- **Handoff:** Invoke `commit` for conventional commit, then `github-cli` to open PR
- **Record:** PR URL in artifacts table, set feature `status: completed`
- **Failure:** If PR creation fails (no remote, auth error), set phase to `blocked`

---

## Backwards Transitions

Valid: `implement → plan`, `code_review → plan`

When triggered:

1. Log the reason
2. **Code handling:** Warn user that existing code may conflict. Present options:
   - (a) Keep all existing code on the branch
   - (b) Revert specific commits
   - (c) Create a new branch from the default branch
3. Log the user's choice
4. Reset phases from `plan` onward to `pending`
5. Re-enter Phase 2

---

## Phase Retry

If any phase fails:

1. Log failure reason in state file
2. Set phase status to `blocked` with blocker description
3. Present error and suggest resolution
4. On next invocation, retry from the beginning of the blocked phase

---

## Feature Abandonment

1. Set `status: abandoned`
2. Log reason and timestamp
3. State file remains as audit record
4. Feature branch (if any) is not auto-deleted
5. Cannot be resumed — start a new feature to restart
```

- [ ] **Step 2: Commit**

```bash
git add core/skills/dev-cycle/references/phase-transitions.md
git commit -m "feat(dev-cycle): add phase transitions reference"
```

---

## Task 8: Create the main SKILL.md

**Files:**

- Create: `core/skills/dev-cycle/SKILL.md`

This is the main orchestrator skill file — the prompt instructions that Claude follows.

- [ ] **Step 1: Write SKILL.md**

Create `core/skills/dev-cycle/SKILL.md`:

```markdown
---
name: dev-cycle
description: >
  Orchestrate the full GitHub-issues-driven development lifecycle.
  7-phase pipeline from brainstorm through PR with state tracking
  and cross-conversation resume. Use when user says "dev cycle",
  "development workflow", "full development pipeline", or invokes /dev-cycle.
---

# Dev Cycle Orchestrator

Orchestrate the full development lifecycle: brainstorm → plan → review → issues → implement → code review → PR.

**Disambiguation:** If the user only wants a PRD, route to `/write-a-prd`. If they only want a plan, route to `/prd-to-plan`. This skill is for the full end-to-end lifecycle.

## The 7-Phase Pipeline

Every phase is mandatory. No phase can be skipped.

| #   | Phase           | Delegates To                                           | Gate Condition                    |
| --- | --------------- | ------------------------------------------------------ | --------------------------------- |
| 1   | **Brainstorm**  | `write-a-prd`                                          | Issue URL recorded                |
| 2   | **Plan**        | `prd-to-plan`                                          | Plan file exists at `docs/plans/` |
| 3   | **CEO Review**  | `plan-ceo-review` (recommend HOLD SCOPE)               | Review complete, user approves    |
| 4   | **Issues**      | Orchestrator (plan slices → GitHub issues)             | All issue URLs recorded           |
| 5   | **Implement**   | Orchestrator (`tdd` per issue, `subagent-development`) | All issues resolved, tests pass   |
| 6   | **Code Review** | `code-review`                                          | Clean review                      |
| 7   | **PR**          | `commit` + `github-cli`                                | PR URL recorded                   |

## Re-entry Logic

On every invocation:

### No arguments (`/dev-cycle`)

1. Scan `docs/dev-cycle/` for state files with `status: in_progress`
2. If one → ask: "Resume **{feature}** (`{branch}`)? Currently at **{phase}**."
3. If multiple → list with branch names, ask which to resume
4. If none → ask: "What feature are you working on?" → start Phase 1

### With argument (`/dev-cycle {slug}`)

1. Look for `docs/dev-cycle/{slug}.md`
2. Found → resume at `current_phase`
3. Not found → create state file, start Phase 1

### Slug Collision

When creating a new state file, check `docs/dev-cycle/` for existing slugs. If the slug already exists (abandoned or completed), suffix with `-2`, `-3`, etc.

### Context Loading on Resume

Before continuing, load ALL referenced artifacts:

- **Brainstorm:** `gh issue view` the PRD issue
- **Plan:** Read plan file from disk
- **CEO Review:** Read the plan file (includes review revisions)
- **Issues:** `gh issue view` each implementation issue
- **Implement:** Check git status on feature branch, review closed issues

Present summary: "Resuming **{feature}** at **{phase}**. Here's where we left off: ..."

## Phase Execution

### Phase 1: Brainstorm

Invoke `write-a-prd`. Trust the skill's internal flow (interview → PRD → GitHub issue). Record the issue URL in the state file.

### Phase 2: Plan

Pass the PRD issue URL to `prd-to-plan`. Record the plan file path (at `docs/plans/{feature}.md`).

### Phase 3: CEO Review

Pass plan file path to `plan-ceo-review`. Recommend HOLD SCOPE mode but let the skill's own mode selection (Step 0F) run. Record when review is complete and user approves.

### Phase 4: Issues

**Owned by the orchestrator.** Read the plan's vertical slices. For each slice, create a GitHub issue using `gh issue create` that:

- References the PRD issue
- Includes acceptance criteria from the plan
- Is created in dependency order

Record each issue URL in the Issues table immediately after creation. See [references/phase-transitions.md](references/phase-transitions.md) for partial-completion recovery.

### Phase 5: Implement

**Owned by the orchestrator.** Create feature branch `feat/{feature-slug}` (see branch handling in [references/phase-transitions.md](references/phase-transitions.md)).

Dispatch one subagent per GitHub issue following `subagent-development` methodology:

- Each subagent invokes the `tdd` skill
- Code review runs between each subagent dispatch
- State file is updated after each subagent completes (not batched)

Log per-subagent events:

- `"Subagent started for issue #N: {title}"`
- `"Subagent completed for issue #N: {pass/fail}"`
- `"Code review after issue #N: {clean/blocking issues found}"`

### Phase 6: Code Review

Invoke `code-review` against all changed files on the feature branch. If blocking issues found → fix, re-run. Loop until clean.

If architectural issues requiring plan rework → trigger backwards transition to Phase 2.

### Phase 7: PR

Check for conflicts with default branch first. Invoke `commit` for conventional commit, then `github-cli` to open PR. Record PR URL, set `status: completed`.

## State File

Each feature tracked at `docs/dev-cycle/{feature-slug}.md`. See [references/state-file-schema.md](references/state-file-schema.md) for full format, field definitions, and transition rules.

## Failure & Recovery

See [references/phase-transitions.md](references/phase-transitions.md) for:

- Phase retry logic (blocked → retry on next invocation)
- Backwards transitions (implement/code_review → plan)
- Feature abandonment

## Branch Management

- **Phases 1–4:** Run on current branch (documentation only)
- **Phase 5:** Creates `feat/{feature-slug}` branch
- **Phase 7:** PRs to the default branch (detected via `gh repo view --json defaultBranchRef`)
- **Resume at Phase 5+:** Check out feature branch if not already on it
```

- [ ] **Step 2: Commit**

```bash
git add core/skills/dev-cycle/SKILL.md
git commit -m "feat(dev-cycle): add main orchestrator SKILL.md"
```

---

## Task 9: Register skill in CLAUDE-base.md

**Files:**

- Modify: `core/CLAUDE-base.md:88-89`

- [ ] **Step 1: Add the `/dev-cycle` entry after `/prd-to-issues`**

Insert after the `/prd-to-issues` block (around line 92) in `core/CLAUDE-base.md`:

```markdown
### `/dev-cycle`

**Trigger when:** user says "dev cycle", "development workflow", "full development pipeline", or wants the full end-to-end lifecycle from brainstorm through PR. **Disambiguation:** if user only wants a PRD, route to `/write-a-prd`; only a plan, route to `/prd-to-plan`.
**References:** [.claude/skills/dev-cycle/references/](.claude/skills/dev-cycle/references/) — phase transitions, state file schema.
```

- [ ] **Step 2: Commit**

```bash
git add core/CLAUDE-base.md
git commit -m "feat(dev-cycle): register skill in CLAUDE-base.md"
```

---

## Task 10: Smoke test — build a preset and verify dev-cycle is included

**Files:** No new files. Uses existing tooling.

- [ ] **Step 1: Build the python-api preset and verify dev-cycle skill is included**

```bash
uv run python scripts/build_preset.py python-api
```

Check the output:

```bash
ls dist/python-api/.claude/skills/dev-cycle/
```

Expected: `SKILL.md` and `references/` directory with two files.

- [ ] **Step 2: Run smoke test on the built preset**

```bash
uv run python scripts/smoke_test.py python-api
```

Expected: PASS (the new skill references and docs are consistent).

- [ ] **Step 3: Run the full test suite**

```bash
uv run pytest --tb=short
```

Expected: All tests pass.

- [ ] **Step 4: Run the state file validator on an empty directory to verify CLI works**

```bash
mkdir -p docs/dev-cycle
uv run python scripts/dev_cycle_validate.py docs/dev-cycle/
```

Expected: `PASS: 0 state file(s) validated successfully`

- [ ] **Step 5: Clean up and commit if any fixes were needed**

If smoke test or full test suite revealed issues, fix them and commit:

```bash
git add -A
git commit -m "fix(dev-cycle): address smoke test findings"
```

If everything passed cleanly, no commit needed for this task.

---

## Summary

| Task | What                             | Type       | Files |
| ---- | -------------------------------- | ---------- | ----- |
| 1    | Fix prd-to-plan output path      | Prereq fix | 1     |
| 2    | State file parser (TDD)          | Python     | 2     |
| 3    | Field validation (TDD)           | Python     | 2     |
| 4    | Artifact + slug validation (TDD) | Python     | 2     |
| 5    | CLI entry point (TDD)            | Python     | 2     |
| 6    | State file schema reference      | Markdown   | 1     |
| 7    | Phase transitions reference      | Markdown   | 1     |
| 8    | Main SKILL.md                    | Markdown   | 1     |
| 9    | Register in CLAUDE-base.md       | Markdown   | 1     |
| 10   | Smoke test integration           | Validation | 0     |
