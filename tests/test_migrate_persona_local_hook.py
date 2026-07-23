"""SessionStart hook: move a persona owner's local/ out of the versioned cache.

`claude plugin install` caches plugins under
`<cache>/<marketplace>/<preset>/<version>/`, and an update creates a *sibling*
version directory rather than reusing one. The owner's `local/` — tuning,
preferences, and the private memory vault — therefore does not travel: it is
left behind in the old version dir and the new install starts empty.

The fix is to keep it outside the cache entirely, at
`~/.workshop/personas/<preset>/`. This hook performs that one-time move for
owners who already have data in a version dir.

It runs on every session, including resume and compact, so the already-migrated
path must be a single cheap check. It copies rather than moves and never
deletes: `local/` is gitignored by construction, so it is the owner's only copy.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_SOURCE = REPO_ROOT / "core" / "hooks" / "migrate-persona-local.py"


def _installed_hook(cache: Path, preset: str, version: str) -> Path:
    """Place the hook where the plugin cache would, so __file__ resolves."""
    scripts = cache / "the-workshop" / preset / version / "hooks" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    installed = scripts / HOOK_SOURCE.name
    installed.write_text(HOOK_SOURCE.read_text(), encoding="utf-8")
    return installed


def _seed_local(version_dir: Path, marker: str) -> dict[str, str]:
    files = {
        "tuning.md": f"# Tuning\n\n{marker}\n",
        "preferences.md": f"# Preferences\n\n{marker}\n",
        "memory/MEMORY.md": f"- [note](notes/a.md) {marker}\n",
        "memory/notes/a.md": f"Long-accumulated context. {marker}\n",
    }
    for relative, text in files.items():
        path = version_dir / "local" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return files


def run(hook: Path, home: Path, payload: object) -> subprocess.CompletedProcess[str]:
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(hook)],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=30,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
    )


@pytest.fixture
def home(tmp_path: Path) -> Path:
    target = tmp_path / "home"
    target.mkdir()
    return target


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    return tmp_path / "cache"


def _destination(home: Path, preset: str) -> Path:
    return home / ".workshop" / "personas" / preset


class TestMigration:
    def test_local_is_copied_out_of_the_version_dir(
        self, home: Path, cache: Path
    ) -> None:
        hook = _installed_hook(cache, "advisor-product-design", "0.1.2")
        version_dir = hook.parents[2]
        files = _seed_local(version_dir, "kathy")

        result = run(hook, home, {"hook_event_name": "SessionStart", "source": "startup"})

        assert result.returncode == 0
        destination = _destination(home, "advisor-product-design")
        for relative, text in files.items():
            assert (destination / relative).read_text() == text

    def test_the_owners_original_copy_is_never_deleted(
        self, home: Path, cache: Path
    ) -> None:
        """local/ is gitignored by construction — this is their only copy."""
        hook = _installed_hook(cache, "advisor-product-design", "0.1.2")
        version_dir = hook.parents[2]
        _seed_local(version_dir, "kathy")

        run(hook, home, {"hook_event_name": "SessionStart", "source": "startup"})

        assert (version_dir / "local" / "tuning.md").exists()
        assert (version_dir / "local" / "memory" / "notes" / "a.md").exists()

    def test_a_pointer_is_left_behind_so_the_old_copy_is_not_a_mystery(
        self, home: Path, cache: Path
    ) -> None:
        hook = _installed_hook(cache, "advisor-product-design", "0.1.2")
        version_dir = hook.parents[2]
        _seed_local(version_dir, "kathy")

        run(hook, home, {"hook_event_name": "SessionStart", "source": "startup"})

        pointer = version_dir / "local" / "MIGRATED.md"
        assert pointer.exists()
        assert str(_destination(home, "advisor-product-design")) in pointer.read_text()

    def test_newest_version_wins_when_several_version_dirs_have_local(
        self, home: Path, cache: Path
    ) -> None:
        """An owner who has updated a few times has stale copies in old dirs."""
        old = _installed_hook(cache, "advisor-product-design", "0.1.0")
        _seed_local(old.parents[2], "stale")
        current = _installed_hook(cache, "advisor-product-design", "0.1.10")
        _seed_local(current.parents[2], "current")

        run(current, home, {"hook_event_name": "SessionStart", "source": "startup"})

        tuning = _destination(home, "advisor-product-design") / "tuning.md"
        assert "current" in tuning.read_text()

    def test_already_migrated_is_left_alone(self, home: Path, cache: Path) -> None:
        """The owner's live data must never be overwritten by a stale version dir."""
        hook = _installed_hook(cache, "advisor-product-design", "0.1.2")
        _seed_local(hook.parents[2], "stale-in-cache")
        destination = _destination(home, "advisor-product-design")
        destination.mkdir(parents=True)
        (destination / "tuning.md").write_text("# Tuning\n\nlive edits\n")

        result = run(hook, home, {"hook_event_name": "SessionStart", "source": "startup"})

        assert result.returncode == 0
        assert (destination / "tuning.md").read_text() == "# Tuning\n\nlive edits\n"

    def test_running_twice_changes_nothing(self, home: Path, cache: Path) -> None:
        hook = _installed_hook(cache, "advisor-product-design", "0.1.2")
        _seed_local(hook.parents[2], "kathy")
        payload = {"hook_event_name": "SessionStart", "source": "startup"}

        run(hook, home, payload)
        first = (_destination(home, "advisor-product-design") / "tuning.md").read_text()
        second_result = run(hook, home, payload)

        assert second_result.returncode == 0
        assert (
            _destination(home, "advisor-product-design") / "tuning.md"
        ).read_text() == first

    def test_nothing_to_migrate_is_silent(self, home: Path, cache: Path) -> None:
        """Most sessions have nothing to do; they must not inject context noise."""
        hook = _installed_hook(cache, "advisor-product-design", "0.1.2")

        result = run(hook, home, {"hook_event_name": "SessionStart", "source": "startup"})

        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_the_owner_is_told_where_their_memory_went(
        self, home: Path, cache: Path
    ) -> None:
        """A silent move of someone's private memory is worse than no move."""
        hook = _installed_hook(cache, "advisor-product-design", "0.1.2")
        _seed_local(hook.parents[2], "kathy")

        result = run(hook, home, {"hook_event_name": "SessionStart", "source": "startup"})

        payload = json.loads(result.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        assert str(_destination(home, "advisor-product-design")) in context


class TestFailsOpen:
    @pytest.mark.parametrize("payload", ["", "not json", "{ broken", "[]", "null"])
    def test_unusable_stdin(self, home: Path, cache: Path, payload: str) -> None:
        hook = _installed_hook(cache, "advisor-product-design", "0.1.2")

        result = run(hook, home, payload)

        assert result.returncode == 0
        assert "Traceback" not in result.stderr

    def test_hook_outside_a_plugin_cache_layout(self, tmp_path: Path, home: Path) -> None:
        """Run from the repo or anywhere else, there is no persona to migrate."""
        loose = tmp_path / "loose"
        loose.mkdir()
        installed = loose / HOOK_SOURCE.name
        installed.write_text(HOOK_SOURCE.read_text(), encoding="utf-8")

        result = run(installed, home, {"hook_event_name": "SessionStart"})

        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_unreadable_destination_parent_does_not_crash(
        self, home: Path, cache: Path
    ) -> None:
        """A file where the destination directory belongs must not raise."""
        hook = _installed_hook(cache, "advisor-product-design", "0.1.2")
        _seed_local(hook.parents[2], "kathy")
        workshop = home / ".workshop"
        workshop.parent.mkdir(parents=True, exist_ok=True)
        workshop.write_text("not a directory")

        result = run(hook, home, {"hook_event_name": "SessionStart"})

        assert result.returncode == 0
        assert "Traceback" not in result.stderr
