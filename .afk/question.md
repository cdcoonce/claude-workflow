# Issue #101 — gate blocked by pre-existing, unrelated failures

## Implementation status: complete

`scripts/dev_cycle_validate.py`'s `_validate_parsed_state` now checks each
artifact row's `status` against `VALID_ARTIFACT_STATUSES` and appends an
error naming the phase, the bad value, the filename, and the valid set
(mirrors the existing `status`/`current_phase` error style). The existing
"completed but no artifact" check is unchanged and still runs after the new
check. `tests/test_dev_cycle_validate.py::TestArtifactCompleteness::test_invalid_artifact_status_fails`
covers an invalid status (`done`) and asserts the error names the phase and
the bad value; existing tests cover valid statuses passing.

`git diff HEAD --name-only` shows only these two files changed, both named
in the issue body.

## Blocker: 3 prior gate runs failed on 4 tests unrelated to this issue

Every prior attempt (including this one, by inspection) fails the same 4
tests, none of which touch `dev_cycle_validate.py`:

- `tests/test_build.py::TestBuildPluginSkills::test_build_copies_specific_core_skills`
- `tests/test_build.py::TestBuildPluginDocs::test_build_copies_agent_matching_doc`
- `tests/test_build.py::TestBuildPluginDocs::test_build_agent_matching_doc_has_content`
- `tests/test_validation.py::TestValidation::test_missing_core_skill_in_list_raises_error`

Root cause, confirmed by reading (not modifying) `scripts/build_preset.py`:

- Line ~185: `if manifest["core"].get("skills") == "all":` only copies core
  skills when `core.skills` is the literal string `"all"`. When a manifest
  sets `core.skills` to a list (e.g. `["commit", "tdd"]`), nothing is
  copied — the list-form case was never implemented.
- There is no docs-copying step in `build_preset.py` at all (no reference to
  `docs` or `agent-matching.md`), so `dist/<preset>/docs/agent-matching.md`
  is never produced.
- `_validate_manifest` never validates skill names when `core.skills` is a
  list, so a nonexistent skill name doesn't raise `BuildValidationError`.

Evidence this is pre-existing and unrelated to issue #101:

- `git diff main -- scripts/build_preset.py` is empty — this branch never
  touched that file.
- `git status --short scripts/build_preset.py` is empty.
- `git log --oneline -- tests/test_build.py` shows the relevant tests were
  added in `0c813ec feat(agents): codify agent-matching algorithm as shared
infrastructure`, an already-merged, unrelated commit — the list-form
  `core.skills` and docs-copying features were apparently never finished in
  `build_preset.py`/`_validate_manifest` to match.

Per the "no opportunistic fixes" / scope-discipline rules for this repo, I
did not touch `build_preset.py` or `scripts/validation.py` — fixing them is
out of scope for issue #101 and would draw a VERDICT: FAIL from the
adversarial scope reviewer for touching files not named in the issue body.

I was also unable to execute `uv run pytest` / `python3` directly in this
session (every invocation returned "This command requires approval" with no
prompt surfaced), so I could not re-run the gate myself to reconfirm; the
analysis above is from static reading of the diff and source, not a fresh
test run.

## Ask

Please either:

1. Accept this diff as correct for issue #101 and separately file/track a
   fix for the `core.skills`-as-list + docs-copying gap in
   `build_preset.py` (and the matching validation in `_validate_manifest`),
   or
2. Confirm whether the gate for this issue should be scoped to
   `tests/test_dev_cycle_validate.py` rather than the full suite, since the
   full suite appears to be red on `main` independent of any dev-cycle work.
