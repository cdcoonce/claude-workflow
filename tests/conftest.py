"""Shared test fixtures for the template system."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create a minimal template repo structure for testing."""
    core = tmp_path / "core"
    core.mkdir()

    skills = core / "skills"
    skills.mkdir()
    for skill_name in ["commit", "code-review", "tdd"]:
        skill_dir = skills / skill_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(f"# {skill_name} skill")

    docs = core / "docs"
    docs.mkdir()
    (docs / "tdd.md").write_text("# TDD methodology")
    (docs / "root-cause-tracing.md").write_text("# Root cause tracing")

    hooks = core / "hooks"
    hooks.mkdir()
    (hooks / "protect-files.py").write_text("# protect files hook")

    (core / "CLAUDE-base.md").write_text("# Base CLAUDE\n\n## Methodology\n")
    (core / "settings-base.json").write_text(json.dumps({
        "hooks": {
            "PreToolUse": [{"matcher": "Edit|Write", "hooks": [
                {"type": "command", "command": "python .claude/hooks/protect-files.py"}
            ]}]
        }
    }))

    presets = tmp_path / "presets"
    presets.mkdir()

    preset = presets / "python-api"
    preset.mkdir()
    (preset / "manifest.json").write_text(json.dumps({
        "name": "python-api",
        "description": "Python backend services",
        "core": {"skills": "all", "docs": "all", "hooks": ["protect-files.py"]},
        "exclude": [],
        "preset_skills": ["deploy"],
        "preset_hooks": ["post-edit-lint.py"],
    }))
    (preset / "CLAUDE-preset.md").write_text("\n## Testing\n\n- Run tests: `uv run pytest`\n")
    (preset / "settings-preset.json").write_text(json.dumps({
        "hooks": {
            "PostToolUse": [{"matcher": "Edit|Write", "hooks": []}]
        }
    }))

    preset_skills = preset / "skills"
    preset_skills.mkdir()
    deploy_skill = preset_skills / "deploy"
    deploy_skill.mkdir()
    (deploy_skill / "SKILL.md").write_text("# deploy skill")

    preset_hooks = preset / "hooks"
    preset_hooks.mkdir()
    (preset_hooks / "post-edit-lint.py").write_text("# lint hook")

    (tmp_path / "dist").mkdir()

    return tmp_path


@pytest.fixture
def bad_manifest_repo(tmp_repo: Path) -> Path:
    """Create a repo with an invalid manifest (references nonexistent skill)."""
    preset = tmp_repo / "presets" / "broken"
    preset.mkdir()
    (preset / "manifest.json").write_text(json.dumps({
        "name": "broken",
        "description": "Broken preset for testing",
        "core": {"skills": "all", "docs": "all", "hooks": ["protect-files.py"]},
        "exclude": [],
        "preset_skills": ["nonexistent-skill"],
        "preset_hooks": ["post-edit-lint.py"],
    }))
    (preset / "CLAUDE-preset.md").write_text("\n## Broken\n")
    (preset / "settings-preset.json").write_text(json.dumps({"hooks": {}}))

    preset_hooks = preset / "hooks"
    preset_hooks.mkdir()
    (preset_hooks / "post-edit-lint.py").write_text("# lint hook")

    return tmp_repo
