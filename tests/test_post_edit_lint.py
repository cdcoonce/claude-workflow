"""Tests for the post-edit-lint hooks' npx invocations.

The hooks are stdin-driven subprocess scripts: they read a JSON payload from
stdin and shell out to formatters/linters. Driving them as real subprocesses
(with a fake `npx` on PATH) exercises the actual argv passed to npx, which is
what matters here -- npx must be called with --no-install so it never tries
to download a missing tool from the network.
"""

from __future__ import annotations

import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FULL_STACK_HOOK = REPO_ROOT / "presets" / "full-stack" / "hooks" / "post-edit-lint.py"
CLAUDE_TOOLING_HOOK = (
    REPO_ROOT / "presets" / "claude-tooling" / "hooks" / "post-edit-lint.py"
)

FAKE_NPX_SCRIPT = """#!/bin/sh
echo "$@" >> "$NPX_LOG"
exit 0
"""

# Mirrors real npx: with --no-install and no locally-installed package, it
# exits non-zero instead of downloading. Without --no-install it would try to
# fetch the package from the network -- that's exactly the behavior this fix
# prevents, so the fake enforces the flag's presence.
FAKE_NPX_NO_INSTALL_SCRIPT = """#!/bin/sh
case "$*" in
  *--no-install*) exit 1 ;;
  *) echo "$@" >> "$NPX_LOG"; exit 0 ;;
esac
"""


def _write_fake_npx(bin_dir: Path, script: str) -> None:
    npx_path = bin_dir / "npx"
    npx_path.write_text(script)
    npx_path.chmod(npx_path.stat().st_mode | stat.S_IEXEC)


def _make_fake_npx(bin_dir: Path) -> None:
    _write_fake_npx(bin_dir, FAKE_NPX_SCRIPT)


def run_hook(
    hook_path: Path, file_path: str, path_dir: Path, npx_log: Path
) -> subprocess.CompletedProcess[str]:
    """Invoke the hook as a subprocess with a controlled PATH and npx log."""
    env = {"PATH": str(path_dir), "NPX_LOG": str(npx_log)}
    return subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps({"tool_input": {"file_path": file_path}}),
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture
def fake_npx_bin(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _make_fake_npx(bin_dir)
    return bin_dir


@pytest.fixture
def no_npx_bin(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "empty-bin"
    bin_dir.mkdir()
    return bin_dir


@pytest.fixture
def uninstalled_tool_npx_bin(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "uninstalled-bin"
    bin_dir.mkdir()
    _write_fake_npx(bin_dir, FAKE_NPX_NO_INSTALL_SCRIPT)
    return bin_dir


class TestNpxInstalled:
    """When npx tools are present on PATH, formatting still runs with --no-install."""

    def test_full_stack_prettier_gets_no_install(
        self, fake_npx_bin: Path, tmp_path: Path
    ) -> None:
        log = tmp_path / "calls.log"
        result = run_hook(FULL_STACK_HOOK, "app.ts", fake_npx_bin, log)

        assert result.returncode == 0
        assert "prettier" in result.stderr
        calls = log.read_text().splitlines()
        assert any("--no-install" in call and "prettier" in call for call in calls)

    def test_full_stack_eslint_gets_no_install(
        self, fake_npx_bin: Path, tmp_path: Path
    ) -> None:
        log = tmp_path / "calls.log"
        result = run_hook(FULL_STACK_HOOK, "app.ts", fake_npx_bin, log)

        assert result.returncode == 0
        assert "eslint" in result.stderr
        calls = log.read_text().splitlines()
        assert any("--no-install" in call and "eslint" in call for call in calls)

    def test_full_stack_stylelint_gets_no_install(
        self, fake_npx_bin: Path, tmp_path: Path
    ) -> None:
        log = tmp_path / "calls.log"
        result = run_hook(FULL_STACK_HOOK, "styles.css", fake_npx_bin, log)

        assert result.returncode == 0
        assert "stylelint" in result.stderr
        calls = log.read_text().splitlines()
        assert any("--no-install" in call and "stylelint" in call for call in calls)

    def test_claude_tooling_prettier_gets_no_install(
        self, fake_npx_bin: Path, tmp_path: Path
    ) -> None:
        log = tmp_path / "calls.log"
        result = run_hook(CLAUDE_TOOLING_HOOK, "README.md", fake_npx_bin, log)

        assert result.returncode == 0
        assert "prettier" in result.stderr
        calls = log.read_text().splitlines()
        assert any("--no-install" in call and "prettier" in call for call in calls)


class TestNpxMissing:
    """When the npx-backed tool is unavailable, the hook records no action."""

    def test_full_stack_records_no_action_without_npx(
        self, no_npx_bin: Path, tmp_path: Path
    ) -> None:
        log = tmp_path / "calls.log"
        result = run_hook(FULL_STACK_HOOK, "app.ts", no_npx_bin, log)

        assert result.returncode == 0
        assert result.stderr == ""
        assert not log.exists()

    def test_claude_tooling_records_no_action_without_npx(
        self, no_npx_bin: Path, tmp_path: Path
    ) -> None:
        log = tmp_path / "calls.log"
        result = run_hook(CLAUDE_TOOLING_HOOK, "README.md", no_npx_bin, log)

        assert result.returncode == 0
        assert result.stderr == ""
        assert not log.exists()


class TestNpxToolNotLocallyInstalled:
    """--no-install makes npx exit non-zero (not download) when the tool is missing."""

    def test_full_stack_records_no_action_when_tool_uninstalled(
        self, uninstalled_tool_npx_bin: Path, tmp_path: Path
    ) -> None:
        log = tmp_path / "calls.log"
        result = run_hook(FULL_STACK_HOOK, "app.ts", uninstalled_tool_npx_bin, log)

        assert result.returncode == 0
        assert result.stderr == ""
        assert not log.exists()

    def test_claude_tooling_records_no_action_when_tool_uninstalled(
        self, uninstalled_tool_npx_bin: Path, tmp_path: Path
    ) -> None:
        log = tmp_path / "calls.log"
        result = run_hook(
            CLAUDE_TOOLING_HOOK, "README.md", uninstalled_tool_npx_bin, log
        )

        assert result.returncode == 0
        assert result.stderr == ""
        assert not log.exists()
