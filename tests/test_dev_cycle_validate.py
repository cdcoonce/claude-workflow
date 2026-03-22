"""Tests for dev_cycle_validate — state file parser and validator."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.dev_cycle_validate import StateFile, parse_state_file, ValidationResult, validate_state_file


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
