# Setup Pre-Commit Skill — Design Spec

## Summary

A unified core skill that sets up pre-commit hooks for both Python and JS/TS projects. Replaces the existing JS-only `setup-pre-commit` skills in `python-api` and `full-stack` presets with a single core skill that detects project type and follows a consistent flow regardless of language.

Note: The `python-api` preset currently ships a JS-only (Husky/lint-staged) pre-commit skill, which is a mismatch this design corrects.

## Goals

- One skill for all project types, living in `core/skills/`
- Consistent UX: both language paths follow the same flow and use `AskUserQuestion` to let the user choose which checks to enable
- Python path uses the `pre-commit` framework with `ruff`, `mypy`, and `pytest`
- JS/TS path uses Husky + lint-staged with Prettier, ESLint, typecheck, and test
- Mixed projects (both `pyproject.toml` and `package.json`) use the `pre-commit` framework as the single hook manager for all languages, avoiding conflicts

## File Structure

```
core/skills/setup-pre-commit/
├── SKILL.md              # Detection logic, frontmatter, shared flow
├── python-setup.md       # Python-specific steps
└── js-setup.md           # JS/TS-specific steps
```

### SKILL.md Frontmatter

```yaml
---
name: setup-pre-commit
description: Set up pre-commit hooks for the current repo. Use when user wants to add pre-commit hooks, configure commit-time linting, formatting, type checking, or testing. Triggers on "pre-commit", "git hooks", "linting hooks", or /setup-pre-commit.
---
```

## Shared Flow (SKILL.md)

Both language paths follow the same sequence:

1. **Detect project type** — check for `pyproject.toml` (Python) or `package.json` (JS/TS).
   - Python only → follow `python-setup.md`
   - JS/TS only → follow `js-setup.md`
   - Both present → offer three options via AskUserQuestion: Python only, JS/TS only, or both. If "both" is selected, use the `pre-commit` framework as the single hook manager (follow `python-setup.md` and include JS tools as additional `local` hooks — no Husky needed).
   - Neither present → inform the user no supported project was detected.
2. **Ask user which checks they want** — present available hooks for the detected language(s) using AskUserQuestion. Let the user select which checks to enable.
3. **Install framework** — language-specific framework installation.
4. **Generate config** — create config file(s) based on user selections.
5. **Install hooks** — activate the hooks in git.
6. **Verify** — run hooks against the full codebase to confirm they work.
7. **Handle verification failures** — if lint/format violations are found, auto-fix where possible (`ruff --fix`, `ruff format`, `prettier --write`) and re-run. If type or test failures occur, inform the user and proceed with committing the hook config files only.
8. **Commit** — stage and commit the config files.

After detection, the skill reads the appropriate sub-file (`python-setup.md` or `js-setup.md`) for language-specific instructions.

## Python Path (python-setup.md)

### Available Checks (presented to user)

- **ruff lint** — linting with autofix (`ruff check --fix`)
- **ruff format** — code formatting (`ruff format`)
- **mypy** — static type checking
- **pytest** — test suite (`uv run pytest`)

### Steps

1. **Install pre-commit**: `uv add --dev pre-commit`
2. **Create `.pre-commit-config.yaml`** with selected hooks:
   - **ruff** (lint + format): Use astral-sh's official `ruff-pre-commit` repo hooks — maintained, versioned, no local ruff dependency needed
   - **mypy**: `local` hook using `uv run mypy src/` (detect source directory from `pyproject.toml` or fall back to `src/`), with `--ignore-missing-imports` by default — needs access to project dependencies
   - **pytest**: `local` hook using `uv run pytest` — needs access to project dependencies
3. **Install hooks**: `uv run pre-commit install`
4. **Verify**: `uv run pre-commit run --all-files`
5. **Commit**: stage and commit with message `Add pre-commit hooks (pre-commit framework)`

### Hook Execution Order

Hooks run in config order, fastest first:

1. ruff check (fast, lint)
2. ruff format (fast, format)
3. mypy (medium, type check)
4. pytest (slow, tests)

### Both-Languages Mode

When both Python and JS/TS are detected and the user selects "both", the `pre-commit` framework manages everything. JS tools are added as `local` hooks in `.pre-commit-config.yaml`:

- **prettier**: `local` hook running `npx prettier --ignore-unknown --write` on staged files
- **eslint**: `local` hook running `npx eslint --fix` on `*.{js,ts,jsx,tsx}` files (only if ESLint config exists in the project)

This avoids the `.git/hooks/pre-commit` ownership conflict between `pre-commit` framework and Husky.

## JS/TS Path (js-setup.md)

### Available Checks (presented to user)

- **prettier** — code formatting
- **eslint** — linting (only offered if an ESLint config already exists in the project, since ESLint v9+ requires a config)
- **typecheck** — TypeScript type checking (requires `typecheck` script in package.json)
- **test** — test suite (requires `test` script in package.json)

### Steps

1. **Detect package manager**: check for lock files (`package-lock.json` → npm, `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `bun.lockb` → bun). Default to npm.
2. **Install dependencies**: add selected tools + `husky` + `lint-staged` (if prettier/eslint selected) as devDependencies.
3. **Initialize Husky**: `npx husky init` — creates `.husky/` dir and `prepare` script.
4. **Create `.husky/pre-commit`**: include selected checks, adapted to detected package manager. If `typecheck` or `test` scripts don't exist in package.json, omit and inform user.
5. **Create `.lintstagedrc`** (if prettier or eslint selected): configure lint-staged to run selected formatters/linters on staged files.
   - Prettier: `"*": "prettier --ignore-unknown --write"`
   - ESLint: `"*.{js,ts,jsx,tsx}": "eslint --fix"`
   - Both: combine into a single config with both entries
6. **Create `.prettierrc`** (if prettier selected and no config exists): sensible defaults.
7. **Verify**: run each command from the pre-commit hook sequentially (not just `npx lint-staged`) to confirm the full hook works.
8. **Commit**: stage and commit with message `Add pre-commit hooks (husky + lint-staged)`

## Changes to Existing Presets

### Removals

- Delete `presets/python-api/skills/setup-pre-commit/` directory
- Delete `presets/full-stack/skills/setup-pre-commit/` directory
- Remove `"setup-pre-commit"` from `presets/python-api/manifest.json` `preset_skills` array
- Remove `"setup-pre-commit"` from `presets/full-stack/manifest.json` `preset_skills` array
- Remove `/setup-pre-commit` trigger documentation from `presets/python-api/CLAUDE-preset.md`
- Remove `/setup-pre-commit` trigger documentation from `presets/full-stack/CLAUDE-preset.md`

### No changes needed

- Core manifest: presets include core skills via `"skills": "all"`, so the new core skill is automatically available
- Other presets (`data-pipeline`, `analysis`, `claude-tooling`): no changes, they'll pick up the core skill automatically

## Notes

- Husky v9+ doesn't need shebangs in hook files
- `prettier --ignore-unknown` skips files Prettier can't parse
- `ruff-pre-commit` repo hooks are maintained by astral-sh and auto-update via `pre-commit autoupdate`
- `mypy` and `pytest` run as local hooks because they need access to the project's virtual environment and dependencies
- `mypy` targets `src/` (or detected source dir) with `--ignore-missing-imports` to avoid failing on projects without full type stub coverage
- ESLint is only offered as an option when an existing ESLint config is detected, since ESLint v9+ requires configuration
