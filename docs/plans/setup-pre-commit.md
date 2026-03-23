# Plan: Unified Setup Pre-Commit Skill

> Source PRD: https://github.com/cdcoonce/claude-workflow/issues/28

## Architectural decisions

Durable decisions that apply across all phases:

- **Skill location**: `core/skills/setup-pre-commit/` with 3 files (`SKILL.md`, `python-setup.md`, `js-setup.md`)
- **Detection signals**: `pyproject.toml` → Python, `package.json` → JS/TS, both → ask user (Python only / JS only / both)
- **User interaction**: `AskUserQuestion` tool for check selection in both language paths
- **Python framework**: `pre-commit` installed via `uv add --dev pre-commit`
- **Python hooks**: ruff via `ruff-pre-commit` repo, mypy/pytest as `local` hooks via `uv run`
- **JS framework**: Husky v9+ with lint-staged
- **Both-languages mode**: `pre-commit` framework manages everything, JS tools as `local` hooks (no Husky)
- **Shared flow**: detect → ask → install → configure → install hooks → verify → handle failures → commit

---

## Phase 1: Core skill with Python path

**User stories**: Python developers can set up pre-commit hooks with ruff, mypy, and pytest via a single skill invocation

### What to build

Create the skill directory with `SKILL.md` containing frontmatter, detection logic, and the shared flow sequence. Create `python-setup.md` with the full Python path: install `pre-commit` via uv, present available checks (ruff lint, ruff format, mypy, pytest) via `AskUserQuestion`, generate `.pre-commit-config.yaml` based on selections, install hooks, verify with `--all-files`, handle failures, and commit. ruff hooks use the official `ruff-pre-commit` repo; mypy targets `src/` with `--ignore-missing-imports`; pytest runs via `uv run`. Hooks are ordered fastest-first.

### Acceptance criteria

- [ ] `core/skills/setup-pre-commit/SKILL.md` exists with correct frontmatter (`name`, `description` with trigger keywords)
- [ ] `SKILL.md` contains detection logic checking for `pyproject.toml` and `package.json`
- [ ] `SKILL.md` contains the shared 8-step flow
- [ ] `SKILL.md` routes to `python-setup.md` when Python is detected
- [ ] `core/skills/setup-pre-commit/python-setup.md` exists with complete Python setup steps
- [ ] Python path uses `AskUserQuestion` to let user select which checks to enable
- [ ] Python path installs `pre-commit` via `uv add --dev pre-commit`
- [ ] ruff hooks use `ruff-pre-commit` repo (not local)
- [ ] mypy hook targets `src/` with `--ignore-missing-imports`
- [ ] pytest hook runs via `uv run pytest`
- [ ] Hook execution order is fastest-first (ruff check → ruff format → mypy → pytest)
- [ ] Verification step runs `uv run pre-commit run --all-files`
- [ ] Failure handling: auto-fix lint/format, inform user on type/test failures

---

## Phase 2: JS/TS path

**User stories**: JS/TS developers can set up pre-commit hooks with Prettier, ESLint, typecheck, and tests via the same skill

### What to build

Create `js-setup.md` with the full JS/TS path: detect package manager from lock files, present available checks (prettier, eslint, typecheck, test) via `AskUserQuestion`, install Husky + lint-staged + selected tools, initialize Husky, create `.husky/pre-commit` with selected checks, create `.lintstagedrc` with correct glob patterns per tool, create `.prettierrc` if needed, verify by running each hook command sequentially, and commit. ESLint is only offered when an existing config is detected. Update `SKILL.md` to route to `js-setup.md` when JS/TS is detected.

### Acceptance criteria

- [ ] `core/skills/setup-pre-commit/js-setup.md` exists with complete JS/TS setup steps
- [ ] JS path uses `AskUserQuestion` to let user select which checks to enable
- [ ] Package manager detection checks all lock file types (npm, pnpm, yarn, bun)
- [ ] ESLint only offered when existing config is detected
- [ ] `.lintstagedrc` includes correct patterns: `"*"` for Prettier, `"*.{js,ts,jsx,tsx}"` for ESLint
- [ ] `.prettierrc` created only if no Prettier config exists
- [ ] Verification runs each hook command sequentially (not just lint-staged)
- [ ] `SKILL.md` routes to `js-setup.md` when `package.json` detected
- [ ] Consistent flow structure with Python path (same step sequence)

---

## Phase 3: Both-languages mode

**User stories**: Full-stack/monorepo developers with both Python and JS/TS can set up unified pre-commit hooks without framework conflicts

### What to build

Update `SKILL.md` detection logic to handle the "both present" case: offer three options (Python only, JS only, both) via `AskUserQuestion`. When "both" is selected, the `pre-commit` framework manages everything. Add a "Both-Languages Mode" section to `python-setup.md` that includes JS tools (Prettier, ESLint) as `local` hooks in `.pre-commit-config.yaml`, running via `npx`. This avoids the `.git/hooks/pre-commit` ownership conflict between `pre-commit` and Husky.

### Acceptance criteria

- [ ] `SKILL.md` offers three options when both `pyproject.toml` and `package.json` are detected
- [ ] "Both" mode uses `pre-commit` framework as single hook manager
- [ ] Prettier added as `local` hook running `npx prettier --ignore-unknown --write`
- [ ] ESLint added as `local` hook running `npx eslint --fix` on `*.{js,ts,jsx,tsx}` (only if config exists)
- [ ] No Husky installed in "both" mode
- [ ] Combined hook order maintains fastest-first principle

---

## Phase 4: Preset cleanup

**User stories**: The old JS-only preset skills are removed, and the new core skill is the single source of truth

### What to build

Remove the old `setup-pre-commit` skill directories from `python-api` and `full-stack` presets. Update both preset `manifest.json` files to remove `"setup-pre-commit"` from `preset_skills`. Update both `CLAUDE-preset.md` files to remove the `/setup-pre-commit` trigger documentation. The new core skill is automatically available via `"skills": "all"` — no additions needed.

### Acceptance criteria

- [ ] `presets/python-api/skills/setup-pre-commit/` directory deleted
- [ ] `presets/full-stack/skills/setup-pre-commit/` directory deleted
- [ ] `"setup-pre-commit"` removed from `presets/python-api/manifest.json` `preset_skills` array
- [ ] `"setup-pre-commit"` removed from `presets/full-stack/manifest.json` `preset_skills` array
- [ ] `/setup-pre-commit` trigger docs removed from `presets/python-api/CLAUDE-preset.md`
- [ ] `/setup-pre-commit` trigger docs removed from `presets/full-stack/CLAUDE-preset.md`
- [ ] Smoke test passes: `uv run python -m scripts.smoke_test python-api`
- [ ] Smoke test passes: `uv run python -m scripts.smoke_test full-stack`
