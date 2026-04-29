---
name: init-project
description: >
  Bootstrap the full .claude ecosystem for a new or existing project. Use when
  the user says "init project", "set up Claude", "add Claude to this project",
  "bootstrap .claude", or invokes /init-project. Runs a 5-phase pipeline:
  detect existing setup, analyze codebase, interview for project purpose and
  conventions, generate CLAUDE.md, and configure protection + automation hooks.
---

# Init Project Orchestrator

Bootstrap a complete `.claude` ecosystem in five phases: detect gaps, analyze, interview, generate CLAUDE.md, and configure hooks. Works for both existing codebases and empty repos.

Read [references/interview-domains.md](references/interview-domains.md) before running the interview phase. Read [references/hook-presets.md](references/hook-presets.md) before presenting guardrail options.

## Phase 1: Detect Gaps

Check for existing `.claude` ecosystem components. For each component found, ask the user whether to update or skip it.

**Components to check:**

| Component | Check | What it means |
|---|---|---|
| `.claude/` directory | Directory exists | Base directory for Claude config |
| `.claude/docs/project.md` | File exists | Codebase analysis already run |
| `CLAUDE.md` | File exists at project root | Root config already generated |
| `.claude/hooks/` | Directory exists with `*.py` files | Protection hooks already configured |
| `.claude/settings.json` | File exists | Claude settings already configured |

**For each component that exists**, use `AskUserQuestion`:

> "{Component} already exists. Would you like to update it or skip it?"
> - (A) Update — re-run the phase that generates this component
> - (B) Skip — keep the existing version

Record the user's decisions. Components marked "Skip" will be bypassed in their respective phases. Components marked "Update" or components that do not exist will be generated normally.

If no components exist, inform the user: "No existing .claude setup detected. Starting fresh setup." and proceed to Phase 2 without asking questions.

## Phase 2: Analyze

> "Phase 2: Analyzing your codebase to understand the tech stack, architecture, and test setup. This will generate `.claude/docs/project.md`."

**Empty repo detection**: Glob for source files (`*.py`, `*.js`, `*.ts`, `*.go`, `*.rs`, `*.java`, `*.rb`). If none are found, the repo is empty or documentation-only.

- **Source files found**: Delegate to `/project-context` for codebase analysis and `project.md` generation. If the user chose "Skip" for `project.md` in Phase 1, skip this delegation but still read the existing `project.md` to extract context for Phase 3.
- **No source files found**: Inform the user: "No source files detected. Switching to interview-heavy mode — I'll ask more detailed questions about your planned stack and conventions." Set a flag for interview-heavy mode. Skip `/project-context` delegation entirely.

If `/project-context` fails (crashes or produces malformed output), log the error, skip analysis, and switch to interview-heavy mode. Do not halt the pipeline.

## Phase 3: Interview

> "Phase 3: Collecting your project conventions. I'll ask about the project, stack, style, methodology, and guardrails."

Run a structured interview across five domains defined in [references/interview-domains.md](references/interview-domains.md). The interview mode depends on Phase 2 results:

- **Normal mode** (codebase analyzed): Present analysis findings for confirmation. Use the "Confirm Mode" question templates from interview-domains.md.
- **Interview-heavy mode** (empty repo or analysis failed): Ask open-ended questions. Use the "Open-Ended Mode" templates from interview-domains.md.

### Domain order

1. **Project Overview** — What the project is, its purpose, intended users
2. **Stack** — Language, framework, package manager, test runner, CI/CD
3. **Style** — Naming conventions, formatter/linter, type hints, docstring style
4. **Methodology** — TDD, branching, review workflow, commit conventions
5. **Guardrails & Automation** — File protection presets + post-edit lint/format hooks (read [references/hook-presets.md](references/hook-presets.md))

For each domain, ask every question in the domain using `AskUserQuestion`. Record all answers — they will be passed as pre-supplied context to downstream skills in Phases 4 and 5.

If the user chose "Skip" for CLAUDE.md in Phase 1, still run the interview — the answers inform hook setup in Phase 5. If the user chose "Skip" for both CLAUDE.md and hooks, skip the interview entirely.

## Phase 4: Generate CLAUDE.md

> "Phase 4: Generating your root CLAUDE.md file based on the project analysis and your answers."

If the user chose "Skip" for CLAUDE.md in Phase 1, skip this phase.

Delegate to `/generate-claude-md`. Pass the following as pre-supplied context so the skill enters orchestrated mode and does not re-interview the user:

- **Project overview**: Project purpose and intended users (from Domain 1)
- **Tech stack**: Language, version, framework, package manager, test runner, CI/CD (from Domain 2)
- **Code style**: Naming convention, formatter/linter, type hints, docstring style (from Domain 3)
- **Methodology**: TDD preference, branching strategy, review workflow, commit convention (from Domain 4)
- **Commands**: Build, run, test commands discovered during analysis or interview

If `/generate-claude-md` fails (e.g., cannot write to project root due to permissions), log the error and continue to Phase 5. Do not halt the pipeline.

## Phase 5: Configure Hooks

> "Phase 5: Setting up hooks based on your guardrail and automation selections."

If the user chose "Skip" for hooks in Phase 1, or if the user selected no guardrails and no automation in Domain 5, skip this phase.

Generate hooks directly rather than delegating to `/setup-hooks` (which requires its own interactive interview and has no orchestrated mode). Use the selections from Domain 5 to create up to two hooks.

### Step 1: Create hooks directory

Create `.claude/hooks/` directory if it does not exist (`mkdir -p .claude/hooks/`).

### Step 2: Generate protect-files hook (PreToolUse)

Skip if the user selected no protection patterns in Domain 5 Part A.

Generate a Python script at `.claude/hooks/protect-files.py` using the canonical template from the [setup-hooks hook protocol](../setup-hooks/references/hook-protocol.md). The script should:
- Read `tool_input.file_path` from stdin JSON
- Check the file path against all selected protection patterns
- Exit with code 2 (blocked) if any pattern matches, code 0 (allowed) otherwise
- Print the blocked pattern to stderr

### Step 3: Generate post-edit-lint hook (PostToolUse)

Skip if the user selected no automation presets in Domain 5 Part B.

Generate a Python script at `.claude/hooks/post-edit-lint.py` using the canonical PostToolUse template from the [setup-hooks hook protocol](../setup-hooks/references/hook-protocol.md). The script should:
- Read `tool_input.file_path` from stdin JSON
- Check the file extension against the selected formatters/linters
- For each matching tool, use `shutil.which()` to verify availability, then run via `subprocess.run()`
- Report executed actions to stderr
- Use stdlib only (no pip dependencies)

Example structure for a Python + Ruff selection:

```python
if file_path.endswith(".py") and shutil.which("ruff"):
    run(["ruff", "check", "--fix", file_path], "ruff-check")
    run(["ruff", "format", file_path], "ruff-format")
```

For multi-language projects, chain all selected formatters with appropriate extension guards.

### Step 4: Wire hooks into settings.json

Read `.claude/settings.json` (create it if missing with `{"hooks": {"PreToolUse": [], "PostToolUse": []}}`).

If protect-files was generated, append a PreToolUse entry:
```json
{
  "matcher": "Edit|Write",
  "hooks": [{"type": "command", "command": "python3 .claude/hooks/protect-files.py"}]
}
```

If post-edit-lint was generated, append a PostToolUse entry:
```json
{
  "matcher": "Edit|Write",
  "hooks": [{"type": "command", "command": "python3 .claude/hooks/post-edit-lint.py"}]
}
```

Write the updated settings.json with 2-space indent formatting.

If any step fails (e.g., Python not available, cannot create directories), log the reason and skip that step. Do not halt the pipeline.

## Wrap-Up

Present a summary table showing the result of each phase:

```
| Phase | Component | Status |
|-------|-----------|--------|
| 1. Detect | Existing setup | Completed — {N} components found |
| 2. Analyze | .claude/docs/project.md | Completed / Skipped (user choice) / Skipped (empty repo) |
| 3. Interview | Conventions | Completed — {N} domains |
| 4. CLAUDE.md | CLAUDE.md | Completed / Skipped (user choice) / Failed ({reason}) |
| 5. Hooks | .claude/hooks/ | Completed ({N} hooks) / Skipped (user choice) / Skipped (no selections) / Failed ({reason}) |
```

Then use `AskUserQuestion` to offer:

> "Setup complete. Would you like to commit the generated files?"
> - (A) Commit generated files via /commit (Recommended)
> - (B) Leave files uncommitted

If the user selects (A), invoke `/commit` to stage and commit all generated `.claude/` files and `CLAUDE.md`.

## Error Handling — Failure vs. State-Transition Table

Use this table to distinguish between expected state transitions (handle gracefully) and actual failures (skip and report).

| Delegation | Expected State Transition | Actual Failure (skip and report) |
|---|---|---|
| `/project-context` | Empty repo detected -> switch to interview-heavy mode | Codebase analysis crashes or produces malformed output |
| `/generate-claude-md` | No project.md exists -> interview-only skeleton mode | Skill cannot write to project root (permissions) |
| Hook generation | User selects no guardrails and no automation -> skip hooks gracefully | Cannot create `.claude/hooks/` directory; cannot write settings.json |

**Key principle**: No single phase failure should halt the pipeline. Log the error, skip the phase, record the status, and continue. The wrap-up summary will show the user exactly what succeeded and what did not.

## Fallback (no AskUserQuestion available)

If `AskUserQuestion` is not available in the runtime environment, present choices as formatted text instead:

**[Header] — [Question]**

**Recommended:** [Your recommendation and why]

**Alternatives:**

- (A) [Option] — [trade-off]
- (B) [Option] — [trade-off]

Apply this fallback pattern to every question in Phases 1, 3, and Wrap-Up. When presenting the Guardrails & Automation multiSelects in Domain 5, list all options with `[x]` for recommended defaults and `[ ]` for optional items, and ask the user to reply with the numbers or letters of their selections.
