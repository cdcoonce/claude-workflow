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

## Phase 1: Orchestrator

**Step 1 — Parse slug:** Usage: `/improve-skill <slug>`. If no slug given, reply with usage and stop.

**Step 2 — Resolve skill path:** Check `core/skills/{slug}/SKILL.md`, then `presets/*/skills/{slug}/SKILL.md`. If not found, abort: `Error: no skill found for slug "{slug}". Searched core/skills/{slug}/SKILL.md and presets/*/skills/{slug}/SKILL.md.` Record resolved path as `skill_path`. Derive `tests_path` as the directory of `skill_path` plus `/tests.md`.

**Step 3 — Check state file:** Look for `docs/skill-improve/{slug}.state.md`.

- **`status: in_progress`:** Read `skill_path`, `current_phase`, `best_score`. Verify `skill_path` exists on disk. Report: "Resuming **{slug}** at phase **{current_phase}** (best score: {best_score}%)." Jump to that phase.
- **`status: completed` or `status: abandoned`:** Notify user, start new run (suffix slug with `-2`, `-3` etc.).
- **Not found:** Proceed to Step 4.

**Step 4 — Create state file:** Write `docs/skill-improve/{slug}.state.md`. Set `status: in_progress`, `current_phase: grill`. Log: `{YYYY-MM-DD} — State file created. Skill path: {skill_path}`. Proceed to Phase 2.

---

## Phase 2: Grill

**Step 1 — Check for existing tests.md:** If `{tests_path}` exists: count data rows, show one-line summaries. Ask user what harder or missing cases to add. Append new rows only (never remove; never duplicate T00). Jump to Step 3. If not found: proceed to Step 2.

**Step 2 — Interview:** First, read `{skill_path}` and infer 5–10 suggested test cases from its content. Then conduct the interview using AskUserQuestion if available, otherwise numbered text Q&A.

**If AskUserQuestion is available:** Use it for every question with selectable options (use multiSelect where multiple choices apply):

- Q1: Primary purpose — offer selectable trigger phrases inferred from the skill's description.
- Q2: Critical behaviors — offer selectable options inferred from the skill's steps (multiSelect).
- Q3: Misuse scenarios — offer selectable options inferred from skill edge cases (multiSelect).
- Q4: Edge cases — offer selectable options inferred from the skill (multiSelect).
- Q5: Suggested test cases — present inferred test cases as selectable options (multiSelect); user picks which to include and may add more.
- Q6: How many total tests? (suggest 10–15)

**If AskUserQuestion is NOT available:** Ask questions 1–6 in sequence as numbered plain text. For Q5, list the inferred test cases as numbered suggestions before asking for user additions.

Write `{tests_path}`: columns `| ID | Scenario | Expected Behavior | Result | Reason |`. T00 is always first: Scenario = "Skill SKILL.md must be ≤100 lines", Expected = "Claude counts lines; if >100, reports the violation and halts execution." Number remaining cases T01, T02, etc. If user answered 0 for test count, re-prompt once.

**Step 3 — Set config:** Ask target pass rate (default 90%) and max iterations (default 5). Record in state file. Advance `current_phase` to `baseline`. Log: `{YYYY-MM-DD} — Grill complete. Suite: {total} tests. Target: {rate}%. Max: {max} iterations.`

**Step 4 — Commit:** `git add {tests_path} docs/skill-improve/{slug}.state.md && git commit -m "test({slug}): add benchmark test suite"`

---

## Phase 3: Baseline

Read `references/phase-3-baseline.md` using the Read tool, then follow its instructions exactly.

After completion: `baseline_score` is recorded in state under `baseline_score`; iteration 0 is added to the Scores table; `best_score` is initialized to `baseline_score`.

---

## Phase 4: Iterate

Read `references/phase-4-iterate.md` using the Read tool, then follow its instructions exactly.

The Skill Writer and QA Tester execute as a team across multiple iterations. After each iteration: if score > `best_score`, update `best_score` and `best_iteration` in state; if score < `best_score`, log the regression but preserve `best_score` and `best_iteration`. If two consecutive iterations show no score improvement, invoke the strategy agent to propose a rewrite strategy before the next Skill Writer iteration. Loop continues until target pass rate is met or max iterations is reached.

---

## Phase 5: Finalize

Read `references/phase-5-finalize.md` using the Read tool, then follow its instructions exactly.

After completion: a PR is filed; state file `status` is set to `completed`; state file is archived to `docs/archive/skill-improve/`; a score report is produced showing baseline → best score.

---

## Phase 6: Agent Definitions

Agents live in `core/agents/`: `qa-tester`, `skill-writer`, `strategy`.
