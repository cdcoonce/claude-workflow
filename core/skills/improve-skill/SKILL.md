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

- **Found, `status: in_progress`:** Read `skill_path`, `current_phase`, and `best_score` from state. Verify `skill_path` still exists on disk; if not, abort with an error. Report: "Resuming **{slug}** at phase **{current_phase}** (best score: {best_score}%)." Jump to that phase.
- **Found, `status: completed` or `status: abandoned`:** Notify user, start a new run (suffix slug with `-2`, `-3` etc. to avoid collision).
- **Not found:** Proceed to Step 4.

### Step 4 — Create state file

Write `docs/skill-improve/{slug}.state.md` (see `state-schema.md` for template). Set `status: in_progress`, `current_phase: grill`. Append a log entry: `{YYYY-MM-DD} — State file created. Skill path: {skill_path}`. Confirm: "State file created at `docs/skill-improve/{slug}.state.md`." Then proceed to Phase 2.

---

## Phase 2: Grill

### Step 1 — Check for existing tests.md

Check `core/skills/{slug}/tests.md`.

**If found:** Count data rows (excluding header). Show: "Found {N} existing tests for {slug}: [one-line summary per scenario]." Ask: "What harder or missing cases should I add? (press Enter to keep existing suite.)" If user provides cases, append them as new rows (never remove existing rows; never add a T00 row if one already exists in the file). If user skips, keep suite as-is. Jump to Step 3.

**If not found:** Proceed to Step 2.

### Step 2 — Interview (AskUserQuestion if available, else numbered text Q&A)

Ask in sequence:

1. What is this skill's primary purpose and when should it trigger?
2. What are the 3 most critical behaviors it must always do correctly?
3. What would misuse or incorrect triggering look like?
4. What edge cases or unusual inputs must it handle?
5. How many test cases do you want? (suggest 10–15)

Write `core/skills/{slug}/tests.md` with columns: `| ID | Scenario | Expected Behavior | Result | Reason |`. T00 is always first: Scenario = "Skill SKILL.md must be ≤100 lines", Expected = "Claude counts lines and stops if exceeded." Number remaining cases T01, T02, etc.

### Step 3 — Set config

Ask: "Target pass rate? (default: 90%)" and "Max iterations? (default: 5)". Record both in state file. Advance `current_phase` to `baseline`. Append log entry: `{YYYY-MM-DD} — Grill complete. {N} tests written. Target: {rate}%. Max iterations: {max}.`

## Phase 3: Baseline

(See Phase 3 details — added in subsequent task)

## Phase 4: Iterate

(See Phase 4 details — added in subsequent task)

## Phase 5: Finalize

(See Phase 5 details — added in subsequent task)

## Phase 6: Agent Definitions

(See Phase 6 details — added in subsequent task)
