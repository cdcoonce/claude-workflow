from __future__ import annotations

from pathlib import Path


class BundleError(Exception):
    """Raised when a preset bundle is missing or malformed."""


class Bundle:
    """A built preset on disk: a complete Claude Code plugin directory
    (`<presets_root>/<name>/` containing `.claude-plugin/plugin.json`)."""

    def __init__(self, name: str, path: Path) -> None:
        self.name = name
        self.path = path

    @staticmethod
    def _is_preset(path: Path) -> bool:
        return (path / ".claude-plugin" / "plugin.json").is_file()

    @classmethod
    def load(cls, presets_root: Path, name: str) -> "Bundle":
        path = presets_root / name
        if not cls._is_preset(path):
            raise BundleError(
                f"preset {name!r} not found under {presets_root} "
                "(no .claude-plugin/plugin.json)"
            )
        return cls(name, path)

    @classmethod
    def available(cls, presets_root: Path) -> list[str]:
        if not presets_root.is_dir():
            return []
        return sorted(p.name for p in presets_root.iterdir() if cls._is_preset(p))
