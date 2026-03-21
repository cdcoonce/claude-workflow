"""Assemble a Claude config preset from core + delta.

Build order (D16):
1. Copy all core/skills/ -> dist/<preset>/.claude/skills/
2. Copy all core/docs/ -> dist/<preset>/.claude/docs/
3. Copy core hooks listed in manifest -> dist/<preset>/.claude/hooks/
4. Copy preset-specific skills (overrides core on collision, D17)
5. Copy preset-specific hooks
6. Merge settings-base.json + settings-preset.json -> .claude/settings.json (D13)
7. Concatenate CLAUDE-base.md + CLAUDE-preset.md -> CLAUDE.md (D12)
8. Apply exclusions from manifest (D11)
9. Write .template-version (D25)
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


class BuildValidationError(Exception):
    """Raised when manifest validation fails."""


def _get_version() -> str:
    """Get current git tag or short commit hash for .template-version (D25)."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _validate_manifest(
    manifest: dict,
    core_path: Path,
    preset_path: Path,
) -> None:
    """Validate all manifest references exist. Fail fast if not (D19)."""
    errors: list[str] = []

    for hook_name in manifest["core"].get("hooks", []):
        if not (core_path / "hooks" / hook_name).exists():
            errors.append(f"Core hook not found: {hook_name}")

    for skill_name in manifest.get("preset_skills", []):
        if not (preset_path / "skills" / skill_name).exists():
            errors.append(f"Preset skill not found: {skill_name}")

    for hook_name in manifest.get("preset_hooks", []):
        if not (preset_path / "hooks" / hook_name).exists():
            errors.append(f"Preset hook not found: {hook_name}")

    preset_skill_names = {f"skills/{s}" for s in manifest.get("preset_skills", [])}
    excluded = set(manifest.get("exclude", []))
    conflicts = preset_skill_names & excluded
    if conflicts:
        errors.append(
            f"Skills in both preset_skills and exclude: {', '.join(conflicts)}. "
            f"A preset override cannot also be excluded."
        )

    if errors:
        raise BuildValidationError(
            "Manifest validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )


def _merge_settings(base_path: Path, preset_path: Path) -> dict:
    """Shallow-merge base + preset settings. Preset hook arrays append to base (D13)."""
    base = json.loads(base_path.read_text())
    preset = json.loads(preset_path.read_text())

    merged = json.loads(json.dumps(base))

    for hook_type, hook_list in preset.get("hooks", {}).items():
        if hook_type in merged.get("hooks", {}):
            merged["hooks"][hook_type].extend(hook_list)
        else:
            merged.setdefault("hooks", {})[hook_type] = hook_list

    return merged


def build_preset(preset_name: str, *, repo_root: Path | None = None) -> Path:
    """Build a preset into dist/<preset_name>/.

    Parameters
    ----------
    preset_name
        Name of the preset directory under presets/.
    repo_root
        Root of the template repo. Defaults to current working directory.

    Returns
    -------
    Path
        Path to the built output directory.
    """
    root = repo_root or Path.cwd()
    core_path = root / "core"
    preset_path = root / "presets" / preset_name
    dist_path = root / "dist" / preset_name
    claude_dir = dist_path / ".claude"

    if not preset_path.exists():
        raise BuildValidationError(
            f"Preset '{preset_name}' not found at {preset_path}"
        )

    manifest = json.loads((preset_path / "manifest.json").read_text())
    _validate_manifest(manifest, core_path, preset_path)

    if dist_path.exists():
        shutil.rmtree(dist_path)
    claude_dir.mkdir(parents=True)

    if manifest["core"].get("skills") == "all":
        shutil.copytree(core_path / "skills", claude_dir / "skills")

    if manifest["core"].get("docs") == "all":
        shutil.copytree(core_path / "docs", claude_dir / "docs")

    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    for hook_name in manifest["core"].get("hooks", []):
        shutil.copy2(core_path / "hooks" / hook_name, hooks_dir / hook_name)

    for skill_name in manifest.get("preset_skills", []):
        src = preset_path / "skills" / skill_name
        dest = claude_dir / "skills" / skill_name
        if dest.exists():
            print(f"WARNING: preset skill '{skill_name}' overrides core skill '{skill_name}'")
            shutil.rmtree(dest)
        shutil.copytree(src, dest)

    for hook_name in manifest.get("preset_hooks", []):
        shutil.copy2(preset_path / "hooks" / hook_name, hooks_dir / hook_name)

    merged_settings = _merge_settings(
        core_path / "settings-base.json",
        preset_path / "settings-preset.json",
    )
    (claude_dir / "settings.json").write_text(
        json.dumps(merged_settings, indent=2) + "\n"
    )

    base_md = (core_path / "CLAUDE-base.md").read_text()
    preset_md = (preset_path / "CLAUDE-preset.md").read_text()
    (dist_path / "CLAUDE.md").write_text(base_md + preset_md)

    for exclusion in manifest.get("exclude", []):
        excluded_path = claude_dir / exclusion
        if excluded_path.exists():
            if excluded_path.is_dir():
                shutil.rmtree(excluded_path)
            else:
                excluded_path.unlink()

    (claude_dir / ".template-version").write_text(_get_version() + "\n")

    return dist_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run python scripts/build_preset.py <preset_name>")
        sys.exit(1)

    preset = sys.argv[1]
    output = build_preset(preset)
    print(f"\nBuilt preset '{preset}' -> {output}/")
    print(f"  {output}/.claude/")
    print(f"  {output}/CLAUDE.md")
    print(f"\nCopy to your project:")
    print(f"  cp -r {output}/.claude /path/to/your/project/")
    print(f"  cp {output}/CLAUDE.md /path/to/your/project/")
