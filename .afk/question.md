# Issue #73 — blocked on unrelated pre-existing test failures

## Scoped work: complete

- `scripts/build_preset.py:304` already uses
  `excluded_path.is_relative_to(dist_path.resolve())` instead of the
  fragile `str(excluded_path).startswith(...)` check. This was already
  committed at HEAD (introduced incidentally by commit `b348b704`
  "fix(hooks): portable hook runner for Claude Code, CoCo, and Codex").
- `tests/test_build.py::TestBuildExclusions::test_exclusion_path_containment`
  (the existing containment test) still passes against this implementation.
- Added `test_exclusion_path_containment_rejects_sibling_prefix` in
  `tests/test_build.py` (right after `test_exclusion_path_containment`),
  which builds a manifest exclusion resolving to `dist/python-api-evil/marker.txt`
  (a sibling of `dist/python-api` sharing a name prefix) and asserts the file
  is NOT deleted. This exercises exactly the false-negative scenario the
  issue describes and passes against the current `is_relative_to` guard.

No other change is required to satisfy issue #73's acceptance criteria.

## Why `uv run pytest` still fails

Running the full suite fails on 4 tests that are unrelated to the exclusion
containment check:

- `TestBuildPluginSkills::test_build_copies_specific_core_skills`
- `TestBuildPluginDocs::test_build_copies_agent_matching_doc`
- `TestBuildPluginDocs::test_build_agent_matching_doc_has_content`
- `TestValidation::test_missing_core_skill_in_list_raises_error`

These fail because commit `b348b704` (predates this issue's branch point,
already on `main`/HEAD) rewrote `build_preset.py` for the portable
hook-runner change and, as a side effect, silently dropped two features that
still have committed tests exercising them:

1. **`core.skills` as a list** — `_validate_manifest` no longer validates
   `manifest["core"]["skills"]` when it's a list (removed
   `isinstance(core_skills, list)` branch), and `build_preset` no longer
   copies named skills when `core.skills` is a list (removed the
   `elif isinstance(skills_setting, list):` branch). Only `"all"` is
   handled now.
2. **`docs/agent-matching.md` copy step** — the entire "Copy
   agent-matching.md -> docs/" step (introduced in `0c813ec` "feat(agents):
   codify agent-matching algorithm as shared infrastructure") was deleted
   from `build_preset.py`, but `tests/conftest.py` still seeds
   `core/docs/agent-matching.md` and `tests/test_build.py` still asserts it
   lands in `dist/<preset>/docs/agent-matching.md`.

I confirmed via `git diff main -- scripts/build_preset.py` that this branch
makes no changes to that file beyond what's already on `main`/HEAD — the
regression and the failing tests both predate this issue and are unrelated
to `Path.is_relative_to`.

## Why I didn't fix it here

Per this repo's conventions, fixing those two dropped features would mean
editing `build_preset.py` in ways not named or required by issue #73's
acceptance criteria (which only covers the exclusion containment check).
That's out-of-scope opportunistic cleanup and would be expected to fail
adversarial scope review, so I'm flagging it here instead of silently
widening the diff.

## Suggested follow-up

File a separate issue to restore, in `scripts/build_preset.py`:

- `core.skills` list support in both `_validate_manifest` (raise
  `BuildValidationError` for unknown core skill names) and `build_preset`
  (copy only the named skills).
- The `docs/agent-matching.md` copy step (gated on the preset shipping at
  least one agent, per the original `0c813ec`/`ccf03c2` behavior).

Once that's fixed, `uv run pytest` should be fully green including this
issue's new sibling-prefix containment test.
