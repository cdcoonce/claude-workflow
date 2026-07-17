"""Validate internal consistency of a built plugin.

Checks:
- .claude-plugin/plugin.json exists with required fields (name, version, description)
- Every directory in skills/ has a SKILL.md
- Every directory in agents/ has a valid AGENT.md (frontmatter with name, description, role)
- Agent names match their directory names
- Agent roles are one of the documented roles (see VALID_ROLES)
- Agent skills.add references resolve to existing skills in skills/
- hooks/hooks.json references scripts that exist in hooks/scripts/
- Every relative link or backtick-quoted path in bundled skill/agent docs
  resolves within that skill/agent directory
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

# Matches a backtick-quoted inline token, e.g. `references/foo.md`.
_BACKTICK_PATTERN = re.compile(r"`([^`\n]+)`")


def _fenced_line_numbers(doc_content: str) -> set[int]:
    """Return line numbers of doc_content that fall inside a ``` fenced code block."""
    in_fence = False
    fenced_lines: set[int] = set()
    for line_num, line in enumerate(doc_content.split("\n")):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            fenced_lines.add(line_num)
    return fenced_lines


def _is_out_of_contract(target: str) -> bool:
    """Return True for anchors, project-root-relative paths, and URI-scheme targets."""
    return target.startswith(_LINK_SKIP_PREFIXES) or bool(
        _URI_SCHEME_PATTERN.match(target)
    )


def _backtick_reference_target(doc_md: Path, raw_token: str) -> str | None:
    """Resolve a backtick-quoted token to a validate-able relative ``.md`` path.

    Applies the scoping contract that separates genuine intra-skill doc
    references from incidental backtick mentions: the token must parse as a
    relative path ending in ``.md`` with no URI scheme and no skip-prefix, and
    its first path segment must exist as a directory alongside ``doc_md``.
    Bare basenames, root-relative mentions, and illustrative example paths
    fail this check and are skipped.

    Parameters
    ----------
    doc_md
        The doc file the token was found in, used to resolve the reference.
    raw_token
        The raw text found between a pair of backticks.

    Returns
    -------
    str | None
        The path portion of the token (query/fragment stripped), or None if
        the token is out of contract and should be skipped.
    """
    target = raw_token.strip()
    if "/" not in target or _is_out_of_contract(target):
        return None
    file_part = re.split(r"[#?]", target, maxsplit=1)[0]
    if not file_part.endswith(".md"):
        return None
    first_segment = file_part.split("/", 1)[0]
    if not first_segment or not (doc_md.parent / first_segment).is_dir():
        return None
    return file_part


def _validate_doc_links(docs_dir: Path, doc_filename: str, label: str) -> list[str]:
    """Validate that relative references in bundled docs resolve to existing files.

    Scans every ``.md`` file bundled alongside each ``doc_filename`` (not just
    ``doc_filename`` itself), checking both markdown-style links
    (``[text](path)``) and in-contract backtick-quoted paths (see
    ``_backtick_reference_target``).

    Parameters
    ----------
    docs_dir
        Root directory to search recursively for doc files (e.g., skills/).
    doc_filename
        Name of the primary doc file that marks a skill/agent directory
        (e.g., "SKILL.md").
    label
        Human-readable label used in error messages (e.g., "Skill").

    Returns
    -------
    list[str]
        Error strings for any references that fail to resolve.
    """
    errors: list[str] = []
    for primary_doc in docs_dir.rglob(doc_filename):
        item_dir = primary_doc.parent
        for doc_md in sorted(item_dir.rglob("*.md")):
            doc_content = doc_md.read_text(encoding="utf-8")
            fenced_lines = _fenced_line_numbers(doc_content)
            doc_rel = doc_md.relative_to(item_dir.parent).as_posix()

            for match in _LINK_PATTERN.finditer(doc_content):
                line_num = doc_content.count("\n", 0, match.start())
                if line_num in fenced_lines:
                    continue
                link_target = match.group(2).strip()
                # Strip an optional markdown link title — [text](path "Title") —
                # keeping only the path token. Skip when the path is
                # quote-wrapped, since such a path may legitimately contain
                # spaces.
                if link_target and not link_target.startswith(("'", '"')):
                    link_target = link_target.split(None, 1)[0]
                if not link_target or _is_out_of_contract(link_target):
                    continue
                file_part = re.split(r"[#?]", link_target, maxsplit=1)[0]
                if not file_part:
                    continue
                resolved = (doc_md.parent / file_part).resolve()
                if not resolved.exists():
                    errors.append(
                        f"{label} '{doc_rel}' links to '{file_part}' but file not found"
                    )

            for match in _BACKTICK_PATTERN.finditer(doc_content):
                line_num = doc_content.count("\n", 0, match.start())
                if line_num in fenced_lines:
                    continue
                file_part = _backtick_reference_target(doc_md, match.group(1))
                if file_part is None:
                    continue
                resolved = (doc_md.parent / file_part).resolve()
                if not resolved.exists():
                    errors.append(
                        f"{label} '{doc_rel}' references "
                        f"'{file_part}' but file not found"
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

            frontmatter = _parse_frontmatter(skill_md.read_text(encoding="utf-8"))
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
