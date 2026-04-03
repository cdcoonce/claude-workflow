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

Read `references/phase-2-grill.md` using the Read tool, then follow its instructions exactly.

After completion: test suite is written to `{tests_path}`; config (target pass rate, max iterations) is recorded in the state file; `current_phase` is advanced to `baseline`.

---

## Phase 3: Baseline

Read `references/phase-3-baseline.md` using the Read tool, then follow its instructions exactly.

After completion: `baseline_score` is recorded in state under `baseline_score`; iteration 0 is added to the Scores table; `best_score` is initialized to `baseline_score`.

---

## Phase 4: Iterate

Read `references/phase-4-iterate.md` using the Read tool, then follow its instructions exactly.

The Skill Writer and QA Tester execute as a team across multiple iterations. After each iteration: if score > `best_score` (improvement), update `best_score` and `best_iteration` in state and reset `stall_count` to 0; if score ≤ `best_score` (tie or regression), increment `stall_count` by 1 — additionally, if score < `best_score` (regression), log the regression, preserve `best_score` and `best_iteration`, and revert to the best known SKILL.md. When `stall_count` >= 2, invoke the strategy agent to propose a rewrite strategy before the next Skill Writer iteration begins, then reset `stall_count` to 0. Loop continues until target pass rate is met or max iterations is reached.

---

## Phase 5: Finalize

Read `references/phase-5-finalize.md` using the Read tool, then follow its instructions exactly.

After completion: a PR is filed using the SKILL.md content from `best_iteration` (not the most recent rewrite); state file `status` is set to `completed`; state file is archived to `docs/archive/skill-improve/`; a score report is produced showing baseline → best score.

---

## Phase 6: Agent Definitions

Agents live in `core/agents/`: `skill-analyst`, `qa-tester`, `skill-writer`, `strategy`.
