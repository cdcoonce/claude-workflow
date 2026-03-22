"""Validate internal consistency of a built preset (D23).

Checks:
- Every skill referenced in CLAUDE.md has a directory in .claude/skills/
- Every hook referenced in settings.json has a file in .claude/hooks/
- Every doc path referenced in CLAUDE.md exists
"""

from __future__ import annotations

import json
import re
import sys
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
