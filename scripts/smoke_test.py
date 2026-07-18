"""Validate internal consistency of a built plugin.

Checks:
- .claude-plugin/plugin.json exists with required fields (name, version, description)
- Every directory in skills/ has a SKILL.md
- Every directory in agents/ has a valid AGENT.md (frontmatter with name, description, role)
- Agent names match their directory names
- Agent roles are one of the documented roles (see VALID_ROLES)
- Agent skills.add references resolve to existing skills in skills/
- hooks/hooks.json references scripts that exist in hooks/scripts/
- Every relative link in SKILL.md files resolves within the skill directory
- settings.json at root is valid JSON
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Valid agent roles, matching the documented vocabulary in CLAUDE.md.
VALID_ROLES = (
    "implementer",
    "reviewer",
    "analyst",
    "qa-tester",
    "skill-writer",
    "strategy",
)

# Link prefixes that are not intra-doc relative paths and should be skipped
# during link resolution (anchors, project-root-relative paths).
_LINK_SKIP_PREFIXES = ("#", ".claude/")

# Matches any URI scheme prefix (e.g. "http:", "mailto:", "tel:") so such
# links aren't mistaken for relative file paths.
_URI_SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")

_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# Authoring budget from core/skills/write-a-skill/references/quality-criteria.md.
SKILL_LINE_CAP = 100

# Frozen at #281: the skills that already exceeded SKILL_LINE_CAP when this
# check was introduced. Shrink-only — remove an entry once its SKILL.md drops
# under the cap; never add a new one (see SKILL_LINE_CAP_ALLOWLIST_BASELINE).
SKILL_LINE_CAP_ALLOWLIST = frozenset(
    {
        "add-claude-workflow-hook",
        "commit",
        "daa-code-review",
        "dev-cycle",
        "dignified-python",
        "github-cli",
        "grill-me",
        "plan-ceo-review",
        "prd-to-plan",
        "project-context",
        "readme-generator",
        "tdd",
        "triage-issue",
    }
)

# High-water mark for SKILL_LINE_CAP_ALLOWLIST, frozen independently of it so
# an edit to the allowlist above can't silently drag this along. Never edit
# this set — it exists only so _validate_allowlist_shrink_only can detect a
# future addition to SKILL_LINE_CAP_ALLOWLIST.
SKILL_LINE_CAP_ALLOWLIST_BASELINE = frozenset(
    {
        "add-claude-workflow-hook",
        "commit",
        "daa-code-review",
        "dev-cycle",
        "dignified-python",
        "github-cli",
        "grill-me",
        "plan-ceo-review",
        "prd-to-plan",
        "project-context",
        "readme-generator",
        "tdd",
        "triage-issue",
    }
)

# Frontmatter keys a SKILL.md may declare (write-a-skill quality-criteria.md).
_SKILL_FRONTMATTER_ALLOWED_KEYS = frozenset({"name", "description"})


def _validate_allowlist_shrink_only(
    current: frozenset[str], baseline: frozenset[str]
) -> list[str]:
    """Check that a grandfather allowlist has only shrunk from its baseline.

    Parameters
    ----------
    current
        The active allowlist.
    baseline
        The frozen snapshot captured when the allowlist was introduced.

    Returns
    -------
    list[str]
        Error strings for any entries in ``current`` but not ``baseline``.
    """
    added = sorted(current - baseline)
    if not added:
        return []
    return [
        f"SKILL_LINE_CAP_ALLOWLIST added entries {added} not present in "
        "SKILL_LINE_CAP_ALLOWLIST_BASELINE — the allowlist is shrink-only, "
        "remove them instead"
    ]


def _validate_doc_links(docs_dir: Path, doc_filename: str, label: str) -> list[str]:
    """Validate that relative links in doc files resolve to existing files.

    Parameters
    ----------
    docs_dir
        Root directory to search recursively for doc files (e.g., skills/).
    doc_filename
        Name of the doc file to look for (e.g., "SKILL.md").
    label
        Human-readable label used in error messages (e.g., "Skill").

    Returns
    -------
    list[str]
        Error strings for any links that fail to resolve.
    """
    errors: list[str] = []
    for doc_md in docs_dir.rglob(doc_filename):
        doc_content = doc_md.read_text(encoding="utf-8")
        in_fence = False
        fenced_lines: set[int] = set()
        for line_num, line in enumerate(doc_content.split("\n")):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                fenced_lines.add(line_num)

        for match in _LINK_PATTERN.finditer(doc_content):
            line_num = doc_content.count("\n", 0, match.start())
            if line_num in fenced_lines:
                continue
            link_target = match.group(2).strip()
            # Strip an optional markdown link title — [text](path "Title") — keeping
            # only the path token. Skip when the path is quote-wrapped, since such a
            # path may legitimately contain spaces.
            if link_target and not link_target.startswith(("'", '"')):
                link_target = link_target.split(None, 1)[0]
            if link_target.startswith(_LINK_SKIP_PREFIXES) or _URI_SCHEME_PATTERN.match(
                link_target
            ):
                continue
            file_part = re.split(r"[#?]", link_target, maxsplit=1)[0]
            if not file_part:
                continue
            resolved = (doc_md.parent / file_part).resolve()
            if not resolved.exists():
                doc_name = doc_md.parent.name
                errors.append(
                    f"{label} '{doc_name}/{doc_filename}' links to "
                    f"'{link_target}' but file not found"
                )
    return errors


def _strip_quotes(value: str) -> str:
    """Strip a single matching pair of surrounding quotes from a scalar.

    Parameters
    ----------
    value
        Raw scalar text, possibly wrapped in matching ``'`` or ``"`` quotes.

    Returns
    -------
    str
        ``value`` with one surrounding pair of quotes removed, or ``value``
        unchanged if it isn't quoted.
    """
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


@dataclass
class SmokeTestResult:
    """Result of a smoke test run."""

    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


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
    block_scalar = False
    for line in frontmatter_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        is_indented = line != line.lstrip()
        if ":" in stripped and not stripped.startswith("-") and not is_indented:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = re.sub(r"\s+#.*$", "", value.strip())
            if value.startswith("[") and value.endswith("]"):
                result[key] = [
                    _strip_quotes(v.strip())
                    for v in value[1:-1].split(",")
                    if v.strip()
                ]
                current_key = None
                block_scalar = False
            elif value and value[0] in ("|", ">"):
                # YAML block scalar (|, >, with optional chomping/indent indicator):
                # the value continues on the following indented lines.
                result[key] = ""
                current_key = key
                block_scalar = True
            elif value:
                result[key] = _strip_quotes(value)
                current_key = None
                block_scalar = False
            else:
                result[key] = {}
                current_key = key
                block_scalar = False
        elif current_key and is_indented:
            if block_scalar:
                # Fold every indented line into the value, colons and all.
                result[current_key] = f"{result[current_key]} {stripped}".strip()
            elif ":" in stripped:
                if not isinstance(result[current_key], dict):
                    result[current_key] = {}
                sub_key, _, sub_value = stripped.partition(":")
                sub_key = sub_key.strip()
                sub_value = sub_value.strip()
                if sub_value.startswith("[") and sub_value.endswith("]"):
                    result[current_key][sub_key] = [
                        _strip_quotes(v.strip())
                        for v in sub_value[1:-1].split(",")
                        if v.strip()
                    ]
                else:
                    result[current_key][sub_key] = _strip_quotes(sub_value)
            elif result[current_key] == {}:
                result[current_key] = stripped
            elif isinstance(result[current_key], str):
                result[current_key] = f"{result[current_key]} {stripped}"
    return result if result else None


def _core_skill_names(dist_path: Path) -> frozenset[str]:
    """Names of skills sourced from core/skills/, given a built plugin path.

    The skill-authoring budget checks (line cap, frontmatter shape, reference
    depth) enforce this repo's own authoring standard and apply only to core
    skills, not preset-specific skills bundled alongside them in the same
    built ``skills/`` directory.

    Parameters
    ----------
    dist_path
        Path to the built plugin directory (e.g., dist/python-api/), expected
        at ``<repo_root>/dist/<preset_name>``.

    Returns
    -------
    frozenset[str]
        Directory names under core/skills/, or an empty set if core/skills/
        can't be located relative to ``dist_path``.
    """
    core_skills_dir = dist_path.parent.parent / "core" / "skills"
    if not core_skills_dir.is_dir():
        return frozenset()
    return frozenset(d.name for d in core_skills_dir.iterdir() if d.is_dir())


def smoke_test(dist_path: Path) -> SmokeTestResult:
    """Validate internal consistency of a built plugin.

    Parameters
    ----------
    dist_path
        Path to the built plugin directory (e.g., dist/python-api/).

    Returns
    -------
    SmokeTestResult
        Result with any errors found.
    """
    result = SmokeTestResult()

    result.errors.extend(
        _validate_allowlist_shrink_only(
            SKILL_LINE_CAP_ALLOWLIST, SKILL_LINE_CAP_ALLOWLIST_BASELINE
        )
    )

    # 1. Validate .claude-plugin/plugin.json
    plugin_json_path = dist_path / ".claude-plugin" / "plugin.json"
    if not plugin_json_path.exists():
        result.errors.append("plugin.json not found at .claude-plugin/plugin.json")
        return result

    try:
        plugin_data = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        result.errors.append("plugin.json is not valid JSON")
        return result

    for required_field in ["name", "version", "description"]:
        if required_field not in plugin_data:
            result.errors.append(
                f"plugin.json missing required field '{required_field}'"
            )

    # 2. Validate skills: every directory in skills/ has a valid SKILL.md
    skills_dir = dist_path / "skills"
    core_skill_names = _core_skill_names(dist_path)
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                result.errors.append(
                    f"Skill '{skill_dir.name}' directory has no SKILL.md"
                )
                continue

            is_core_skill = skill_dir.name in core_skill_names
            skill_md_text = skill_md.read_text(encoding="utf-8")

            if is_core_skill:
                line_count = len(skill_md_text.splitlines())
                if (
                    line_count > SKILL_LINE_CAP
                    and skill_dir.name not in SKILL_LINE_CAP_ALLOWLIST
                ):
                    result.errors.append(
                        f"Skill '{skill_dir.name}/SKILL.md' has {line_count} "
                        f"lines, exceeding the {SKILL_LINE_CAP}-line cap"
                    )

            frontmatter = _parse_frontmatter(skill_md_text)
            if frontmatter is None:
                result.errors.append(
                    f"Skill '{skill_dir.name}/SKILL.md' has no valid frontmatter"
                )
                continue

            for req_field in ["name", "description"]:
                if req_field not in frontmatter or not frontmatter.get(req_field):
                    result.errors.append(
                        f"Skill '{skill_dir.name}/SKILL.md' missing required "
                        f"field '{req_field}'"
                    )

            if is_core_skill:
                extra_keys = sorted(set(frontmatter) - _SKILL_FRONTMATTER_ALLOWED_KEYS)
                if extra_keys:
                    result.errors.append(
                        f"Skill '{skill_dir.name}/SKILL.md' frontmatter has "
                        f"unexpected keys {extra_keys} (only 'name' and "
                        "'description' allowed)"
                    )

                references_dir = skill_dir / "references"
                if references_dir.exists():
                    for entry in references_dir.rglob("*"):
                        if entry.is_dir():
                            result.errors.append(
                                f"Skill '{skill_dir.name}/references' has "
                                f"nested directory '{entry.relative_to(skill_dir)}' "
                                "— references must be one level deep"
                            )

    # 3. Validate agents: every directory in agents/ has a valid AGENT.md
    agents_dir = dist_path / "agents"
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

            frontmatter = _parse_frontmatter(agent_md.read_text(encoding="utf-8"))
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
            if role and role not in VALID_ROLES:
                valid = ", ".join(repr(r) for r in VALID_ROLES)
                result.errors.append(
                    f"Agent '{agent_dir.name}/AGENT.md' has invalid role "
                    f"'{role}' (must be one of {valid})"
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
                    if not skills_dir.exists() or not (skills_dir / skill_ref).is_dir():
                        result.errors.append(
                            f"Agent '{agent_dir.name}/AGENT.md' references skill "
                            f"'{skill_ref}' in skills.add but skill not found "
                            f"in skills/"
                        )

    # 4. Validate hooks: hooks.json references scripts that exist in hooks/scripts/
    hooks_json_path = dist_path / "hooks" / "hooks.json"
    if hooks_json_path.exists():
        try:
            hooks_data = json.loads(hooks_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            result.errors.append("hooks/hooks.json is not valid JSON")
            hooks_data = {}

        hooks_scripts_dir = dist_path / "hooks" / "scripts"
        for hook_type, hook_entries in hooks_data.get("hooks", {}).items():
            for entry in hook_entries:
                for hook in entry.get("hooks", []):
                    command = hook.get("command", "")
                    # Extract script filename from $CLAUDE_PLUGIN_ROOT/hooks/scripts/<file>
                    hook_match = re.search(r'hooks/scripts/([^\s"]+)', command)
                    if hook_match:
                        script_name = hook_match.group(1)
                        if not (hooks_scripts_dir / script_name).exists():
                            result.errors.append(
                                f"Hook script '{script_name}' referenced in "
                                f"hooks.json but not found in hooks/scripts/"
                            )

    # 5. Validate intra-skill reference links in SKILL.md files
    if skills_dir.exists():
        result.errors.extend(_validate_doc_links(skills_dir, "SKILL.md", "Skill"))

    # 5b. Validate intra-agent reference links in AGENT.md files
    if agents_dir.exists():
        result.errors.extend(_validate_doc_links(agents_dir, "AGENT.md", "Agent"))

    # 6. Validate settings.json is valid JSON
    settings_path = dist_path / "settings.json"
    if settings_path.exists():
        try:
            json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            result.errors.append("settings.json is not valid JSON")

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
        print(f"PASS: plugin '{preset_name}' is internally consistent")
    else:
        print(f"FAIL: plugin '{preset_name}' has {len(result.errors)} error(s):")
        for error in result.errors:
            print(f"  - {error}")
        sys.exit(1)
