#!/usr/bin/env python3
"""SessionStart hook: move a persona's local/ out of the versioned plugin cache.

`claude plugin install` caches plugins at `<cache>/<marketplace>/<preset>/<version>/`,
and an update writes a *sibling* version directory rather than reusing one. An
owner's `local/` — tuning, preferences, and the private memory vault — therefore
does not travel: it stays in the old version dir while the new install starts
empty. Preserving it across a same-destination reinstall does not help, because
the plugin cache never reuses a destination.

So it does not live there. The canonical location is
`~/.workshop/personas/<preset>/`, outside the cache entirely, per the
machine-local convention in CLAUDE.md. This hook performs the one-time move for
owners who already have data in a version dir.

SessionStart cannot block and runs on every session — including resume, clear,
and compact — so this exits 0 always and short-circuits on a single `exists()`
check once migration has happened.

It COPIES and never deletes. `local/` is gitignored by construction, so it is
the owner's only copy; a half-finished move would destroy months of accumulated
memory with no backup anywhere. The original is left in place with a pointer
file, and an already-populated destination is never overwritten — live data
outranks whatever a stale version dir still holds.
"""

import json
import shutil
import sys
from pathlib import Path

LOCAL = "local"
POINTER = "MIGRATED.md"

try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    sys.exit(0)  # Fail open: an unparseable payload asks nothing of us.

if not isinstance(data, dict):
    sys.exit(0)


def version_key(directory: Path):
    """Sort key for a version dir name, numeric where it parses.

    `0.1.10` must sort above `0.1.2`; a lexical sort gets that backwards.
    Anything unparseable sorts lowest rather than raising.
    """
    parts = []
    for chunk in directory.name.split("."):
        parts.append(int(chunk) if chunk.isdigit() else -1)
    return parts


def installed_layout(script: Path):
    """(preset_dir, version_dir) when running from a plugin cache, else None.

    SessionStart carries no plugin-root field, so location comes from __file__:
    `<preset>/<version>/hooks/scripts/<this>.py`.
    """
    try:
        resolved = script.resolve()
        scripts_dir = resolved.parent
        version_dir = scripts_dir.parent.parent
        preset_dir = version_dir.parent
    except OSError:
        return None
    if scripts_dir.name != "scripts" or scripts_dir.parent.name != "hooks":
        return None
    if not preset_dir.is_dir():
        return None
    return preset_dir, version_dir


def newest_overlay(preset_dir: Path, current: Path):
    """The `local/` worth migrating: newest version dir that has real content.

    An owner who has updated a few times has stale copies in older dirs; the
    newest wins. The current version dir is preferred when it has one.
    """
    candidates = []
    try:
        siblings = [d for d in preset_dir.iterdir() if d.is_dir()]
    except OSError:
        return None
    for version_dir in siblings:
        overlay = version_dir / LOCAL
        if not overlay.is_dir():
            continue
        try:
            has_content = any(
                p.is_file() and p.name != POINTER for p in overlay.rglob("*")
            )
        except OSError:
            continue
        if has_content:
            candidates.append(version_dir)
    if not candidates:
        return None
    if current in candidates:
        return current / LOCAL
    return max(candidates, key=version_key) / LOCAL


layout = installed_layout(Path(__file__))
if layout is None:
    sys.exit(0)

preset_dir, version_dir = layout
destination = Path.home() / ".workshop" / "personas" / preset_dir.name

try:
    # Fast path, and the common one: already migrated. Never overwrite live
    # data with a stale cached copy.
    if destination.exists():
        sys.exit(0)
except OSError:
    sys.exit(0)

source = newest_overlay(preset_dir, version_dir)
if source is None:
    sys.exit(0)

try:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
except (OSError, shutil.Error):
    # Leave the original untouched and try again next session.
    shutil.rmtree(destination, ignore_errors=True)
    sys.exit(0)

try:
    (source / POINTER).write_text(
        "This copy is no longer read.\n\n"
        f"Your tuning, preferences, and memory now live at:\n\n    {destination}\n\n"
        "They were copied there so plugin updates stop stranding them in an old\n"
        "version directory. This directory is kept as a backup and can be deleted\n"
        "once you have confirmed the new location looks right.\n",
        encoding="utf-8",
    )
except OSError:
    pass

print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": (
                    f"Persona storage moved: {preset_dir.name}'s tuning, preferences "
                    f"and memory now live at {destination}, outside the versioned "
                    "plugin cache, so plugin updates no longer strand them. The "
                    f"previous copy is kept at {source} as a backup. If the owner "
                    "asks where their memory went, tell them this."
                ),
            }
        }
    )
)
sys.exit(0)
