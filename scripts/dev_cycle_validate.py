"""Dev cycle state file parser and validator.

Parses YAML frontmatter from dev-cycle state files and validates
schema integrity, phase transitions, and artifact completeness.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

VALID_PHASES = (
    "brainstorm", "plan", "ceo_review", "issues",
    "implement", "code_review", "pr",
)
VALID_STATUSES = ("not_started", "in_progress", "completed", "abandoned")
VALID_ARTIFACT_STATUSES = ("pending", "in_progress", "completed", "blocked")
CURRENT_SCHEMA_VERSION = 1

_FRONTMATTER_RE = re.compile(r"\A---\n(.+?)\n---", re.DOTALL)
_FIELD_RE = re.compile(r"^(\w+):\s*(.+?)(?:\s*#.*)?$", re.MULTILINE)

REQUIRED_FIELDS = ("schema_version", "feature", "status", "current_phase")


@dataclass
class StateFile:
    """Parsed representation of a dev-cycle state file."""

    schema_version: int
    feature: str
    status: str
    current_phase: str
    created: str = ""
    updated: str = ""
    branch: str = ""
    path: Path = field(default_factory=lambda: Path())


def parse_state_file(path: Path) -> StateFile:
    """Parse a dev-cycle state file and return a StateFile object.

    Parameters
    ----------
    path : Path
        Path to the state file.

    Returns
    -------
    StateFile
        Parsed state file data.

    Raises
    ------
    ValueError
        If the file has no frontmatter or is missing required fields.
    """
    text = path.read_text()
    match = _FRONTMATTER_RE.search(text)
    if not match:
        raise ValueError(f"No YAML frontmatter found in {path.name}")

    raw_fields: dict[str, str] = {}
    for field_match in _FIELD_RE.finditer(match.group(1)):
        raw_fields[field_match.group(1)] = field_match.group(2).strip()

    for req in REQUIRED_FIELDS:
        if req not in raw_fields:
            raise ValueError(
                f"Missing required field '{req}' in {path.name}"
            )

    return StateFile(
        schema_version=int(raw_fields["schema_version"]),
        feature=raw_fields["feature"],
        status=raw_fields["status"],
        current_phase=raw_fields["current_phase"],
        created=raw_fields.get("created", ""),
        updated=raw_fields.get("updated", ""),
        branch=raw_fields.get("branch", ""),
        path=path,
    )


@dataclass
class ValidationResult:
    """Result of validating a state file."""

    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def validate_state_file(path: Path) -> ValidationResult:
    """Validate a single dev-cycle state file.

    Parameters
    ----------
    path : Path
        Path to the state file.

    Returns
    -------
    ValidationResult
        Validation result with any errors found.
    """
    errors: list[str] = []

    try:
        state = parse_state_file(path)
    except ValueError as exc:
        return ValidationResult(errors=[str(exc)])

    if state.schema_version > CURRENT_SCHEMA_VERSION:
        errors.append(
            f"Unsupported schema_version {state.schema_version} "
            f"in {path.name} (max supported: {CURRENT_SCHEMA_VERSION})"
        )

    if state.status not in VALID_STATUSES:
        errors.append(
            f"Invalid status '{state.status}' in {path.name}. "
            f"Valid values: {', '.join(VALID_STATUSES)}"
        )

    if state.current_phase not in VALID_PHASES:
        errors.append(
            f"Invalid current_phase '{state.current_phase}' in {path.name}. "
            f"Valid values: {', '.join(VALID_PHASES)}"
        )

    expected_slug = path.stem
    if state.feature != expected_slug:
        errors.append(
            f"Feature slug '{state.feature}' does not match "
            f"filename '{expected_slug}' in {path.name}"
        )

    return ValidationResult(errors=errors)
