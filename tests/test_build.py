"""Tests for build_preset.py — verifies correct assembly of core + preset delta."""

from pathlib import Path

from scripts.build_preset import build_preset


class TestBuildPreset:
    """Build produces correct output structure."""

    def test_build_creates_dist_directory(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api"
        assert dist.exists()

    def test_build_copies_core_skills(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api" / ".claude" / "skills"
        assert (dist / "commit" / "SKILL.md").exists()
        assert (dist / "code-review" / "SKILL.md").exists()
        assert (dist / "tdd" / "SKILL.md").exists()

    def test_build_copies_core_docs(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api" / ".claude" / "docs"
        assert (dist / "tdd.md").exists()
        assert (dist / "root-cause-tracing.md").exists()

    def test_build_copies_core_hooks(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api" / ".claude" / "hooks"
        assert (dist / "protect-files.py").exists()

    def test_build_copies_preset_skills(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api" / ".claude" / "skills"
        assert (dist / "deploy" / "SKILL.md").exists()

    def test_build_copies_preset_hooks(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api" / ".claude" / "hooks"
        assert (dist / "post-edit-lint.py").exists()

    def test_build_merges_settings(self, tmp_repo: Path) -> None:
        import json

        build_preset("python-api", repo_root=tmp_repo)
        settings_path = tmp_repo / "dist" / "python-api" / ".claude" / "settings.json"
        settings = json.loads(settings_path.read_text())
        assert "PreToolUse" in settings["hooks"]
        assert "PostToolUse" in settings["hooks"]

    def test_build_concatenates_claude_md(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        claude_md = tmp_repo / "dist" / "python-api" / "CLAUDE.md"
        content = claude_md.read_text()
        assert "## Methodology" in content
        assert "## Testing" in content

    def test_build_writes_template_version(self, tmp_repo: Path) -> None:
        build_preset("python-api", repo_root=tmp_repo)
        version_file = tmp_repo / "dist" / "python-api" / ".claude" / ".template-version"
        assert version_file.exists()
        content = version_file.read_text().strip()
        assert len(content) > 0


class TestBuildExclusions:
    """Exclusions remove core items from output."""

    def test_exclude_removes_core_skill(self, tmp_repo: Path) -> None:
        import json

        manifest_path = tmp_repo / "presets" / "python-api" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["exclude"] = ["skills/tdd"]
        manifest_path.write_text(json.dumps(manifest))

        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api" / ".claude" / "skills"
        assert not (dist / "tdd").exists()
        assert (dist / "commit").exists()


class TestBuildOverrides:
    """Preset skills with same name as core skills override them (D17)."""

    def test_preset_skill_overrides_core(self, tmp_repo: Path) -> None:
        override = tmp_repo / "presets" / "python-api" / "skills" / "tdd"
        override.mkdir()
        (override / "SKILL.md").write_text("# OVERRIDDEN tdd skill")

        manifest_path = tmp_repo / "presets" / "python-api" / "manifest.json"
        import json
        manifest = json.loads(manifest_path.read_text())
        manifest["preset_skills"].append("tdd")
        manifest_path.write_text(json.dumps(manifest))

        build_preset("python-api", repo_root=tmp_repo)
        dist = tmp_repo / "dist" / "python-api" / ".claude" / "skills" / "tdd"
        content = (dist / "SKILL.md").read_text()
        assert "OVERRIDDEN" in content


class TestSettingsMerge:
    """Settings merge handles edge cases correctly."""

    def test_duplicate_hook_type_appends(self, tmp_repo: Path) -> None:
        import json

        preset_settings = tmp_repo / "presets" / "python-api" / "settings-preset.json"
        preset_settings.write_text(json.dumps({
            "hooks": {
                "PreToolUse": [{"matcher": "Bash", "hooks": []}],
                "PostToolUse": [{"matcher": "Edit|Write", "hooks": []}],
            }
        }))

        build_preset("python-api", repo_root=tmp_repo)
        settings_path = tmp_repo / "dist" / "python-api" / ".claude" / "settings.json"
        settings = json.loads(settings_path.read_text())

        assert len(settings["hooks"]["PreToolUse"]) == 2
        assert settings["hooks"]["PreToolUse"][0]["matcher"] == "Edit|Write"
        assert settings["hooks"]["PreToolUse"][1]["matcher"] == "Bash"
