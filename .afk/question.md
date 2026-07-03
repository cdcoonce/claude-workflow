# Issue #111 — gate failure is pre-existing/unrelated, not caused by this diff

## Implementation status

The diff for issue #111 is complete and matches the acceptance criteria:

- `scripts/build_marketplace.py`: tracks `seen_names: dict[str, str]` while building
  `plugins`, and raises `ValueError` naming both colliding preset directories when a
  `name` repeats (mirrors the existing missing-name error style).
- `tests/test_marketplace.py`: adds
  `test_marketplace_duplicate_name_raises_clear_error`, which creates a
  `python-api-copy` preset with `name: "python-api"` (duplicating the existing
  `python-api` preset) and asserts `pytest.raises(ValueError, match="python-api-copy")`.

`git diff HEAD --name-only` shows only these two files touched — both required by the
acceptance criteria.

## Why the full-suite gate fails anyway (root-caused, not fixed)

The prior gate run's failing-test output includes 4 failures that are **not** in
`test_marketplace.py` and are unrelated to this issue:

- `tests/test_build.py::TestBuildPluginSkills::test_build_copies_specific_core_skills`
- `tests/test_build.py::TestBuildPluginDocs::test_build_copies_agent_matching_doc`
- `tests/test_build.py::TestBuildPluginDocs::test_build_agent_matching_doc_has_content`
- `tests/test_validation.py::TestValidation::test_missing_core_skill_in_list_raises_error`

Root cause: `scripts/build_preset.py` has no code path for `core.skills` as a list
(only handles the literal string `"all"`, `build_preset.py:185`) and no code that
copies an `agent-matching.md` doc into `dist/<preset>/docs/`. These are pre-existing
feature gaps, not regressions introduced by this branch:
`git diff $(git merge-base main HEAD) -- tests/test_build.py tests/test_validation.py scripts/build_preset.py`
produces **zero output** — these files are byte-identical to `main`.

There is also a separate, pre-existing build-crash symptom in the same log:
`uv sync`/`pip install -e .` failing with
`FileNotFoundError: Forced include not found: .../scripts/installer/presets`.
`pyproject.toml` declares
`[tool.hatch.build.targets.wheel.force-include]` mapping
`scripts/installer/presets -> scripts/installer/presets`, but that directory is
**empty and untracked** (`git ls-files scripts/installer/presets/` returns nothing;
no commit ever touched it). Git doesn't track empty directories, so a fresh clone or
worktree checkout lacks the path entirely, breaking the editable install regardless of
any change in this issue's diff.

## Why I'm not fixing these here

Per repo conventions, fixing `scripts/build_preset.py`'s missing features or the
`pyproject.toml` force-include/packaging gap is out of scope for issue #111 (duplicate
plugin-name detection in `build_marketplace.py`) and would trigger the adversarial
reviewer's scope check (unrelated file touches + `pyproject.toml` edits are explicitly
disallowed). Widening this diff to "fix while I'm here" is exactly the anti-pattern the
conventions warn against.

## Ask

Please confirm: should the gate for this issue be scoped to `tests/test_marketplace.py`
(and/or `tests/test_build.py`'s unrelated-to-marketplace pre-existing failures be
tracked as separate issues), or is there a reason these are expected to already pass
that I'm missing? I did not modify `scripts/build_preset.py`, `pyproject.toml`, or
`scripts/installer/presets`.
