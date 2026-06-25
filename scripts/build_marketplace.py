"""Generate .claude-plugin/marketplace.json from all preset manifests.

Scans presets/ for manifest.json files and produces a single marketplace
index at .claude-plugin/marketplace.json in the repo root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _scan_presets(presets_dir: Path) -> list[dict[str, str]]:
    """Scan *presets_dir* and return one entry per preset that has a manifest.

    Parameters
    ----------
    presets_dir
        Directory containing one sub-directory per preset.

    Returns
    -------
    list[dict[str, str]]
        Unsorted list of plugin descriptor dicts with keys
        ``name``, ``version``, ``description``, and ``source``.
    """
    plugins: list[dict[str, str]] = []
    for preset_dir in sorted(presets_dir.iterdir()):
        if not preset_dir.is_dir():
            continue
        manifest_path = preset_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        plugins.append({
            "name": manifest["name"],
            "version": manifest.get("version", "0.0.0"),
            "description": manifest.get("description", ""),
            "source": f"./dist/{manifest['name']}",
        })
    return plugins


def build_marketplace(repo_root: Path | None = None) -> Path:
    """Generate marketplace.json listing all available plugins.

    Parameters
    ----------
    repo_root
        Root of the template repo. Defaults to current working directory.

    Returns
    -------
    Path
        Path to the generated marketplace.json file.
    """
    root = repo_root or Path.cwd()
    presets_dir = root / "presets"

    plugins = _scan_presets(presets_dir)
    plugins.sort(key=lambda p: p["name"])

    marketplace_dir = root / ".claude-plugin"
    marketplace_dir.mkdir(parents=True, exist_ok=True)

    marketplace = {
        "name": "claude-workflow",
        "owner": {"name": "Charles Coonce"},
        "plugins": plugins,
    }

    marketplace_path = marketplace_dir / "marketplace.json"
    marketplace_path.write_text(
        json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return marketplace_path


if __name__ == "__main__":
    output = build_marketplace()
    print(f"Generated marketplace: {output}")
