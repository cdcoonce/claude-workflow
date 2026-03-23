"""Validate internal consistency of a built preset (D23).

Checks:
- Every skill referenced in CLAUDE.md has a directory in .claude/skills/
- Every hook referenced in settings.json has a file in .claude/hooks/
- Every doc path referenced in CLAUDE.md exists
- Every intra-skill reference link in SKILL.md files resolves to an existing file
- Every agent in .claude/agents/ has valid frontmatter (name, description, role)
- Agent names match their directory names
- Agent skills.add references resolve to existing skills
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


def _parse_frontmatter(text: str) -> dict | None:
    """Parse YAML frontmatter from markdown text.

    Parameters
    ----------
    text
        Full markdown text that may begin with ``---`` delimited frontmatter.

    Returns
    -------
    dict | None
        Parsed key-value pairs, or None if no valid frontmatter found.
    """
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    frontmatter_text = text[3:end].strip()
    if not frontmatter_text:
        return None
    result: dict = {}
    current_key: str | None = None
    for line in frontmatter_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        is_indented = line != line.lstrip()
        if ":" in stripped and not stripped.startswith("-") and not is_indented:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                result[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            elif value:
                result[key] = value
            else:
                result[key] = {}
                current_key = key
        elif current_key and ":" in stripped and is_indented:
            sub_key, _, sub_value = stripped.partition(":")
            sub_key = sub_key.strip()
            sub_value = sub_value.strip()
            if sub_value.startswith("[") and sub_value.endswith("]"):
                result[current_key][sub_key] = [
                    v.strip() for v in sub_value[1:-1].split(",") if v.strip()
                ]
            else:
                result[current_key][sub_key] = sub_value
    return result if result else None


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

    # Check intra-skill reference links in SKILL.md files
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    if skills_dir.exists():
        for skill_md in skills_dir.rglob("SKILL.md"):
            skill_content = skill_md.read_text()
            for match in link_pattern.finditer(skill_content):
                link_target = match.group(2)
                # Skip external URLs, anchors, and project-root-relative paths
                if link_target.startswith(("http://", "https://", "#", ".claude/")):
                    continue
                resolved = (skill_md.parent / link_target).resolve()
                if not resolved.exists():
                    skill_name = skill_md.parent.name
                    result.errors.append(
                        f"Skill '{skill_name}/SKILL.md' links to "
                        f"'{link_target}' but file not found"
                    )

    # Check agent frontmatter in .claude/agents/
    agents_dir = claude_dir / "agents"
    if agents_dir.exists():
        for agent_dir in sorted(agents_dir.iterdir()):
            if not agent_dir.is_dir():
                continue
            agent_md = agent_dir / "AGENT.md"
            if not agent_md.exists():
                result.errors.append(
                    f"Agent '{agent_dir.name}' directory has no AGENT.md"
                )
                continue

            frontmatter = _parse_frontmatter(agent_md.read_text())
            if frontmatter is None:
                result.errors.append(
                    f"Agent '{agent_dir.name}/AGENT.md' has no valid frontmatter"
                )
                continue

            # Check required fields
            for req_field in ["name", "description", "role"]:
                if req_field not in frontmatter:
                    result.errors.append(
                        f"Agent '{agent_dir.name}/AGENT.md' missing required "
                        f"field '{req_field}'"
                    )

            # Validate role
            role = frontmatter.get("role", "")
            if role and role not in ("implementer", "reviewer"):
                result.errors.append(
                    f"Agent '{agent_dir.name}/AGENT.md' has invalid role "
                    f"'{role}' (must be 'implementer' or 'reviewer')"
                )

            # Validate name matches directory
            name = frontmatter.get("name", "")
            if name and name != agent_dir.name:
                result.errors.append(
                    f"Agent '{agent_dir.name}/AGENT.md' name '{name}' does not "
                    f"match directory name '{agent_dir.name}'"
                )

            # Validate skills.add references
            skills_config = frontmatter.get("skills", {})
            if isinstance(skills_config, dict):
                for skill_ref in skills_config.get("add", []):
                    if skills_dir.exists() and not (skills_dir / skill_ref).is_dir():
                        result.errors.append(
                            f"Agent '{agent_dir.name}/AGENT.md' references skill "
                            f"'{skill_ref}' in skills.add but skill not found "
                            f"in .claude/skills/"
                        )

    return result


if __name__ == "__main__":
    from scripts.build_preset import build_preset

    if len(sys.argv) != 2:
        print("Usage: uv run python -m scripts.smoke_test <preset_name>")
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
