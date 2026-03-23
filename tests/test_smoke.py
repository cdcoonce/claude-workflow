"""Tests for smoke_test.py — validates internal consistency of built presets (D23)."""

import json
from pathlib import Path

import pytest

from scripts.build_preset import build_preset
from scripts.smoke_test import smoke_test, SmokeTestResult


class TestSmokeTest:
    """Smoke test catches internal inconsistencies in built output."""

    def test_valid_build_passes_smoke_test(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"
        result = smoke_test(dist)
        assert result.passed is True
        assert len(result.errors) == 0

    def test_missing_skill_directory_fails(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"

        # Add a skill reference to CLAUDE.md without the actual skill
        claude_md = dist / "CLAUDE.md"
        content = claude_md.read_text()
        content += "\n### `/fake-skill`\n\n**Trigger when:** never.\n"
        claude_md.write_text(content)

        result = smoke_test(dist)
        assert result.passed is False
        assert any("fake-skill" in e for e in result.errors)

    def test_missing_hook_file_fails(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"

        # Remove the specific hook referenced in settings.json
        (dist / ".claude" / "hooks" / "protect-files.py").unlink()

        result = smoke_test(dist)
        assert result.passed is False
        assert any("protect-files.py" in e for e in result.errors)

    def test_missing_doc_reference_fails(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"

        # Add a doc reference to CLAUDE.md without the actual doc
        claude_md = dist / "CLAUDE.md"
        content = claude_md.read_text()
        content += "\nFull process: [.claude/docs/nonexistent.md](.claude/docs/nonexistent.md)\n"
        claude_md.write_text(content)

        result = smoke_test(dist)
        assert result.passed is False
        assert any("nonexistent.md" in e for e in result.errors)

    def test_valid_intra_skill_link_passes(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"

        # Add a skill with a valid reference link
        skill_dir = dist / ".claude" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "guide.md").write_text("# Guide\n")
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: test\n---\n\n"
            "See [guide](references/guide.md) for details.\n"
        )

        result = smoke_test(dist)
        assert result.passed is True

    def test_broken_intra_skill_link_fails(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"

        # Add a skill with a broken reference link
        skill_dir = dist / ".claude" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: test\n---\n\n"
            "See [missing](references/nonexistent.md) for details.\n"
        )

        result = smoke_test(dist)
        assert result.passed is False
        assert any("test-skill/SKILL.md" in e and "nonexistent.md" in e for e in result.errors)


class TestSmokeAgents:
    """Smoke test validates agent integrity."""

    def test_valid_agents_pass(self, tmp_repo: Path) -> None:
        """Agents with valid frontmatter pass smoke test."""
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"
        result = smoke_test(dist)
        assert result.passed

    def test_missing_frontmatter_fails(self, tmp_repo: Path) -> None:
        """Agent without frontmatter fails smoke test."""
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"
        agent_md = dist / ".claude" / "agents" / "tdd-implementer" / "AGENT.md"
        agent_md.write_text("# No frontmatter here\n")
        result = smoke_test(dist)
        assert not result.passed
        assert any("frontmatter" in e.lower() or "required" in e.lower() for e in result.errors)

    def test_invalid_role_fails(self, tmp_repo: Path) -> None:
        """Agent with invalid role fails smoke test."""
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"
        agent_md = dist / ".claude" / "agents" / "tdd-implementer" / "AGENT.md"
        agent_md.write_text("---\nname: tdd-implementer\ndescription: test\nrole: invalid\n---\n")
        result = smoke_test(dist)
        assert not result.passed
        assert any("role" in e for e in result.errors)

    def test_name_mismatch_fails(self, tmp_repo: Path) -> None:
        """Agent whose name doesn't match directory fails smoke test."""
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"
        agent_md = dist / ".claude" / "agents" / "tdd-implementer" / "AGENT.md"
        agent_md.write_text("---\nname: wrong-name\ndescription: test\nrole: implementer\n---\n")
        result = smoke_test(dist)
        assert not result.passed
        assert any("name" in e and "match" in e for e in result.errors)

    def test_missing_skill_reference_fails(self, tmp_repo: Path) -> None:
        """Agent referencing nonexistent skill in skills.add fails smoke test."""
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"
        agent_md = dist / ".claude" / "agents" / "tdd-implementer" / "AGENT.md"
        agent_md.write_text(
            "---\nname: tdd-implementer\ndescription: test\nrole: implementer\n"
            "skills:\n  add: [nonexistent-skill]\n---\n"
        )
        result = smoke_test(dist)
        assert not result.passed
        assert any("nonexistent-skill" in e for e in result.errors)
