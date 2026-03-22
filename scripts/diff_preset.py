"""Compare a project's .claude/ against a freshly-built preset to identify drift (D14).

Usage:
    uv run python -m scripts.diff_preset <preset_name> <project_path>
"""

from __future__ import annotations

import filecmp
import sys
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

    version_file = project_claude_dir / ".template-version"
    if version_file.exists():
        result.template_version = version_file.read_text().strip()

    dist_path = build_preset(preset_name, repo_root=root)
    baseline_claude_dir = dist_path / ".claude"
    baseline_claude_md = dist_path / "CLAUDE.md"

    project_files = _collect_files(project_claude_dir, project_claude_dir)
    baseline_files = _collect_files(baseline_claude_dir, baseline_claude_dir)

    for rel_path, baseline_path in baseline_files.items():
        if rel_path in project_files:
            if not filecmp.cmp(baseline_path, project_files[rel_path], shallow=False):
                result.modified_files.append(rel_path)
        else:
            result.removed_files.append(rel_path)

    for rel_path in project_files:
        if rel_path not in baseline_files:
            result.added_files.append(rel_path)

    if project_claude_md.exists() and baseline_claude_md.exists():
        if not filecmp.cmp(project_claude_md, baseline_claude_md, shallow=False):
            result.modified_files.append("CLAUDE.md")
    elif project_claude_md.exists():
        result.added_files.append("CLAUDE.md")
    elif baseline_claude_md.exists():
        result.removed_files.append("CLAUDE.md")

    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: uv run python -m scripts.diff_preset <preset_name> <project_path>")
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
