from __future__ import annotations

from pathlib import Path

from scripts.installer.bundle import Bundle
from scripts.installer.report import InstallReport, Scope


class AgentAdapter:
    """Installs an agent-agnostic Bundle into one coding agent's world.

    Subclasses implement the agent-specific placement and report any bundle
    capability they cannot support (never a silent half-install)."""

    name: str = ""

    def detect(self, target: Path) -> bool:
        raise NotImplementedError

    def install(self, bundle: Bundle, target: Path, scope: Scope) -> InstallReport:
        raise NotImplementedError

    def uninstall(self, target: Path, preset: str) -> InstallReport:
        raise NotImplementedError


# Registry — adding Cursor/Gemini/Cortex later is a new class + one entry here.
_ADAPTERS: dict[str, AgentAdapter] = {}


def register(adapter: AgentAdapter) -> None:
    _ADAPTERS[adapter.name] = adapter


def get_adapter(name: str) -> AgentAdapter:
    return _ADAPTERS[name]


def adapter_names() -> list[str]:
    return sorted(_ADAPTERS)


def detect_adapter(target: Path) -> AgentAdapter | None:
    for name in adapter_names():
        if _ADAPTERS[name].detect(target):
            return _ADAPTERS[name]
    return None
