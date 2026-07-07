from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Scope(str, Enum):
    PROJECT = "project"
    USER = "user"


@dataclass
class InstallReport:
    """What an adapter did: items installed, and items skipped with a reason
    (a capability the target agent does not support). Never a silent half-install."""

    agent: str
    preset: str
    installed: list[str] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)

    def add_installed(self, item: str) -> None:
        self.installed.append(item)

    def add_skipped(self, item: str, reason: str) -> None:
        self.skipped.append((item, reason))
