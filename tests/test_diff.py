"""Tests for diff_preset.py — verifies diff accuracy between project and preset (D14, D22)."""

import json
import shutil
from pathlib import Path

from scripts.build_preset import build_preset
from scripts.diff_preset import diff_preset, DiffResult


def _build_and_copy_to_project(tmp_repo: Path) -> Path:
    """Build a preset, then copy output to a separate 'project' directory.

    This avoids the rebuild-destroys-comparison-target problem:
    diff_preset internally calls build_preset which writes to dist/,
    so the "project" must live elsewhere.
    """
    build_preset("python-api", repo_root=tmp_repo)
    project = tmp_repo / "fake_project"
    shutil.copytree(tmp_repo / "dist" / "python-api", project)
    return project


class TestDiffPreset:
    """Diff correctly identifies changes between a project's .claude/ and a built preset."""

    def test_identical_project_has_no_diff(self, tmp_repo: Path) -> None:
        project = _build_and_copy_to_project(tmp_repo)

        result = diff_preset(
            project_claude_dir=project / ".claude",
            project_claude_md=project / "CLAUDE.md",
            preset_name="python-api",
            repo_root=tmp_repo,
        )
        assert result.has_changes is False
        assert len(result.modified_files) == 0
        assert len(result.added_files) == 0
        assert len(result.removed_files) == 0

    def test_modified_skill_detected(self, tmp_repo: Path) -> None:
        project = _build_and_copy_to_project(tmp_repo)

        skill_md = project / ".claude" / "skills" / "commit" / "SKILL.md"
        skill_md.write_text("# MODIFIED commit skill")

        result = diff_preset(
            project_claude_dir=project / ".claude",
            project_claude_md=project / "CLAUDE.md",
            preset_name="python-api",
            repo_root=tmp_repo,
        )
        assert result.has_changes is True
        assert any("commit/SKILL.md" in f for f in result.modified_files)

    def test_added_file_detected(self, tmp_repo: Path) -> None:
        project = _build_and_copy_to_project(tmp_repo)

        new_file = project / ".claude" / "skills" / "commit" / "NEW.md"
        new_file.write_text("# New file")

        result = diff_preset(
            project_claude_dir=project / ".claude",
            project_claude_md=project / "CLAUDE.md",
            preset_name="python-api",
            repo_root=tmp_repo,
        )
        assert result.has_changes is True
        assert any("NEW.md" in f for f in result.added_files)

    def test_removed_file_detected(self, tmp_repo: Path) -> None:
        project = _build_and_copy_to_project(tmp_repo)

        (project / ".claude" / "skills" / "commit" / "SKILL.md").unlink()

        result = diff_preset(
            project_claude_dir=project / ".claude",
            project_claude_md=project / "CLAUDE.md",
            preset_name="python-api",
            repo_root=tmp_repo,
        )
        assert result.has_changes is True
        assert any("commit/SKILL.md" in f for f in result.removed_files)

    def test_modified_claude_md_detected(self, tmp_repo: Path) -> None:
        project = _build_and_copy_to_project(tmp_repo)

        (project / "CLAUDE.md").write_text("# Completely different")

        result = diff_preset(
            project_claude_dir=project / ".claude",
            project_claude_md=project / "CLAUDE.md",
            preset_name="python-api",
            repo_root=tmp_repo,
        )
        assert result.has_changes is True
        assert "CLAUDE.md" in result.modified_files

    def test_reads_template_version(self, tmp_repo: Path) -> None:
        project = _build_and_copy_to_project(tmp_repo)

        result = diff_preset(
            project_claude_dir=project / ".claude",
            project_claude_md=project / "CLAUDE.md",
            preset_name="python-api",
            repo_root=tmp_repo,
        )
        assert result.template_version is not None
