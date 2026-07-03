# issue-119: gate blocked by pre-existing packaging defect (unrelated to this issue)

## Implementation status

The required test is already implemented in `tests/test_build.py`
(`test_exclude_removes_single_file`, added under `TestBuildExclusions`):

```python
def test_exclude_removes_single_file(self, tmp_repo: Path) -> None:
    manifest_path = tmp_repo / "presets" / "python-api" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["exclude"] = ["README.md"]
    manifest_path.write_text(json.dumps(manifest))

    build_preset("python-api", repo_root=tmp_repo)
    dist_path = tmp_repo / "dist" / "python-api"
    assert not (dist_path / "README.md").exists()
    assert (dist_path / "settings.json").exists()
```

This satisfies all four acceptance criteria: it excludes a single generated
file (`README.md`, step 9 in `build_preset`) via the manifest, asserts it's
gone from `dist/<preset>/`, asserts the sibling `settings.json` (step 7,
generated before the excluded file) still exists, and exercises the
`excluded_path.unlink()` branch (the `else` arm at
`scripts/build_preset.py:311`, i.e. the non-directory branch of the step-10
exclusion loop) that was previously uncovered.

## Blocker: gate cannot run in this worktree — pre-existing, out of scope

The prior gate run failed with a `hatchling.build.build_editable`
`FileNotFoundError` during `uv sync`, unrelated to any test-file change:

```
FileNotFoundError: Forced include not found:
.../scripts/installer/presets
```

Root cause: `pyproject.toml` declares

```toml
[tool.hatch.build.targets.wheel.force-include]
"scripts/installer/presets" = "scripts/installer/presets"
```

but `scripts/installer/presets/` is gitignored
(`.gitignore:16`, comment: "Generated preset bundles (populated by the
pre-build step before uv build)") and **no script in this repo currently
populates it** (introduced in commit `ed31f76`,
"build(installer): console entry point + bundle presets into the wheel").
In any fresh checkout/worktree that hasn't manually run that undocumented
pre-build step, the directory doesn't exist, so hatchling's forced include
fails and `uv sync` / `uv run` crash before any test collects. This affects
every issue slice built in a fresh worktree, not just this one — it is not
caused by, and not fixable within the scope of, issue #119.

Per repo convention I have not modified `pyproject.toml`/`uv.lock` and have
not speculatively created `scripts/installer/presets/` (its basename isn't
named in the issue body). Flagging for a maintainer decision — options:

1. Commit an empty `scripts/installer/presets/.gitkeep` so the force-include
   never fails on a missing path, independent of the pre-build step.
2. Implement the missing pre-build step that copies built `dist/` output
   into `scripts/installer/presets/` before packaging.
3. Make the force-include conditional/optional so its absence doesn't crash
   the editable build.

No code changes were made beyond the already-present test addition described
above.
