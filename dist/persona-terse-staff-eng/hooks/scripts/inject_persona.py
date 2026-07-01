# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""SessionStart hook: inject a persona output-style as additionalContext.

Shipped inside each `persona-*` plugin. On session start Claude Code runs it via
`uv run`; it reads the plugin's single `output-styles/*.md`, strips the YAML
frontmatter, and emits the body as SessionStart `additionalContext` so the persona
is layered on top of the default engineering instructions (purely additive — it
never replaces the base prompt).

Cross-platform by design: pure Python via `uv run`, no bash. Fails safe — any error
prints nothing and exits 0, so a broken persona can never break a session.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _strip_frontmatter(text: str) -> str:
    """Return the markdown body with a leading YAML frontmatter block removed."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text.strip()


def main() -> int:
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if not root:
        return 0  # fail safe: nothing to inject

    styles = sorted(Path(root, "output-styles").glob("*.md"))
    if not styles:
        return 0

    body = _strip_frontmatter(styles[0].read_text(encoding="utf-8"))
    if not body:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": body,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never let a persona hook break a session.
        sys.exit(0)
