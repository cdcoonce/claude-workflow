# Claude Template System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the claude-workflow repo from a working project into a template system with a `core/` shared library, 5 named presets, and Python build/diff/smoke-test tooling managed by `uv`.

**Architecture:** Core + delta preset architecture. Shared skills, docs, and hooks live in `core/`. Each preset directory holds only its delta (preset-specific skills, hooks, CLAUDE-preset.md, settings-preset.json, manifest.json). A Python build script assembles `core/` + preset delta into a ready-to-copy output in `dist/`. A diff script enables manual sync of improvements back from projects.

**Tech Stack:** Python 3.12+, uv, pytest

**Decisions Reference:** This plan implements all 26 decisions from the grill session. Key decisions are referenced as (D#) throughout.

---

## File Structure

```
claude-workflow/
├── CLAUDE.md                          ← Template system docs (D6)
├── COMPATIBILITY.md                   ← Claude Code feature assumptions (D21)
├── .gitignore                         ← dist/, __pycache__, .DS_Store
├── pyproject.toml                     ← uv project config (D18)
├── core/
│   ├── CLAUDE-base.md                 ← Universal methodology, style, skill triggers (D12)
│   ├── settings-base.json             ← Universal hook config: protect-files (D13)
│   ├── skills/                        ← 17 universal skills (D7)
│   │   ├── commit/
│   │   ├── daa-code-review/
│   │   ├── github-cli/
│   │   ├── tdd/
│   │   ├── triage-issue/
│   │   ├── project-context/
│   │   ├── grill-me/
│   │   ├── plan-ceo-review/
│   │   ├── write-a-prd/
│   │   ├── prd-to-plan/
│   │   ├── prd-to-issues/
│   │   ├── request-refactor-plan/
│   │   ├── improve-codebase-architecture/
│   │   ├── design-an-interface/
│   │   ├── readme-generator/
│   │   ├── git-guardrails-claude-code/
│   │   └── write-a-skill/
│   ├── docs/                          ← 4 methodology docs (D8)
│   │   ├── tdd.md
│   │   ├── root-cause-tracing.md
│   │   ├── subagent-development.md
│   │   └── parallel-agents.md
│   └── hooks/
│       └── protect-files.py           ← Universal file protection hook (D9)
├── presets/
│   ├── python-api/
│   │   ├── manifest.json
│   │   ├── CLAUDE-preset.md
│   │   ├── settings-preset.json
│   │   ├── skills/
│   │   │   ├── deploy/
│   │   │   └── setup-pre-commit/
│   │   └── hooks/
│   │       └── post-edit-lint.py      ← Ruff only
│   ├── data-pipeline/
│   │   ├── manifest.json
│   │   ├── CLAUDE-preset.md
│   │   ├── settings-preset.json
│   │   └── hooks/
│   │       └── post-edit-lint.py      ← Ruff only
│   ├── full-stack/
│   │   ├── manifest.json
│   │   ├── CLAUDE-preset.md
│   │   ├── settings-preset.json
│   │   ├── skills/
│   │   │   └── setup-pre-commit/
│   │   └── hooks/
│   │       └── post-edit-lint.py      ← Ruff + Prettier + ESLint + Stylelint
│   ├── claude-tooling/
│   │   ├── manifest.json
│   │   ├── CLAUDE-preset.md
│   │   ├── settings-preset.json
│   │   └── hooks/
│   │       └── post-edit-lint.py      ← Ruff + Prettier (for markdown/json)
│   └── analysis/
│       ├── manifest.json
│       ├── CLAUDE-preset.md
│       ├── settings-preset.json
│       └── hooks/
│           └── post-edit-lint.py      ← Ruff only
├── scripts/
│   ├── __init__.py
│   ├── build_preset.py                ← Assembles core + delta → dist/ (D10, D15, D16)
│   ├── diff_preset.py                 ← Diffs project .claude/ against built preset (D14)
│   └── smoke_test.py                  ← Validates internal consistency of built output (D23)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    ← Shared fixtures: temp dirs, sample core/preset structures
│   ├── test_build.py                  ← Build correctness (D22)
│   ├── test_validation.py             ← Fail-fast on bad manifests (D22)
│   ├── test_diff.py                   ← Diff accuracy (D22)
│   └── test_smoke.py                  ← Smoke test logic (D23)
└── dist/                              ← Build output, gitignored (D15)
```

---

### Task 1: Project Initialization

**Files:**

- Create: `pyproject.toml`
- Create: `.gitignore`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "claude-workflow"
version = "0.1.0"
description = "Template system for Claude Code configurations"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create .gitignore**

```
dist/
__pycache__/
*.pyc
.DS_Store
*.egg-info/
.pytest_cache/
.ruff_cache/
```

- [ ] **Step 3: Initialize uv and verify**

Run: `uv sync`
Expected: Lock file created, virtual environment set up.

- [ ] **Step 4: Verify pytest runs (empty suite)**

Run: `uv run pytest -v`
Expected: "no tests ran" (0 collected), exit code 5 (no tests). This confirms the toolchain works.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore uv.lock
git commit -m "chore: initialize uv project with pytest config"
```

---

### Task 2: Create Core Directory Structure

Move the 17 universal skills, 4 methodology docs, and the universal hook from `.claude/` into `core/`.

**Files:**

- Create: `core/` directory tree
- Move from: `.claude/skills/` (17 skills), `.claude/docs/` (4 docs), `.claude/hooks/protect-files.py`

- [ ] **Step 1: Create core directory skeleton**

```bash
mkdir -p core/skills core/docs core/hooks
```

- [ ] **Step 2: Move universal skills to core/skills/**

Move these 17 skill directories from `.claude/skills/` to `core/skills/`:

- `commit`, `daa-code-review`, `github-cli`, `tdd`, `triage-issue`, `project-context`, `grill-me`, `plan-ceo-review`, `write-a-prd`, `prd-to-plan`, `prd-to-issues`, `request-refactor-plan`, `improve-codebase-architecture`, `design-an-interface`, `readme-generator`, `git-guardrails-claude-code`, `write-a-skill`

```bash
for skill in commit daa-code-review github-cli tdd triage-issue project-context grill-me plan-ceo-review write-a-prd prd-to-plan prd-to-issues request-refactor-plan improve-codebase-architecture design-an-interface readme-generator git-guardrails-claude-code write-a-skill; do
  mv .claude/skills/$skill core/skills/
done
```

- [ ] **Step 3: Move methodology docs to core/docs/**

```bash
mv .claude/docs/tdd.md core/docs/
mv .claude/docs/root-cause-tracing.md core/docs/
mv .claude/docs/subagent-development.md core/docs/
mv .claude/docs/parallel-agents.md core/docs/
```

- [ ] **Step 4: Move universal hook to core/hooks/**

```bash
mv .claude/hooks/protect-files.py core/hooks/
```

- [ ] **Step 5: Move preset-specific skills to a staging area**

The remaining skills in `.claude/skills/` are preset-specific. Move them temporarily:

```bash
mkdir -p _staging/skills
mv .claude/skills/deploy _staging/skills/
mv .claude/skills/setup-pre-commit _staging/skills/
```

Note: `scaffold-exercises` and `edit-article` are intentionally dropped — they were not assigned to any preset (D7). Delete them explicitly:

```bash
rm -rf .claude/skills/scaffold-exercises
rm -rf .claude/skills/edit-article
```

- [ ] **Step 6: Stage the remaining .claude/ artifacts for cleanup**

Keep `.claude/hooks/post-edit-lint.py` — it'll be the basis for preset-specific hooks.
Remove `.claude/skills/README.md` (no longer needed — presets define their own skill sets).
Remove `.claude/docs/project.md` (empty, will be regenerated per-project via skill).
Remove `.claude/settings.json` (will be replaced by core/preset merge system).

```bash
mv .claude/hooks/post-edit-lint.py _staging/
rm .claude/skills/README.md
rm .claude/docs/project.md
rm .claude/settings.json
```

- [ ] **Step 7: Verify core structure**

Run: `find core -type f | sort`
Expected: All 17 skill directories with their contents, 4 docs, 1 hook.

- [ ] **Step 8: Commit**

```bash
git add core/ _staging/
git rm -r --cached .claude/skills/ .claude/docs/ .claude/hooks/ .claude/settings.json
git commit -m "refactor: move universal skills, docs, hooks into core/"
```

---

### Task 3: Create CLAUDE-base.md

Extract the universal parts of the current `CLAUDE.md` into `core/CLAUDE-base.md`. This becomes the shared foundation concatenated into every preset's final `CLAUDE.md` (D12).

**Files:**

- Create: `core/CLAUDE-base.md`

- [ ] **Step 1: Write core/CLAUDE-base.md**

```markdown
# Development Standards

This file is auto-loaded every conversation. It defines how Claude should work in this project.

## Methodology

### TDD — Test-Driven Development

Write the test first. Watch it fail. Write minimal code to pass. No production code without a failing test.
Full process: [.claude/docs/tdd.md](.claude/docs/tdd.md)

### Root Cause Tracing

Never fix at the symptom. Trace backward through the call chain to the original trigger, then fix at the source.
Full process: [.claude/docs/root-cause-tracing.md](.claude/docs/root-cause-tracing.md)

### Subagent-Driven Development

When executing a plan with multiple independent tasks, dispatch a fresh subagent per task with code review between each.
Full process: [.claude/docs/subagent-development.md](.claude/docs/subagent-development.md)

### Parallel Agent Dispatch

When 3+ unrelated failures need investigation, dispatch one agent per independent problem domain concurrently.
Full process: [.claude/docs/parallel-agents.md](.claude/docs/parallel-agents.md)

## Planning

Write implementation plans to `docs/plans/{file_name}.md` before starting non-trivial work. Once a plan has been fully implemented, move it to `docs/archive/`.

## Code Style

- Descriptive variable names (`private_key_bytes` not `pkb`)
- SOLID, DRY, YAGNI — simplicity over complexity
- Type hints on all function signatures
- Numpy-style docstrings for public functions

## Skills

Skills live in `.claude/skills/`. Each `SKILL.md` defines an invocable skill with trigger conditions.

### `/daa-code-review`

**Trigger when:** user asks for a "code review", "quality check", pre-commit review, or wants code analyzed for issues.
**Output:** Save markdown report to `docs/code_reviews/{YYYY-MM-DD}_{file_name}.md`.

### `/github-cli`

**Trigger when:** user needs to interact with GitHub — issues, pull requests, PR reviews, CI/CD pipelines, or pushing changes.

### `/commit`

**Trigger when:** user asks to commit, make a commit, save work, or when Claude needs to commit changes after completing a task.

### `/readme-generator`

**Trigger when:** user asks to create, generate, update, or improve a README, or says "document this project".
**References:** [.claude/skills/readme-generator/references/](.claude/skills/readme-generator/references/) — analysis methodology, mermaid guidelines, badge reference.

### `/grill-me`

**Trigger when:** user wants to stress-test a plan, get grilled on their design, or mentions "grill me".

### `/plan-ceo-review`

**Trigger when:** user asks for a plan review, CEO review, mega review, or wants a plan challenged/stress-tested before implementation.
**References:** [.claude/skills/plan-ceo-review/references/](.claude/skills/plan-ceo-review/references/) — review sections, required outputs.

### `/project-context`

**Trigger when:** user asks to create, update, or refresh project context, says "update project.md", or when onboarding Claude to a new repo.
**Output:** `.claude/docs/project.md`

### `/tdd`

**Trigger when:** user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development.

### `/triage-issue`

**Trigger when:** user reports a bug, wants to file an issue, mentions "triage", or wants to investigate and plan a fix for a problem.

### `/write-a-prd`

**Trigger when:** user wants to write a PRD, create a product requirements document, or plan a new feature.

### `/prd-to-plan`

**Trigger when:** user wants to break down a PRD, create an implementation plan, plan phases from a PRD, or mentions "tracer bullets".

### `/prd-to-issues`

**Trigger when:** user wants to convert a PRD to issues, create implementation tickets, or break down a PRD into work items.

### `/request-refactor-plan`

**Trigger when:** user wants to plan a refactor, create a refactoring RFC, or break a refactor into safe incremental steps.

### `/improve-codebase-architecture`

**Trigger when:** user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more testable.

### `/design-an-interface`

**Trigger when:** user wants to design an API, explore interface options, compare module shapes, or mentions "design it twice".

### `/git-guardrails-claude-code`

**Trigger when:** user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code.

### `/write-a-skill`

**Trigger when:** user wants to create, write, or build a new Claude Code skill.

## Project Context

See [.claude/docs/project.md](.claude/docs/project.md) for project-specific details (tech stack, architecture, test markers).
```

- [ ] **Step 2: Commit**

```bash
git add core/CLAUDE-base.md
git commit -m "feat: create CLAUDE-base.md with universal methodology and skill triggers"
```

---

### Task 4: Create settings-base.json

Extract the universal hook config (file protection) into `core/settings-base.json` (D13).

**Files:**

- Create: `core/settings-base.json`

- [ ] **Step 1: Write core/settings-base.json**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.py"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add core/settings-base.json
git commit -m "feat: create settings-base.json with universal file protection hook"
```

---

### Task 5: Build Script — Tests First

Write failing tests for `scripts/build_preset.py` before implementing it (D18, D22).

**Files:**

- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_build.py`
- Create: `tests/test_validation.py`
- Create: `scripts/__init__.py`

- [ ] **Step 1: Create test infrastructure**

Create `tests/__init__.py` and `scripts/__init__.py` (empty files).

- [ ] **Step 2: Write conftest.py with shared fixtures**

```python
"""Shared test fixtures for the template system."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create a minimal template repo structure for testing."""
    # Core structure
    core = tmp_path / "core"
    core.mkdir()

    # Core skills
    skills = core / "skills"
    skills.mkdir()
    for skill_name in ["commit", "daa-code-review", "tdd"]:
        skill_dir = skills / skill_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(f"# {skill_name} skill")

    # Core docs
    docs = core / "docs"
    docs.mkdir()
    (docs / "tdd.md").write_text("# TDD methodology")
    (docs / "root-cause-tracing.md").write_text("# Root cause tracing")

    # Core hooks
    hooks = core / "hooks"
    hooks.mkdir()
    (hooks / "protect-files.py").write_text("# protect files hook")

    # Core base files
    (core / "CLAUDE-base.md").write_text("# Base CLAUDE\n\n## Methodology\n")
    (core / "settings-base.json").write_text(json.dumps({
        "hooks": {
            "PreToolUse": [{"matcher": "Edit|Write", "hooks": []}]
        }
    }))

    # Presets directory
    presets = tmp_path / "presets"
    presets.mkdir()

    # A sample preset
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

    # Preset-specific skill
    preset_skills = preset / "skills"
    preset_skills.mkdir()
    deploy_skill = preset_skills / "deploy"
    deploy_skill.mkdir()
    (deploy_skill / "SKILL.md").write_text("# deploy skill")

    # Preset-specific hook
    preset_hooks = preset / "hooks"
    preset_hooks.mkdir()
    (preset_hooks / "post-edit-lint.py").write_text("# lint hook")

    # Dist directory
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
```

- [ ] **Step 3: Write test_build.py — build correctness tests**

```python
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
        # Create a preset skill with same name as core skill
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
        """When both base and preset define the same hook type, entries are appended."""
        import json

        # Add PreToolUse to preset settings (base already has PreToolUse)
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

        # PreToolUse should have both base entry and preset entry
        assert len(settings["hooks"]["PreToolUse"]) == 2
        assert settings["hooks"]["PreToolUse"][0]["matcher"] == "Edit|Write"
        assert settings["hooks"]["PreToolUse"][1]["matcher"] == "Bash"
```

- [ ] **Step 4: Write test_validation.py — fail-fast tests**

```python
"""Tests for build validation — bad manifests cause fail-fast errors (D19)."""

from pathlib import Path

import pytest

from scripts.build_preset import build_preset, BuildValidationError


class TestValidation:
    """Build fails fast on invalid input."""

    def test_missing_preset_raises_error(self, tmp_repo: Path) -> None:
        with pytest.raises(BuildValidationError, match="not-a-preset"):
            build_preset("not-a-preset", repo_root=tmp_repo)

    def test_missing_preset_skill_raises_error(self, bad_manifest_repo: Path) -> None:
        with pytest.raises(BuildValidationError, match="nonexistent-skill"):
            build_preset("broken", repo_root=bad_manifest_repo)

    def test_missing_preset_hook_raises_error(self, tmp_repo: Path) -> None:
        import json

        preset = tmp_repo / "presets" / "bad-hook"
        preset.mkdir()
        (preset / "manifest.json").write_text(json.dumps({
            "name": "bad-hook",
            "description": "Bad hook reference",
            "core": {"skills": "all", "docs": "all", "hooks": ["protect-files.py"]},
            "exclude": [],
            "preset_skills": [],
            "preset_hooks": ["missing-hook.py"],
        }))
        (preset / "CLAUDE-preset.md").write_text("\n## Bad\n")
        (preset / "settings-preset.json").write_text(json.dumps({"hooks": {}}))
        preset_hooks = preset / "hooks"
        preset_hooks.mkdir()

        with pytest.raises(BuildValidationError, match="missing-hook.py"):
            build_preset("bad-hook", repo_root=tmp_repo)

    def test_missing_core_hook_raises_error(self, tmp_repo: Path) -> None:
        import json

        preset = tmp_repo / "presets" / "python-api"
        manifest_path = preset / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["core"]["hooks"] = ["nonexistent-hook.py"]
        manifest_path.write_text(json.dumps(manifest))

        with pytest.raises(BuildValidationError, match="nonexistent-hook.py"):
            build_preset("python-api", repo_root=tmp_repo)

    def test_exclude_conflicts_with_preset_skill(self, tmp_repo: Path) -> None:
        """Excluding a skill that's also in preset_skills should fail (D17 + D11 guard)."""
        preset = tmp_repo / "presets" / "conflict"
        preset.mkdir()
        (preset / "manifest.json").write_text(json.dumps({
            "name": "conflict",
            "description": "Conflict test",
            "core": {"skills": "all", "docs": "all", "hooks": ["protect-files.py"]},
            "exclude": ["skills/deploy"],
            "preset_skills": ["deploy"],
            "preset_hooks": [],
        }))
        (preset / "CLAUDE-preset.md").write_text("\n## Conflict\n")
        (preset / "settings-preset.json").write_text(json.dumps({"hooks": {}}))
        preset_skills = preset / "skills" / "deploy"
        preset_skills.mkdir(parents=True)
        (preset_skills / "SKILL.md").write_text("# deploy")

        with pytest.raises(BuildValidationError, match="both preset_skills and exclude"):
            build_preset("conflict", repo_root=tmp_repo)
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `uv run pytest tests/test_build.py tests/test_validation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.build_preset'`

- [ ] **Step 6: Commit failing tests**

```bash
git add tests/ scripts/__init__.py
git commit -m "test: add failing tests for build_preset (red phase)"
```

---

### Task 6: Build Script — Implementation

Write `scripts/build_preset.py` to make all tests from Task 5 pass (D10, D15, D16, D17, D19, D25).

**Files:**

- Create: `scripts/build_preset.py`

- [ ] **Step 1: Implement build_preset.py**

```python
"""Assemble a Claude config preset from core + delta.

Build order (D16):
1. Copy all core/skills/ → dist/<preset>/.claude/skills/
2. Copy all core/docs/ → dist/<preset>/.claude/docs/
3. Copy core hooks listed in manifest → dist/<preset>/.claude/hooks/
4. Copy preset-specific skills (overrides core on collision, D17)
5. Copy preset-specific hooks
6. Merge settings-base.json + settings-preset.json → .claude/settings.json (D13)
7. Concatenate CLAUDE-base.md + CLAUDE-preset.md → CLAUDE.md (D12)
8. Apply exclusions from manifest (D11)
9. Write .template-version (D25)
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class BuildValidationError(Exception):
    """Raised when manifest validation fails."""


def _get_version() -> str:
    """Get current git tag or short commit hash for .template-version (D25)."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _validate_manifest(
    manifest: dict,
    core_path: Path,
    preset_path: Path,
) -> None:
    """Validate all manifest references exist. Fail fast if not (D19)."""
    errors: list[str] = []

    # Validate core hooks
    for hook_name in manifest["core"].get("hooks", []):
        if not (core_path / "hooks" / hook_name).exists():
            errors.append(f"Core hook not found: {hook_name}")

    # Validate preset skills
    for skill_name in manifest.get("preset_skills", []):
        if not (preset_path / "skills" / skill_name).exists():
            errors.append(f"Preset skill not found: {skill_name}")

    # Validate preset hooks
    for hook_name in manifest.get("preset_hooks", []):
        if not (preset_path / "hooks" / hook_name).exists():
            errors.append(f"Preset hook not found: {hook_name}")

    # Validate no conflict between preset_skills and exclude (D17 + D11 guard)
    preset_skill_names = {f"skills/{s}" for s in manifest.get("preset_skills", [])}
    excluded = set(manifest.get("exclude", []))
    conflicts = preset_skill_names & excluded
    if conflicts:
        errors.append(
            f"Skills in both preset_skills and exclude: {', '.join(conflicts)}. "
            f"A preset override cannot also be excluded."
        )

    if errors:
        raise BuildValidationError(
            "Manifest validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )


def _merge_settings(base_path: Path, preset_path: Path) -> dict:
    """Shallow-merge base + preset settings. Preset hook arrays append to base (D13)."""
    base = json.loads(base_path.read_text())
    preset = json.loads(preset_path.read_text())

    merged = json.loads(json.dumps(base))  # deep copy

    for hook_type, hook_list in preset.get("hooks", {}).items():
        if hook_type in merged.get("hooks", {}):
            merged["hooks"][hook_type].extend(hook_list)
        else:
            merged.setdefault("hooks", {})[hook_type] = hook_list

    return merged


def build_preset(preset_name: str, *, repo_root: Path | None = None) -> Path:
    """Build a preset into dist/<preset_name>/.

    Parameters
    ----------
    preset_name
        Name of the preset directory under presets/.
    repo_root
        Root of the template repo. Defaults to current working directory.

    Returns
    -------
    Path
        Path to the built output directory.
    """
    root = repo_root or Path.cwd()
    core_path = root / "core"
    preset_path = root / "presets" / preset_name
    dist_path = root / "dist" / preset_name
    claude_dir = dist_path / ".claude"

    # Validate preset exists
    if not preset_path.exists():
        raise BuildValidationError(
            f"Preset '{preset_name}' not found at {preset_path}"
        )

    # Load and validate manifest
    manifest = json.loads((preset_path / "manifest.json").read_text())
    _validate_manifest(manifest, core_path, preset_path)

    # Clean previous build
    if dist_path.exists():
        shutil.rmtree(dist_path)
    claude_dir.mkdir(parents=True)

    # Step 1: Copy core skills
    if manifest["core"].get("skills") == "all":
        shutil.copytree(core_path / "skills", claude_dir / "skills")

    # Step 2: Copy core docs
    if manifest["core"].get("docs") == "all":
        shutil.copytree(core_path / "docs", claude_dir / "docs")

    # Step 3: Copy core hooks
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    for hook_name in manifest["core"].get("hooks", []):
        shutil.copy2(core_path / "hooks" / hook_name, hooks_dir / hook_name)

    # Step 4: Copy preset skills (overrides core on collision, D17)
    for skill_name in manifest.get("preset_skills", []):
        src = preset_path / "skills" / skill_name
        dest = claude_dir / "skills" / skill_name
        if dest.exists():
            print(f"WARNING: preset skill '{skill_name}' overrides core skill '{skill_name}'")
            shutil.rmtree(dest)
        shutil.copytree(src, dest)

    # Step 5: Copy preset hooks
    for hook_name in manifest.get("preset_hooks", []):
        shutil.copy2(preset_path / "hooks" / hook_name, hooks_dir / hook_name)

    # Step 6: Merge settings
    merged_settings = _merge_settings(
        core_path / "settings-base.json",
        preset_path / "settings-preset.json",
    )
    (claude_dir / "settings.json").write_text(
        json.dumps(merged_settings, indent=2) + "\n"
    )

    # Step 7: Concatenate CLAUDE.md
    base_md = (core_path / "CLAUDE-base.md").read_text()
    preset_md = (preset_path / "CLAUDE-preset.md").read_text()
    (dist_path / "CLAUDE.md").write_text(base_md + preset_md)

    # Step 8: Apply exclusions
    for exclusion in manifest.get("exclude", []):
        excluded_path = claude_dir / exclusion
        if excluded_path.exists():
            if excluded_path.is_dir():
                shutil.rmtree(excluded_path)
            else:
                excluded_path.unlink()

    # Step 9: Write .template-version (D25)
    (claude_dir / ".template-version").write_text(_get_version() + "\n")

    return dist_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: uv run python scripts/build_preset.py <preset_name>")
        sys.exit(1)

    preset = sys.argv[1]
    output = build_preset(preset)
    print(f"\nBuilt preset '{preset}' → {output}/")
    print(f"  {output}/.claude/")
    print(f"  {output}/CLAUDE.md")
    print(f"\nCopy to your project:")
    print(f"  cp -r {output}/.claude /path/to/your/project/")
    print(f"  cp {output}/CLAUDE.md /path/to/your/project/")
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_build.py tests/test_validation.py -v`
Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add scripts/build_preset.py
git commit -m "feat: implement build_preset with validation, merging, and version tracking"
```

---

### Task 7: Diff Script — Tests First

Write failing tests for `scripts/diff_preset.py` (D14, D22).

**Files:**

- Create: `tests/test_diff.py`

- [ ] **Step 1: Write test_diff.py**

```python
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

        # Simulate modifying a skill in the "project"
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

        # Simulate adding a new file in the "project"
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

        # Simulate removing a file in the "project"
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_diff.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.diff_preset'`

- [ ] **Step 3: Commit failing tests**

```bash
git add tests/test_diff.py
git commit -m "test: add failing tests for diff_preset (red phase)"
```

---

### Task 8: Diff Script — Implementation

Write `scripts/diff_preset.py` to make all tests from Task 7 pass (D14).

**Files:**

- Create: `scripts/diff_preset.py`

- [ ] **Step 1: Implement diff_preset.py**

```python
"""Compare a project's .claude/ against a freshly-built preset to identify drift (D14).

Usage:
    uv run python scripts/diff_preset.py <preset_name> <project_path>
"""

from __future__ import annotations

import filecmp
from dataclasses import dataclass, field
from pathlib import Path

from scripts.build_preset import build_preset


@dataclass
class DiffResult:
    """Result of comparing a project's .claude/ against a built preset."""

    template_version: str | None = None
    modified_files: list[str] = field(default_factory=list)
    added_files: list[str] = field(default_factory=list)
    removed_files: list[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.modified_files or self.added_files or self.removed_files)


def _collect_files(directory: Path, relative_to: Path) -> dict[str, Path]:
    """Collect all files in a directory as relative path strings."""
    files = {}
    if directory.exists():
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.name != ".template-version":
                rel = str(file_path.relative_to(relative_to))
                files[rel] = file_path
    return files


def diff_preset(
    *,
    project_claude_dir: Path,
    project_claude_md: Path,
    preset_name: str,
    repo_root: Path | None = None,
) -> DiffResult:
    """Diff a project's .claude/ and CLAUDE.md against a freshly-built preset.

    Parameters
    ----------
    project_claude_dir
        Path to the project's .claude/ directory.
    project_claude_md
        Path to the project's CLAUDE.md file.
    preset_name
        Name of the preset to build and compare against.
    repo_root
        Root of the template repo.

    Returns
    -------
    DiffResult
        Summary of differences.
    """
    root = repo_root or Path.cwd()
    result = DiffResult()

    # Read template version from project
    version_file = project_claude_dir / ".template-version"
    if version_file.exists():
        result.template_version = version_file.read_text().strip()

    # Build a fresh preset for comparison
    dist_path = build_preset(preset_name, repo_root=root)
    baseline_claude_dir = dist_path / ".claude"
    baseline_claude_md = dist_path / "CLAUDE.md"

    # Collect files from both sides
    project_files = _collect_files(project_claude_dir, project_claude_dir)
    baseline_files = _collect_files(baseline_claude_dir, baseline_claude_dir)

    # Find modified and removed files
    for rel_path, baseline_path in baseline_files.items():
        if rel_path in project_files:
            if not filecmp.cmp(baseline_path, project_files[rel_path], shallow=False):
                result.modified_files.append(rel_path)
        else:
            result.removed_files.append(rel_path)

    # Find added files
    for rel_path in project_files:
        if rel_path not in baseline_files:
            result.added_files.append(rel_path)

    # Compare CLAUDE.md
    if project_claude_md.exists() and baseline_claude_md.exists():
        if not filecmp.cmp(project_claude_md, baseline_claude_md, shallow=False):
            result.modified_files.append("CLAUDE.md")
    elif project_claude_md.exists():
        result.added_files.append("CLAUDE.md")
    elif baseline_claude_md.exists():
        result.removed_files.append("CLAUDE.md")

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: uv run python scripts/diff_preset.py <preset_name> <project_path>")
        sys.exit(1)

    preset_name = sys.argv[1]
    project_path = Path(sys.argv[2])

    result = diff_preset(
        project_claude_dir=project_path / ".claude",
        project_claude_md=project_path / "CLAUDE.md",
        preset_name=preset_name,
    )

    if not result.has_changes:
        print("No differences found.")
    else:
        if result.modified_files:
            print("Modified:")
            for f in result.modified_files:
                print(f"  M {f}")
        if result.added_files:
            print("Added (in project, not in preset):")
            for f in result.added_files:
                print(f"  A {f}")
        if result.removed_files:
            print("Removed (in preset, not in project):")
            for f in result.removed_files:
                print(f"  D {f}")
    if result.template_version:
        print(f"\nProject was built from template version: {result.template_version}")
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_diff.py -v`
Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add scripts/diff_preset.py
git commit -m "feat: implement diff_preset for manual drift detection"
```

---

### Task 9: Smoke Test — Tests First

Write failing tests for `scripts/smoke_test.py` (D23).

**Files:**

- Create: `tests/test_smoke.py`

- [ ] **Step 1: Write test_smoke.py**

```python
"""Tests for smoke_test.py — validates internal consistency of built presets (D23)."""

import json
from pathlib import Path

import pytest

from scripts.build_preset import build_preset
from scripts.smoke_test import smoke_test, SmokeTestFailure


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_smoke.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.smoke_test'`

- [ ] **Step 3: Commit failing tests**

```bash
git add tests/test_smoke.py
git commit -m "test: add failing tests for smoke_test (red phase)"
```

---

### Task 10: Smoke Test — Implementation

Write `scripts/smoke_test.py` to make all tests from Task 9 pass (D23).

**Files:**

- Create: `scripts/smoke_test.py`

- [ ] **Step 1: Implement smoke_test.py**

```python
"""Validate internal consistency of a built preset (D23).

Checks:
- Every skill referenced in CLAUDE.md has a directory in .claude/skills/
- Every hook referenced in settings.json has a file in .claude/hooks/
- Every doc path referenced in CLAUDE.md exists
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SmokeTestResult:
    """Result of a smoke test run."""

    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


class SmokeTestFailure(Exception):
    """Raised when smoke test fails."""


def smoke_test(dist_path: Path) -> SmokeTestResult:
    """Validate internal consistency of a built preset.

    Parameters
    ----------
    dist_path
        Path to the built preset directory (e.g., dist/python-api/).

    Returns
    -------
    SmokeTestResult
        Result with any errors found.
    """
    result = SmokeTestResult()
    claude_dir = dist_path / ".claude"
    claude_md = dist_path / "CLAUDE.md"

    if not claude_md.exists():
        result.errors.append("CLAUDE.md not found in dist output")
        return result

    content = claude_md.read_text()

    # Check skill references: lines like ### `/skill-name`
    skill_pattern = re.compile(r"###\s+`/([^`]+)`")
    skills_dir = claude_dir / "skills"
    for match in skill_pattern.finditer(content):
        skill_name = match.group(1)
        # Normalize: daa-code-review -> code-review (handle prefixes)
        possible_names = [skill_name, skill_name.replace("daa-", "")]
        if not any((skills_dir / name).is_dir() for name in possible_names):
            result.errors.append(
                f"Skill '/{skill_name}' referenced in CLAUDE.md but no directory "
                f"found in .claude/skills/"
            )

    # Check doc references: [.claude/docs/something.md](.claude/docs/something.md)
    doc_pattern = re.compile(r"\[\.claude/docs/([^\]]+)\]\(\.claude/docs/[^)]+\)")
    for match in doc_pattern.finditer(content):
        doc_path = match.group(1)
        if not (claude_dir / "docs" / doc_path).exists():
            result.errors.append(
                f"Doc '.claude/docs/{doc_path}' referenced in CLAUDE.md but file not found"
            )

    # Check hook references in settings.json
    settings_path = claude_dir / "settings.json"
    if settings_path.exists():
        settings = json.loads(settings_path.read_text())
        hooks_dir = claude_dir / "hooks"
        for hook_type, hook_entries in settings.get("hooks", {}).items():
            for entry in hook_entries:
                for hook in entry.get("hooks", []):
                    command = hook.get("command", "")
                    # Extract hook filename from command
                    hook_match = re.search(
                        r'hooks/([^\s"]+)', command
                    )
                    if hook_match:
                        hook_file = hook_match.group(1)
                        if not (hooks_dir / hook_file).exists():
                            result.errors.append(
                                f"Hook '{hook_file}' referenced in settings.json "
                                f"but not found in .claude/hooks/"
                            )

    return result


if __name__ == "__main__":
    import sys

    from scripts.build_preset import build_preset

    if len(sys.argv) != 2:
        print("Usage: uv run python scripts/smoke_test.py <preset_name>")
        sys.exit(1)

    preset_name = sys.argv[1]
    dist_path = build_preset(preset_name)
    result = smoke_test(dist_path)

    if result.passed:
        print(f"PASS: preset '{preset_name}' is internally consistent")
    else:
        print(f"FAIL: preset '{preset_name}' has {len(result.errors)} error(s):")
        for error in result.errors:
            print(f"  - {error}")
        sys.exit(1)
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_smoke.py -v`
Expected: All tests PASS.

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests across all test files PASS.

- [ ] **Step 4: Commit**

```bash
git add scripts/smoke_test.py
git commit -m "feat: implement smoke_test for built preset consistency validation"
```

---

### Task 11: Create Preset — python-api

Create the first preset delta: `python-api` (D3).

**Files:**

- Create: `presets/python-api/manifest.json`
- Create: `presets/python-api/CLAUDE-preset.md`
- Create: `presets/python-api/settings-preset.json`
- Move: `_staging/skills/deploy` → `presets/python-api/skills/deploy/`
- Move: `_staging/skills/setup-pre-commit` → `presets/python-api/skills/setup-pre-commit/`
- Create: `presets/python-api/hooks/post-edit-lint.py`

- [ ] **Step 1: Create preset directory structure**

```bash
mkdir -p presets/python-api/skills presets/python-api/hooks
```

- [ ] **Step 2: Move preset-specific skills from staging**

```bash
mv _staging/skills/deploy presets/python-api/skills/
mv _staging/skills/setup-pre-commit presets/python-api/skills/
```

- [ ] **Step 3: Write manifest.json**

```json
{
  "name": "python-api",
  "description": "Python backend services — Lambda, FastAPI, Flask",
  "core": {
    "skills": "all",
    "docs": "all",
    "hooks": ["protect-files.py"]
  },
  "exclude": [],
  "preset_skills": ["deploy", "setup-pre-commit"],
  "preset_hooks": ["post-edit-lint.py"]
}
```

- [ ] **Step 4: Write CLAUDE-preset.md**

```markdown
## Testing

- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=src --cov-report=term-missing`
- Prefer real code over mocks
- Test fixtures in `tests/fixtures/`

## Skills (Preset-Specific)

### `/deploy`

**Trigger when:** user asks to deploy, redeploy, push to Lambda, update the service, or after updating lambda_function.py.

### `/setup-pre-commit`

**Trigger when:** user wants to add pre-commit hooks, set up Husky, or configure lint-staged.
```

- [ ] **Step 5: Write settings-preset.json**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-edit-lint.py"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: Write post-edit-lint.py for python-api (Ruff only)**

Adapt from `_staging/post-edit-lint.py` — strip Prettier, ESLint, Stylelint. Keep only Ruff for `.py` files.

Read `_staging/post-edit-lint.py` for the current implementation, then create a Python-only version at `presets/python-api/hooks/post-edit-lint.py` that:

- Reads the file path from stdin (same hook protocol)
- Runs `ruff check --fix` and `ruff format` on `.py` files only
- Skips all other file types silently

- [ ] **Step 7: Build and smoke test**

```bash
uv run python -c "
from scripts.build_preset import build_preset
from scripts.smoke_test import smoke_test
dist = build_preset('python-api')
result = smoke_test(dist)
print('PASS' if result.passed else f'FAIL: {result.errors}')
"
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add presets/python-api/
git commit -m "feat: create python-api preset with deploy, setup-pre-commit, Ruff linting"
```

---

### Task 12: Create Preset — data-pipeline

**Files:**

- Create: `presets/data-pipeline/manifest.json`
- Create: `presets/data-pipeline/CLAUDE-preset.md`
- Create: `presets/data-pipeline/settings-preset.json`
- Create: `presets/data-pipeline/hooks/post-edit-lint.py`

- [ ] **Step 1: Create preset directory structure**

```bash
mkdir -p presets/data-pipeline/hooks
```

- [ ] **Step 2: Write manifest.json**

```json
{
  "name": "data-pipeline",
  "description": "ETL/ELT pipelines, SQL transformations, scheduled data jobs",
  "core": {
    "skills": "all",
    "docs": "all",
    "hooks": ["protect-files.py"]
  },
  "exclude": [],
  "preset_skills": [],
  "preset_hooks": ["post-edit-lint.py"]
}
```

- [ ] **Step 3: Write CLAUDE-preset.md**

```markdown
## Testing

- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=src --cov-report=term-missing`
- Prefer real code over mocks
- Test fixtures in `tests/fixtures/`
- For SQL transformations, test with sample data in fixtures

## Data Pipeline Conventions

- SQL files use lowercase keywords
- Pipeline stages should be idempotent where possible
- Log row counts at each transformation stage
```

- [ ] **Step 4: Write settings-preset.json**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-edit-lint.py"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: Write post-edit-lint.py (Ruff only)**

Same as python-api linting hook — Ruff for `.py` files only.

- [ ] **Step 6: Build and smoke test**

Run build + smoke test (same pattern as Task 11 Step 7).
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add presets/data-pipeline/
git commit -m "feat: create data-pipeline preset with Ruff linting"
```

---

### Task 13: Create Preset — full-stack

**Files:**

- Create: `presets/full-stack/manifest.json`
- Create: `presets/full-stack/CLAUDE-preset.md`
- Create: `presets/full-stack/settings-preset.json`
- Copy: `_staging/skills/setup-pre-commit` → `presets/full-stack/skills/setup-pre-commit/`
- Create: `presets/full-stack/hooks/post-edit-lint.py`

- [ ] **Step 1: Create preset directory structure**

```bash
mkdir -p presets/full-stack/skills presets/full-stack/hooks
```

- [ ] **Step 2: Copy setup-pre-commit skill**

```bash
cp -r presets/python-api/skills/setup-pre-commit presets/full-stack/skills/
```

- [ ] **Step 3: Write manifest.json**

```json
{
  "name": "full-stack",
  "description": "React/Next.js frontend + Python backend",
  "core": {
    "skills": "all",
    "docs": "all",
    "hooks": ["protect-files.py"]
  },
  "exclude": [],
  "preset_skills": ["setup-pre-commit"],
  "preset_hooks": ["post-edit-lint.py"]
}
```

- [ ] **Step 4: Write CLAUDE-preset.md**

```markdown
## Testing

### Backend

- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=src --cov-report=term-missing`

### Frontend

- Run tests: `npm test`
- Run build: `npm run build`

- Prefer real code over mocks
- Test fixtures in `tests/fixtures/`

## Skills (Preset-Specific)

### `/setup-pre-commit`

**Trigger when:** user wants to add pre-commit hooks, set up Husky, or configure lint-staged.
```

- [ ] **Step 5: Write settings-preset.json**

Same structure as python-api (PostToolUse hook for Edit|Write).

- [ ] **Step 6: Write post-edit-lint.py (Ruff + Prettier + ESLint + Stylelint)**

Adapt from `_staging/post-edit-lint.py` — keep all linters:

- Ruff for `.py` files
- Prettier for `.html`, `.css`, `.js`, `.ts`, `.jsx`, `.tsx`, `.md`, `.json`
- ESLint for `.js`, `.ts`, `.jsx`, `.tsx`
- Stylelint for `.css`

- [ ] **Step 7: Build and smoke test**

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add presets/full-stack/
git commit -m "feat: create full-stack preset with setup-pre-commit, full linter stack"
```

---

### Task 14: Create Preset — claude-tooling

**Files:**

- Create: `presets/claude-tooling/manifest.json`
- Create: `presets/claude-tooling/CLAUDE-preset.md`
- Create: `presets/claude-tooling/settings-preset.json`
- Create: `presets/claude-tooling/hooks/post-edit-lint.py`

- [ ] **Step 1: Create preset directory structure**

```bash
mkdir -p presets/claude-tooling/hooks
```

- [ ] **Step 2: Write manifest.json**

```json
{
  "name": "claude-tooling",
  "description": "Developing Claude skills, hooks, agents, and template configurations",
  "core": {
    "skills": "all",
    "docs": "all",
    "hooks": ["protect-files.py"]
  },
  "exclude": [],
  "preset_skills": [],
  "preset_hooks": ["post-edit-lint.py"]
}
```

- [ ] **Step 3: Write CLAUDE-preset.md**

```markdown
## Testing

- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=scripts --cov-report=term-missing`
- Test the build system: `uv run pytest tests/ -v`

## Claude Tooling Conventions

- Skills follow the structure defined in `core/skills/write-a-skill/`
- Every SKILL.md must have: name, description, trigger conditions
- Hook scripts must read from stdin and follow the Claude Code hook protocol
- Test all build/diff/smoke scripts with pytest before committing
```

- [ ] **Step 4: Write settings-preset.json**

Same structure as python-api (PostToolUse hook for Edit|Write).

- [ ] **Step 5: Write post-edit-lint.py (Ruff + Prettier for markdown/json)**

- Ruff for `.py` files
- Prettier for `.md`, `.json` files only

- [ ] **Step 6: Build and smoke test**

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add presets/claude-tooling/
git commit -m "feat: create claude-tooling preset for skill/hook/template development"
```

---

### Task 15: Create Preset — analysis

**Files:**

- Create: `presets/analysis/manifest.json`
- Create: `presets/analysis/CLAUDE-preset.md`
- Create: `presets/analysis/settings-preset.json`
- Create: `presets/analysis/hooks/post-edit-lint.py`

- [ ] **Step 1: Create preset directory structure**

```bash
mkdir -p presets/analysis/hooks
```

- [ ] **Step 2: Write manifest.json**

```json
{
  "name": "analysis",
  "description": "Notebooks, R/Python scripts, statistical analysis, exploratory work",
  "core": {
    "skills": "all",
    "docs": "all",
    "hooks": ["protect-files.py"]
  },
  "exclude": [],
  "preset_skills": [],
  "preset_hooks": ["post-edit-lint.py"]
}
```

- [ ] **Step 3: Write CLAUDE-preset.md**

```markdown
## Testing

- Run tests: `uv run pytest`
- Validate analysis outputs against known fixtures when possible
- For exploratory scripts, verify outputs are reproducible with a fixed seed

## Analysis Conventions

- Use descriptive notebook cell headings
- Pin random seeds for reproducibility
- Document data sources and assumptions inline
```

- [ ] **Step 4: Write settings-preset.json**

Same structure as python-api (PostToolUse hook for Edit|Write).

- [ ] **Step 5: Write post-edit-lint.py (Ruff only)**

Same as python-api and data-pipeline — Ruff for `.py` files only.

- [ ] **Step 6: Build and smoke test**

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add presets/analysis/
git commit -m "feat: create analysis preset for notebooks and exploratory work"
```

---

### Task 16: Root Documentation

Create the template system's own CLAUDE.md, COMPATIBILITY.md, and clean up (D6, D21, D24).

**Files:**

- Rewrite: `CLAUDE.md` (now documents the template system)
- Create: `COMPATIBILITY.md`

- [ ] **Step 1: Rewrite root CLAUDE.md**

```markdown
# Claude Workflow Template System

This file is auto-loaded every conversation. It defines how Claude should work in this repo.

## What This Repo Is

A template system for Claude Code configurations. It produces ready-to-copy `.claude/` directories + `CLAUDE.md` files for new projects.

## Architecture

- `core/` — Universal skills (17), methodology docs (4), file protection hook
- `presets/` — Named project type configurations (python-api, data-pipeline, full-stack, claude-tooling, analysis)
- `scripts/` — Python build/diff/smoke-test tooling
- `dist/` — Build output (gitignored)

## Commands

- Build a preset: `uv run python scripts/build_preset.py <preset_name>`
- Diff a project: `uv run python scripts/diff_preset.py <preset_name> <project_path>`
- Smoke test: `uv run python scripts/smoke_test.py <preset_name>`
- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=scripts --cov-report=term-missing`

## Methodology

### TDD — Test-Driven Development

Write the test first. Watch it fail. Write minimal code to pass.
Full process: [core/docs/tdd.md](core/docs/tdd.md)

### Root Cause Tracing

Never fix at the symptom. Trace backward to the original trigger.
Full process: [core/docs/root-cause-tracing.md](core/docs/root-cause-tracing.md)

### Subagent-Driven Development

Dispatch a fresh subagent per task with code review between each.
Full process: [core/docs/subagent-development.md](core/docs/subagent-development.md)

### Parallel Agent Dispatch

When 3+ unrelated failures need investigation, dispatch one agent per problem domain.
Full process: [core/docs/parallel-agents.md](core/docs/parallel-agents.md)

## Code Style

- Descriptive variable names (`private_key_bytes` not `pkb`)
- SOLID, DRY, YAGNI — simplicity over complexity
- Type hints on all function signatures
- Numpy-style docstrings for public functions

## Planning

Write plans to `docs/plans/{file_name}.md`. Archive completed plans to `docs/archive/`.

## Skills

Skills live in `core/skills/` (universal) and `presets/*/skills/` (preset-specific).
See core CLAUDE.md for skill trigger conditions.
```

- [ ] **Step 2: Write COMPATIBILITY.md**

```markdown
# Claude Code Compatibility

This document lists Claude Code features this template system depends on (D21).
Update when a breaking change is discovered.

## Required Features

### Hooks

- `PreToolUse` hook type — used for file protection
- `PostToolUse` hook type — used for auto-linting
- `Edit|Write` matcher syntax
- `$CLAUDE_PROJECT_DIR` environment variable in hook commands
- Hook scripts receive tool input as JSON on stdin

### Skills

- `.claude/skills/*/SKILL.md` auto-discovery
- Skill `name` and `description` frontmatter for triggering
- `references/` subdirectory loading

### Agent Features

- `Agent` tool with `subagent_type` parameter
- `TodoWrite` tool for task tracking
- `EnterPlanMode` / `ExitPlanMode` tools

### Settings

- `.claude/settings.json` project-level settings
- Hook arrays in settings with `matcher` and `hooks` fields

## Last Verified

2026-03-21 — Claude Code with Opus 4.6
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md COMPATIBILITY.md
git commit -m "docs: rewrite root CLAUDE.md for template system, add COMPATIBILITY.md"
```

---

### Task 17: Cleanup and Final Verification

Remove staging artifacts, verify the full build, clean up the old `.claude/` directory.

**Files:**

- Remove: `_staging/`
- Remove: remaining `.claude/` contents (replaced by core/ + presets/)
- Verify: all presets build and pass smoke tests

- [ ] **Step 1: Clean up staging directory**

```bash
rm -rf _staging/
```

- [ ] **Step 2: Clean up old .claude/ directory**

The old `.claude/` should now be empty (or contain only `.DS_Store`). Remove it — this repo will use the `claude-tooling` preset output as its own `.claude/` (D24).

```bash
rm -rf .claude/
```

- [ ] **Step 3: Build the claude-tooling preset for this repo**

```bash
uv run python -c "from scripts.build_preset import build_preset; build_preset('claude-tooling')"
cp -r dist/claude-tooling/.claude .claude/
```

- [ ] **Step 4: Build and smoke test all presets**

```bash
uv run python -c "
from scripts.build_preset import build_preset
from scripts.smoke_test import smoke_test

for preset in ['python-api', 'data-pipeline', 'full-stack', 'claude-tooling', 'analysis']:
    dist = build_preset(preset)
    result = smoke_test(dist)
    status = 'PASS' if result.passed else f'FAIL: {result.errors}'
    print(f'{preset}: {status}')
"
```

Expected: All 5 presets PASS.

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -v --tb=short`
Expected: All tests PASS.

- [ ] **Step 6: Tag initial release (D25)**

```bash
git tag v0.1.0
```

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "feat: complete template system — 5 presets, build/diff/smoke tooling

Restructured claude-workflow from a working project into a Claude Code
configuration template system. Core + delta architecture with 17 universal
skills, 5 named presets (python-api, data-pipeline, full-stack,
claude-tooling, analysis), and Python build/diff/smoke-test tooling."
```

---

## Execution Summary

| Task | Description                            | Tests         |
| ---- | -------------------------------------- | ------------- |
| 1    | Project initialization (uv, gitignore) | —             |
| 2    | Create core/ from existing .claude/    | —             |
| 3    | Create CLAUDE-base.md                  | —             |
| 4    | Create settings-base.json              | —             |
| 5    | Build script tests (red)               | 14 tests      |
| 6    | Build script implementation (green)    | 14 tests pass |
| 7    | Diff script tests (red)                | 6 tests       |
| 8    | Diff script implementation (green)     | 6 tests pass  |
| 9    | Smoke test tests (red)                 | 4 tests       |
| 10   | Smoke test implementation (green)      | 4 tests pass  |
| 11   | Preset: python-api                     | smoke test    |
| 12   | Preset: data-pipeline                  | smoke test    |
| 13   | Preset: full-stack                     | smoke test    |
| 14   | Preset: claude-tooling                 | smoke test    |
| 15   | Preset: analysis                       | smoke test    |
| 16   | Root documentation                     | —             |
| 17   | Cleanup and final verification         | full suite    |
