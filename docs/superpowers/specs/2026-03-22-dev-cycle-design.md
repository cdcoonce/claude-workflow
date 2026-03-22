# Dev Cycle Orchestrator — Design Spec

## Overview

A new core skill (`/dev-cycle`) that orchestrates the full GitHub-issues-driven development lifecycle. It enforces a strict 7-phase pipeline, delegates heavy lifting to existing skills, and uses a glue layer + state file for reliable handoffs and cross-conversation resume.

**Approach:** Dispatcher + Glue Layer (Approach C) — existing skills do the work, the orchestrator handles sequencing, validation, and state tracking.

**Location:** `core/skills/dev-cycle/` — universal, available to all presets.

---

## The 7-Phase Pipeline

Every phase is mandatory. No phase can be skipped.

| #   | Phase           | Delegates To                                                                               | Artifact Produced                           | Gate Condition                    |
| --- | --------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------- | --------------------------------- |
| 1   | **Brainstorm**  | `write-a-prd` (full skill invocation)                                                      | Clarified requirements + GitHub Issue (PRD) | Issue URL recorded                |
| 2   | **Plan**        | `prd-to-plan`                                                                              | `./plans/{feature}.md`                      | Plan file exists                  |
| 3   | **CEO Review**  | `plan-ceo-review` (recommends HOLD SCOPE; skill's own mode selection runs)                 | Reviewed/revised plan                       | Review complete, user approves    |
| 4   | **Issues**      | `prd-to-issues`                                                                            | GitHub Issues (implementation tickets)      | All issue URLs recorded           |
| 5   | **Implement**   | Orchestrator dispatch loop (`tdd` per issue, following `subagent-development` methodology) | Working code + passing tests                | All issues resolved, tests pass   |
| 6   | **Code Review** | `code-review`                                                                              | Review report, issues fixed                 | Clean review (no blocking issues) |
| 7   | **PR**          | `commit` + `github-cli`                                                                    | Pull request                                | PR URL recorded                   |

**Phase 1 (Brainstorm)** invokes `write-a-prd` as a single skill invocation. The skill's own internal flow handles both the interview/brainstorm and formalization into a GitHub issue. The orchestrator does not split the skill into two phases — it trusts the skill's built-in confirmation gates.

**Phase 3 (CEO Review)** recommends HOLD SCOPE mode to the user but allows the skill's own mode-selection logic (Step 0F) to run. The orchestrator does not suppress the skill's mode selection — it provides a recommendation, not an override.

**Phase 5 (Implement)** is owned by the orchestrator, not delegated to a skill. The orchestrator follows the `subagent-development` methodology (a core doc, not a skill) to dispatch one subagent per GitHub issue, each invoking the `tdd` skill. Code review runs between each subagent dispatch.

---

## State File

Each feature gets a tracking file at `docs/dev-cycle/{feature-slug}.md`. This is the single source of truth for where a feature stands in the pipeline.

**Relationship to other directories:**

- `docs/dev-cycle/` — Dev cycle state files (this spec)
- `docs/plans/` (or `./plans/`) — Plan files created by `prd-to-plan` (Phase 2 artifact)
- `docs/archive/` — Completed plans are archived here per existing convention

When a feature completes (PR merged), its state file remains in `docs/dev-cycle/` as an audit record. The associated plan file follows the existing archive convention.

### Format

```markdown
---
feature: dark-mode-toggle
status: in_progress # not_started | in_progress | completed | abandoned
current_phase: plan # brainstorm | plan | ceo_review | issues | implement | code_review | pr
created: 2026-03-21
updated: 2026-03-21
branch: feat/dark-mode-toggle
---

## Artifacts

| Phase       | Status      | Artifact                               |
| ----------- | ----------- | -------------------------------------- |
| brainstorm  | completed   | https://github.com/user/repo/issues/42 |
| plan        | in_progress | ./plans/dark-mode-toggle.md            |
| ceo_review  | pending     | —                                      |
| issues      | pending     | —                                      |
| implement   | pending     | —                                      |
| code_review | pending     | —                                      |
| pr          | pending     | —                                      |

## Log

- 2026-03-21 10:15 — Brainstorm complete. PRD filed as issue #42.
- 2026-03-21 11:01 — Plan started. Breaking into vertical slices.
```

### Field Definitions

- **feature:** Kebab-case slug used as filename and human-readable identifier.
- **status:** Overall feature status. `not_started` on creation, `in_progress` once phase 1 begins, `completed` once PR is filed, `abandoned` if the user decides to stop.
- **current_phase:** The phase currently being worked on. Valid values: `brainstorm`, `plan`, `ceo_review`, `issues`, `implement`, `code_review`, `pr`.
- **created/updated:** ISO date stamps.
- **branch:** Git feature branch name. Created at the start of Phase 5 (Implement). Format: `feat/{feature-slug}`.
- **Artifacts table:** One row per phase. Status is `pending`, `in_progress`, `completed`, or `blocked`. Artifact column holds the output reference (URL, file path, or description).
- **Log:** Timestamped append-only audit trail. Each phase transition adds an entry.

### Valid Phase Transitions

Phases must proceed in strict forward order. A phase can only move to `completed` when its gate condition is met.

```text
brainstorm → plan → ceo_review → issues → implement → code_review → pr
```

**Exception — backwards transitions:** The orchestrator supports one backwards transition: `implement → plan` (or `code_review → plan`). This is used when implementation or code review reveals that the approach is fundamentally wrong and the plan needs rework. When this happens, the orchestrator logs the reason, resets subsequent phases to `pending`, and re-enters Phase 2. The CEO Review and Issues phases must run again on the revised plan.

---

## Branch Management

- **Phases 1–4** (Brainstorm through Issues) run on whatever branch the user is on. These phases produce documentation and GitHub issues, not code.
- **Phase 5 (Implement)** creates a feature branch `feat/{feature-slug}` before dispatching the first subagent. The branch name is recorded in the state file.
- **Phase 7 (PR)** opens the pull request from `feat/{feature-slug}` to the repository's main branch.
- **Resuming a feature** that is at Phase 5+ includes checking out the feature branch if not already on it.
- **Concurrent features** work on separate branches. When listing in-progress features at re-entry, the orchestrator shows the branch name alongside the feature name and current phase.

---

## Re-entry & Phase Detection

### First Invocation (no arguments)

1. Check `docs/dev-cycle/` for any state files with `status: in_progress`
2. If one exists → ask "Resume **{feature-name}** (`{branch}`)? Currently at **{current_phase}**."
3. If multiple exist → list them with branch names, ask which to resume
4. If none exist → ask "What feature are you working on?" and start phase 1

### Invocation with Argument (e.g., `/dev-cycle dark-mode-toggle`)

1. Look for `docs/dev-cycle/dark-mode-toggle.md`
2. If found → resume at `current_phase`
3. If not found → create state file, start phase 1

### Context Loading on Resume

When resuming a feature (cross-conversation or same-conversation), the orchestrator must load all referenced artifacts into context before proceeding:

1. Read the state file to determine `current_phase` and all recorded artifacts
2. For each completed phase, load the artifact:
   - **Brainstorm:** Fetch the PRD GitHub issue via `gh issue view`
   - **Plan:** Read the plan file from disk
   - **CEO Review:** Read the plan file (which includes review revisions)
   - **Issues:** Fetch all implementation issue URLs via `gh issue view`
   - **Implement:** Check git status on the feature branch, review which issues are closed
3. Present a brief summary to the user: "Resuming **{feature-name}** at **{current_phase}**. Here's where we left off: {summary of completed phases and current state}."
4. Continue with the current phase

---

## Glue Layer — Phase Transitions

Each transition follows the same pattern: validate artifact → update state → prepare context → invoke next skill.

### Brainstorm → Plan

- **Validate:** GitHub issue URL (PRD) is present and accessible
- **Handoff:** Pass issue URL to `prd-to-plan`, which reads the PRD issue and breaks it into vertical slices
- **Record:** Plan file path in state file

### Plan → CEO Review

- **Validate:** Plan file exists at recorded path
- **Handoff:** Pass plan file path to `plan-ceo-review`, recommend HOLD SCOPE mode
- **Record:** Review outcome + any revisions

### CEO Review → Issues

- **Validate:** Plan has been reviewed and user approved the final version
- **Handoff:** Pass finalized plan to `prd-to-issues` to decompose into GitHub issues
- **Record:** All issue URLs in state file

### Issues → Implement

- **Validate:** All GitHub issues created and URLs recorded
- **Handoff:** Create feature branch `feat/{feature-slug}`. Load plan file. Orchestrator dispatches one subagent per issue following `subagent-development` methodology, each invoking the `tdd` skill. Code review runs between each subagent dispatch.
- **Record:** Branch name in state file. Each issue status as implementation progresses.

### Implement → Code Review

- **Validate:** All implementation issues resolved, tests passing
- **Handoff:** Invoke `code-review` against all changed files on the feature branch
- **Gate:** If blocking issues found → fix them, re-run review. Loop until clean.

### Code Review → PR

- **Validate:** Code review passed with no blocking issues
- **Handoff:** Invoke `commit` for conventional commit, then `github-cli` to open PR from `feat/{feature-slug}` to main
- **Record:** PR URL in state file, set feature status to `completed`

---

## Failure & Recovery

### Phase Retry

If a phase fails (e.g., `gh` not authenticated, skill invocation errors), the orchestrator:

1. Logs the failure reason in the state file log
2. Sets the phase status to `blocked` with a description of the blocker
3. Presents the error to the user and suggests resolution steps
4. On the next invocation, retries the blocked phase from the beginning

### Backwards Transitions

When implementation or code review reveals the approach is fundamentally wrong:

1. The user or orchestrator identifies the need to rework the plan
2. Log the reason for the backwards transition
3. Reset phases from `plan` onward to `pending`
4. Re-enter Phase 2 (Plan) — CEO Review and Issues must run again on the revised plan
5. The feature branch is kept; implementation continues on the same branch after the revised plan

Valid backwards transitions:

- `implement → plan` — approach is wrong, plan needs rework
- `code_review → plan` — architectural issues found that require plan changes

All other backwards transitions are not supported. If the PRD itself is wrong, abandon the feature and start a new one.

### Feature Abandonment

If the user decides to stop working on a feature:

1. Set `status: abandoned` in the state file frontmatter
2. Log the reason and timestamp
3. The state file remains as an audit record
4. If a feature branch exists, leave it (do not auto-delete)

The user can later reference abandoned features for context but cannot resume them. To restart, create a new feature.

---

## Skill File Structure

```text
core/skills/dev-cycle/
├── SKILL.md                    # Trigger conditions, phase overview, orchestration logic
└── references/
    ├── phase-transitions.md    # Detailed glue layer specs per transition
    └── state-file-schema.md   # State file format, field definitions, valid transitions
```

### SKILL.md Contents

- **Frontmatter:** `name: dev-cycle`, description with trigger keywords
- **Trigger conditions:** User says "dev cycle", "development workflow", "full development pipeline", "development pipeline", or invokes `/dev-cycle`. **Disambiguation:** If the user only wants a PRD, route to `write-a-prd`. If they only want a plan, route to `prd-to-plan`. This skill is for the full end-to-end lifecycle.
- **Quick start:** The 7-phase pipeline table
- **Orchestration flow:** Re-entry logic, phase detection, glue layer summaries
- **Phase delegation table:** Which skill each phase invokes

### references/phase-transitions.md

- Detailed glue layer validation rules, handoff context, and artifact expectations per transition
- Failure & recovery procedures per phase

### references/state-file-schema.md

- Full state file template with all fields
- Valid values for each field
- Phase transition rules and gate conditions
- Backwards transition rules

### Registration

The skill gets added to `core/CLAUDE-base.md` alongside the existing 17 skills so it appears in every preset's built `CLAUDE.md`.

---

## Design Decisions

1. **Dispatcher + Glue Layer over Monolithic:** Reuses existing skills so improvements propagate automatically. Glue layer adds reliable handoffs without reimplementing skill logic.

2. **Mandatory phases:** No skipping ensures consistent quality. Every feature goes through the full rigor of brainstorming, formal PRD, planned implementation, review, and proper PR workflow.

3. **State file over artifact detection:** Explicit state is more reliable than inferring progress from the environment. Also provides an audit trail.

4. **Code review as hard gate:** PR cannot be created until code review passes with no blocking issues. This enforces quality before code reaches the repository.

5. **CEO Review recommends HOLD SCOPE:** The orchestrator recommends maximum rigor but respects the skill's own mode-selection logic. The user retains control over the review mode.

6. **Core skill, not preset-specific:** This workflow is universal regardless of project type. Every preset benefits from a structured development lifecycle.

7. **7 phases, not 8:** Brainstorm and PRD are a single phase because `write-a-prd` is a single skill with its own internal interview-to-formalization flow. Splitting it would require modifying the existing skill.

8. **Context loading on resume:** The orchestrator reads all referenced artifacts (GitHub issues, plan files, branch state) when resuming, rather than relying solely on the state file's summary data. This ensures full context is available in new conversations.

9. **Feature branches at Phase 5:** Code-producing phases (Implement, Code Review, PR) run on a dedicated feature branch. Documentation phases (Brainstorm through Issues) run on the current branch since they produce docs and GitHub issues, not code.

10. **Backwards transitions limited to plan rework:** Only `implement → plan` and `code_review → plan` are supported. If the PRD is wrong, the feature should be abandoned and restarted. This prevents unbounded loops in the pipeline.
