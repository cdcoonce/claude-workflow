# Note: gate build-crash is pre-existing, unrelated to issue #147

Issue #147's implementation is complete (see `git diff HEAD`):
`--no-install` added to all 4 `npx` invocations in
`presets/full-stack/hooks/post-edit-lint.py` (prettier, eslint, stylelint)
and `presets/claude-tooling/hooks/post-edit-lint.py` (prettier). Ruff's
`shutil.which("ruff")` guards are untouched. `tests/test_post_edit_lint.py`
already exists and covers all acceptance criteria (installed / missing /
present-but-not-locally-installed cases for both hooks), verified by static
read-through since I could not execute the suite (see below).

## Prior attempt's build-crash is pre-existing infra debt, not caused by this diff

The prior attempt's gate failure was:

```
FileNotFoundError: Forced include not found:
.../scripts/installer/presets
```

Root cause: `pyproject.toml` (added in commit `ed31f76`,
"build(installer): console entry point + bundle presets into the wheel")
declares:

```toml
[tool.hatch.build.targets.wheel.force-include]
"scripts/installer/presets" = "scripts/installer/presets"
```

`scripts/installer/presets/` is gitignored (`.gitignore` calls it "Generated
preset bundles (populated by the pre-build step before uv build)"), but no
script in this repo actually populates it — `scripts/build_preset.py` writes
to `dist/`, not `scripts/installer/presets/`. So any fresh checkout/worktree
hits this `hatchling.build.build_editable` failure on `uv sync` /
`uv run pytest`, independent of which files are changed. This is not
something this issue's diff touches (`scripts/installer/*`, `pyproject.toml`
are all untouched here) and per repo convention I will not modify
`pyproject.toml`/`uv.lock` to work around it.

I could not confirm this locally: my sandbox requires approval for
`uv sync`, `uv run pytest`, and even bare `python3 -c` invocations, and no
interactive approver is available in this session, so I was unable to
re-run the gate myself. Verification of the diff was done by static
read-through of the hook logic against each test case in
`tests/test_post_edit_lint.py`.

Recommend: fix the missing pre-build step (generate
`scripts/installer/presets/` from `dist/`, or point the force-include there
directly) in a separate slice, since it blocks the gate for every issue in
this repo, not just this one.
