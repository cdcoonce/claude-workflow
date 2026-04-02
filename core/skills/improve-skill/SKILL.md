---
name: improve-skill
description: >
  Benchmark-driven skill improvement pipeline. Interviews the user to build
  a test suite, scores the original skill, iterates with a Skill Writer and
  QA Tester loop until the target pass rate is reached, then files a PR.
  Use when user says "improve skill", "benchmark skill", "make skill better",
  or invokes /improve-skill.
---

# Improve-Skill Orchestrator

Run a benchmark-driven improvement loop on any skill: interview → baseline → iterate → PR.

## Pipeline Overview

| #   | Phase            | Summary                                                      |
| --- | ---------------- | ------------------------------------------------------------ |
| 1   | **Orchestrator** | Resolve slug, load or create state file (this phase)         |
| 2   | **Grill**        | Interview user to build/extend `tests.md`                    |
| 3   | **Baseline**     | QA Tester agent scores the original skill                    |
| 4   | **Iterate**      | Skill Writer + QA Tester loop on `improve/{slug}` branch     |
| 5   | **Finalize**     | Report + PR + score ledger + state archive                   |
| 6   | **Agents**       | `qa-tester`, `skill-writer`, `strategy` AGENT.md definitions |

## Phase 1: Orchestrator

### Step 1 — Parse slug

Usage: `/improve-skill <slug>`. If no slug given, reply with usage and stop.

### Step 2 — Resolve skill path

Check in order (first match wins):

1. `core/skills/{slug}/SKILL.md`
2. `presets/*/skills/{slug}/SKILL.md`

If not found, abort:

> Error: no skill found for slug "{slug}". Searched `core/skills/{slug}/SKILL.md` and `presets/*/skills/{slug}/SKILL.md`.

Record the resolved path as `skill_path`.

### Step 3 — Check for in-progress state file

Look for `docs/skill-improve/{slug}.state.md`.

- **Found, `status: in_progress`:** Read `current_phase` and `best_score`. Report: "Resuming **{slug}** at phase **{current_phase}** (best score: {best_score}%)." Jump to that phase.
- **Found, other status:** Notify user, start a new run (suffix slug with `-2`, `-3` etc. to avoid collision).
- **Not found:** Proceed to Step 4.

### Step 4 — Create state file

Write `docs/skill-improve/{slug}.state.md` (see `state-schema.md` for template). Set `status: in_progress`, `current_phase: grill`. Confirm: "State file created at `docs/skill-improve/{slug}.state.md`." Then proceed to Phase 2.

---

## Phase 2: Grill

(See Phase 2 details — added in subsequent task)

## Phase 3: Baseline

(See Phase 3 details — added in subsequent task)

## Phase 4: Iterate

(See Phase 4 details — added in subsequent task)

## Phase 5: Finalize

(See Phase 5 details — added in subsequent task)

## Phase 6: Agent Definitions

(See Phase 6 details — added in subsequent task)
