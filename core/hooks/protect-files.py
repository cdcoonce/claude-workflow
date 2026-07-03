#!/usr/bin/env python3
"""Pre-edit hook: block edits to sensitive/generated files."""

import json
import sys
from pathlib import PurePath

data = json.load(sys.stdin)
file_path = data.get("tool_input", {}).get("file_path", "")

if not file_path:
    sys.exit(0)

PROTECTED_DIRS = ["node_modules", ".git"]
PROTECTED_FILES = ["package-lock.json", "uv.lock"]
ENV_PREFIX = ".env"

path = PurePath(file_path)
basename = path.name

matched_pattern = None

for directory in PROTECTED_DIRS:
    if directory in path.parts:
        matched_pattern = f"{directory}/"
        break

if matched_pattern is None:
    for filename in PROTECTED_FILES:
        if basename == filename:
            matched_pattern = filename
            break

if matched_pattern is None and basename.startswith(ENV_PREFIX):
    matched_pattern = ENV_PREFIX

if matched_pattern:
    print(
        f"Blocked: {file_path} matches protected pattern '{matched_pattern}'",
        file=sys.stderr,
    )
    sys.exit(2)
