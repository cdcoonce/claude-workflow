# Dev Cycle Orchestrator — Design Spec

## Overview

A new core skill (`/dev-cycle`) that orchestrates the full GitHub-issues-driven development lifecycle. It enforces a strict 8-phase pipeline, delegates heavy lifting to existing skills, and uses a glue layer + state file for reliable handoffs and cross-conversation resume.

**Approach:** Dispatcher + Glue Layer (Approach C) — existing skills do the work, the orchestrator handles sequencing, validation, and state tracking.

**Location:** `core/skills/dev-cycle/` — universal, available to all presets.

---

## The 8-Phase Pipeline

Every phase is mandatory. No phase can be skipped.

| #   | Phase           | Delegates To                      | Artifact Produced                      | Gate Condition                    |
| --- | --------------- | --------------------------------- | -------------------------------------- | --------------------------------- |
| 1   | **Brainstorm**  | `write-a-prd` (interview portion) | Clarified requirements                 | User confirms understanding       |
| 2   | **PRD**         | `write-a-prd` (formalization)     | GitHub Issue (PRD)                     | Issue URL recorded                |
| 3   | **Plan**        | `prd-to-plan`                     | `./plans/{feature}.md`                 | Plan file exists                  |
| 4   | **CEO Review**  | `plan-ceo-review`                 | Reviewed/revised plan                  | Review complete, user approves    |
| 5   | **Issues**      | `prd-to-issues`                   | GitHub Issues (implementation tickets) | All issue URLs recorded           |
| 6   | **Implement**   | `tdd` + `subagent-development`    | Working code + passing tests           | All issues resolved, tests pass   |
| 7   | **Code Review** | `code-review`                     | Review report, issues fixed            | Clean review (no blocking issues) |
| 8   | **PR**          | `commit` + `github-cli`           | Pull request                           | PR URL recorded                   |

**Phases 1 & 2** both delegate to `write-a-prd`. Phase 1 is the interview/brainstorm portion; phase 2 is the formalization into a GitHub issue. The gate between them is the user confirming requirements are understood before formalization begins.

---

## State File

Each feature gets a tracking file at `docs/dev-cycle/{feature-slug}.md`. This is the single source of truth for where a feature stands in the pipeline.

### Format

```markdown
---
feature: dark-mode-toggle
status: in_progress # not_started | in_progress | completed
current_phase: plan # brainstorm | prd | plan | ceo_review | issues | implement | code_review | pr
created: 2026-03-21
updated: 2026-03-21
---

## Artifacts

| Phase       | Status      | Artifact                               |
| ----------- | ----------- | -------------------------------------- |
| brainstorm  | completed   | Requirements confirmed by user         |
| prd         | completed   | https://github.com/user/repo/issues/42 |
| plan        | in_progress | ./plans/dark-mode-toggle.md            |
| ceo_review  | pending     | —                                      |
| issues      | pending     | —                                      |
| implement   | pending     | —                                      |
| code_review | pending     | —                                      |
| pr          | pending     | —                                      |

## Log

- 2026-03-21 10:15 — Brainstorm complete. User confirmed scope.
- 2026-03-21 10:32 — PRD filed as issue #42.
- 2026-03-21 11:01 — Plan started.
```

### Field Definitions

- **feature:** Kebab-case slug used as filename and human-readable identifier.
- **status:** Overall feature status. `not_started` on creation, `in_progress` once phase 1 begins, `completed` once PR is filed.
- **current_phase:** The phase currently being worked on. Valid values: `brainstorm`, `prd`, `plan`, `ceo_review`, `issues`, `implement`, `code_review`, `pr`.
- **created/updated:** ISO date stamps.
- **Artifacts table:** One row per phase. Status is `pending`, `in_progress`, `completed`, or `blocked`. Artifact column holds the output reference (URL, file path, or description).
- **Log:** Timestamped append-only audit trail. Each phase transition adds an entry.

### Valid Phase Transitions

Phases must proceed in strict order. The only valid transition is from the current phase to the next phase in sequence. A phase can only move to `completed` when its gate condition is met.

```
brainstorm → prd → plan → ceo_review → issues → implement → code_review → pr
```

---

## Re-entry & Phase Detection

### First Invocation (no arguments)

1. Check `docs/dev-cycle/` for any state files with `status: in_progress`
2. If one exists → ask "Resume **{feature-name}**? Currently at **{current_phase}**."
3. If multiple exist → list them, ask which to resume
4. If none exist → ask "What feature are you working on?" and start phase 1

### Invocation with Argument (e.g., `/dev-cycle dark-mode-toggle`)

1. Look for `docs/dev-cycle/dark-mode-toggle.md`
2. If found → resume at `current_phase`
3. If not found → create state file, start phase 1

### Cross-Conversation Resume

User starts a new conversation, runs `/dev-cycle`. Orchestrator reads state file, sees `current_phase: implement` and the artifacts collected so far. Picks up exactly where it left off with full context from the state file.

---

## Glue Layer — Phase Transitions

Each transition follows the same pattern: validate artifact → update state → prepare context → invoke next skill.

### Brainstorm → PRD

- **Validate:** User has explicitly confirmed the requirements
- **Handoff:** Pass confirmed requirements context to `write-a-prd` for formalization into a GitHub issue
- **Record:** Note confirmation in log

### PRD → Plan

- **Validate:** GitHub issue URL is present and accessible
- **Handoff:** Pass issue URL to `prd-to-plan`, which reads the PRD issue and breaks it into vertical slices
- **Record:** Plan file path in state file

### Plan → CEO Review

- **Validate:** Plan file exists at recorded path
- **Handoff:** Pass plan file path to `plan-ceo-review` in HOLD SCOPE mode (maximum rigor)
- **Record:** Review outcome + any revisions

### CEO Review → Issues

- **Validate:** Plan has been reviewed and user approved the final version
- **Handoff:** Pass finalized plan to `prd-to-issues` to decompose into GitHub issues
- **Record:** All issue URLs in state file

### Issues → Implement

- **Validate:** All GitHub issues created and URLs recorded
- **Handoff:** Load plan file, execute via `subagent-development` — dispatch `tdd` per issue
- **Record:** Each issue status as implementation progresses

### Implement → Code Review

- **Validate:** All implementation issues resolved, tests passing
- **Handoff:** Invoke `code-review` against all changed files
- **Gate:** If blocking issues found → fix them, re-run review. Loop until clean.

### Code Review → PR

- **Validate:** Code review passed with no blocking issues
- **Handoff:** Invoke `commit` for conventional commit, then `github-cli` to open PR
- **Record:** PR URL in state file, set feature status to `completed`

---

## Skill File Structure

```
core/skills/dev-cycle/
├── SKILL.md                    # Trigger conditions, phase overview, orchestration logic
└── references/
    ├── phase-transitions.md    # Detailed glue layer specs per transition
    └── state-file-schema.md   # State file format, field definitions, valid transitions
```

### SKILL.md Contents

- **Frontmatter:** `name: dev-cycle`, description with trigger keywords
- **Trigger conditions:** User says "dev cycle", "development workflow", "start a feature", "new feature", "resume feature", or invokes `/dev-cycle`
- **Quick start:** The 8-phase pipeline table
- **Orchestration flow:** Re-entry logic, phase detection, glue layer summaries
- **Phase delegation table:** Which skill each phase invokes

### references/phase-transitions.md

- Detailed glue layer validation rules, handoff context, and artifact expectations per transition

### references/state-file-schema.md

- Full state file template with all fields
- Valid values for each field
- Phase transition rules and gate conditions

### Registration

The skill gets added to `core/CLAUDE-base.md` alongside the existing 17 skills so it appears in every preset's built `CLAUDE.md`.

---

## Design Decisions

1. **Dispatcher + Glue Layer over Monolithic:** Reuses existing skills so improvements propagate automatically. Glue layer adds reliable handoffs without reimplementing skill logic.

2. **Mandatory phases:** No skipping ensures consistent quality. Every feature goes through the full rigor of brainstorming, formal PRD, planned implementation, review, and proper PR workflow.

3. **State file over artifact detection:** Explicit state is more reliable than inferring progress from the environment. Also provides an audit trail.

4. **Code review as hard gate:** PR cannot be created until code review passes with no blocking issues. This enforces quality before code reaches the repository.

5. **CEO Review in HOLD SCOPE mode:** Default to maximum rigor. The user can always request EXPANSION or REDUCTION during the review, but the orchestrator defaults to the safest option.

6. **Core skill, not preset-specific:** This workflow is universal regardless of project type. Every preset benefits from a structured development lifecycle.
