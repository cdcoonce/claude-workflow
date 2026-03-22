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
