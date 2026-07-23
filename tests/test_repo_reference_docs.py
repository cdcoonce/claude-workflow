"""Tests for the repo-reference-docs core skill and its staleness checker."""

import importlib.util
import sys
from pathlib import Path

from scripts.build_preset import build_preset

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "core" / "skills" / "repo-reference-docs"


def test_repo_reference_docs_is_core_skill() -> None:
    """The skill is owned by core/skills so it flows into workbench via core.skills=all."""
    assert (SKILL_DIR / "SKILL.md").is_file()


def test_workbench_ships_repo_reference_docs() -> None:
    """workbench (core.skills: 'all') includes the skill in its built plugin."""
    dist_path = build_preset("workbench", repo_root=REPO_ROOT)
    assert (dist_path / "skills" / "repo-reference-docs" / "SKILL.md").is_file()


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "check_docs", SKILL_DIR / "scripts" / "check_docs.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_checker_flags_missing_covered_path(tmp_path: Path) -> None:
    """A doc whose provenance lists a now-deleted path is reported stale."""
    checker = _load_checker()
    doc = tmp_path / "architecture.md"
    doc.write_text(
        "# Architecture\n\nBody.\n\n"
        "<!-- repo-reference-docs: baseline=abc123 "
        "covers=src/gone.py,src/here.py -->\n"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "here.py").write_text("x = 1\n")
    findings = checker.check_docs(tmp_path, repo_root=tmp_path)
    assert any("gone.py" in f.detail for f in findings)
    assert all("here.py" not in f.detail for f in findings)


def test_checker_passes_when_all_covered_paths_exist(tmp_path: Path) -> None:
    """No findings when every covered path still exists."""
    checker = _load_checker()
    doc = tmp_path / "module-map.md"
    doc.write_text(
        "# Modules\n\nBody.\n\n"
        "<!-- repo-reference-docs: baseline=abc123 covers=src/here.py -->\n"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "here.py").write_text("x = 1\n")
    findings = checker.check_docs(tmp_path, repo_root=tmp_path)
    assert findings == []
