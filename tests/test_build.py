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
        assert (dist / "daa-code-review" / "SKILL.md").exists()
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


class TestBuildAgents:
    """Build copies core agents to output."""

    def test_build_copies_core_agents(self, tmp_repo: Path) -> None:
        """Core agents are copied when manifest has core.agents: 'all'."""
        import json
        manifest_path = tmp_repo / "presets" / "python-api" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["core"]["agents"] = "all"
        manifest_path.write_text(json.dumps(manifest))

        build_preset("python-api", repo_root=tmp_repo)
        agents_dir = tmp_repo / "dist" / "python-api" / ".claude" / "agents"
        assert (agents_dir / "tdd-implementer" / "AGENT.md").exists()
        assert (agents_dir / "code-reviewer" / "AGENT.md").exists()

    def test_build_copies_core_agents_default(self, tmp_repo: Path) -> None:
        """Core agents default to 'all' when core.agents is omitted."""
        build_preset("python-api", repo_root=tmp_repo)
        agents_dir = tmp_repo / "dist" / "python-api" / ".claude" / "agents"
        assert (agents_dir / "tdd-implementer" / "AGENT.md").exists()
        assert (agents_dir / "code-reviewer" / "AGENT.md").exists()

    def test_build_copies_specific_core_agents(self, tmp_repo: Path) -> None:
        """Only listed core agents are copied when manifest lists specific names."""
        import json
        manifest_path = tmp_repo / "presets" / "python-api" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["core"]["agents"] = ["tdd-implementer"]
        manifest_path.write_text(json.dumps(manifest))

        build_preset("python-api", repo_root=tmp_repo)
        agents_dir = tmp_repo / "dist" / "python-api" / ".claude" / "agents"
        assert (agents_dir / "tdd-implementer" / "AGENT.md").exists()
        assert not (agents_dir / "code-reviewer").exists()

    def test_build_copies_role_defaults(self, tmp_repo: Path) -> None:
        """agent-role-defaults.json is copied to .claude/."""
        build_preset("python-api", repo_root=tmp_repo)
        defaults_path = tmp_repo / "dist" / "python-api" / ".claude" / "agent-role-defaults.json"
        assert defaults_path.exists()
        import json
        data = json.loads(defaults_path.read_text())
        assert "implementer" in data
        assert "reviewer" in data

    def test_build_skips_agents_when_dir_missing(self, tmp_repo: Path) -> None:
        """Gracefully skip core agent copy when core/agents/ doesn't exist."""
        import shutil
        shutil.rmtree(tmp_repo / "core" / "agents")
        build_preset("python-api", repo_root=tmp_repo)
        agents_dir = tmp_repo / "dist" / "python-api" / ".claude" / "agents"
        assert not agents_dir.exists()

    def test_build_skips_role_defaults_when_missing(self, tmp_repo: Path) -> None:
        """Gracefully skip role defaults copy when file doesn't exist."""
        (tmp_repo / "core" / "agent-role-defaults.json").unlink()
        build_preset("python-api", repo_root=tmp_repo)
        defaults_path = tmp_repo / "dist" / "python-api" / ".claude" / "agent-role-defaults.json"
        assert not defaults_path.exists()

    def test_exclude_removes_agent(self, tmp_repo: Path) -> None:
        """Exclusion with agents/<name> format removes agent from output."""
        import json
        manifest_path = tmp_repo / "presets" / "python-api" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["exclude"] = ["agents/tdd-implementer"]
        manifest_path.write_text(json.dumps(manifest))

        build_preset("python-api", repo_root=tmp_repo)
        agents_dir = tmp_repo / "dist" / "python-api" / ".claude" / "agents"
        assert not (agents_dir / "tdd-implementer").exists()
        assert (agents_dir / "code-reviewer" / "AGENT.md").exists()

    def test_exclusion_path_containment(self, tmp_repo: Path) -> None:
        """Exclusion paths that escape claude_dir are rejected."""
        import json
        manifest_path = tmp_repo / "presets" / "python-api" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["exclude"] = ["../../etc/passwd"]
        manifest_path.write_text(json.dumps(manifest))

        build_preset("python-api", repo_root=tmp_repo)
        # Should not crash and should not delete anything outside claude_dir
        assert (tmp_repo / "dist" / "python-api" / ".claude").exists()


class TestBuildPresetAgents:
    """Preset agents are assembled into build output."""

    def test_build_copies_preset_agents(self, tmp_repo: Path) -> None:
        """Preset agents listed in manifest are copied to output."""
        import json
        manifest_path = tmp_repo / "presets" / "python-api" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["preset_agents"] = ["api-builder"]
        manifest_path.write_text(json.dumps(manifest))

        build_preset("python-api", repo_root=tmp_repo)
        agents_dir = tmp_repo / "dist" / "python-api" / ".claude" / "agents"
        assert (agents_dir / "api-builder" / "AGENT.md").exists()

    def test_preset_agent_overrides_core(self, tmp_repo: Path) -> None:
        """Preset agent with same name as core agent replaces it."""
        import json
        # Create preset agent that collides with core agent
        override_dir = tmp_repo / "presets" / "python-api" / "agents" / "tdd-implementer"
        override_dir.mkdir(parents=True, exist_ok=True)
        (override_dir / "AGENT.md").write_text(
            "---\nname: tdd-implementer\nrole: implementer\n---\n\n# OVERRIDDEN\n"
        )

        manifest_path = tmp_repo / "presets" / "python-api" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["preset_agents"] = ["tdd-implementer"]
        manifest_path.write_text(json.dumps(manifest))

        build_preset("python-api", repo_root=tmp_repo)
        agent_md = tmp_repo / "dist" / "python-api" / ".claude" / "agents" / "tdd-implementer" / "AGENT.md"
        assert "OVERRIDDEN" in agent_md.read_text()

    def test_preset_agents_defaults_empty(self, tmp_repo: Path) -> None:
        """preset_agents defaults to [] when omitted — no preset agents copied."""
        build_preset("python-api", repo_root=tmp_repo)
        agents_dir = tmp_repo / "dist" / "python-api" / ".claude" / "agents"
        # Only core agents should exist
        assert (agents_dir / "tdd-implementer").exists()
        assert (agents_dir / "code-reviewer").exists()
        assert not (agents_dir / "api-builder").exists()

    def test_validation_fails_missing_preset_agent(self, tmp_repo: Path) -> None:
        """Manifest validation fails if preset_agents references nonexistent agent."""
        import json
        import pytest
        from scripts.build_preset import BuildValidationError

        manifest_path = tmp_repo / "presets" / "python-api" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["preset_agents"] = ["nonexistent-agent"]
        manifest_path.write_text(json.dumps(manifest))

        with pytest.raises(BuildValidationError, match="Preset agent not found"):
            build_preset("python-api", repo_root=tmp_repo)

    def test_validation_catches_agent_in_both_preset_and_exclude(self, tmp_repo: Path) -> None:
        """Validation fails when agent is in both preset_agents and exclude."""
        import json
        import pytest
        from scripts.build_preset import BuildValidationError

        manifest_path = tmp_repo / "presets" / "python-api" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["preset_agents"] = ["api-builder"]
        manifest["exclude"] = ["agents/api-builder"]
        manifest_path.write_text(json.dumps(manifest))

        with pytest.raises(BuildValidationError, match="preset_agents and exclude"):
            build_preset("python-api", repo_root=tmp_repo)


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
