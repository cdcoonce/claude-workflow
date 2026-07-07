# Plan: improve-skill — AutoResearch-Style Benchmark-Driven Skill Improvement

> Source PRD: [#52](https://github.com/cdcoonce/claude-workflow/issues/52)

## Architectural Decisions

Durable decisions that apply across all phases:

- **Skill resolution**: Accept a skill name slug (e.g., `tdd`) and resolve to the first matching `SKILL.md` under `core/skills/` or `presets/*/skills/`. Abort with a clear message if not found.
- **State file location**: `docs/skill-improve/{slug}.state.md` — same re-entry pattern as dev-cycle. Scan on invocation; resume if `status: in_progress`.
- **Test suite location**: `core/skills/{slug}/tests.md` — versioned alongside the skill. Persisted across runs. Grows harder with each run via grill phase appends.
- **Test case schema**: Columns — `ID`, `Scenario`, `Expected Behavior`, `Result`, `Reason`. T00 structural test (100-line limit) always present as first row.
- **Test ratchet**: Suite is fixed within a run. Between runs, grill phase shows existing tests and appends harder cases targeting previous gaps. Tests are never removed.
- **Branch naming**: `improve/{slug}` — created at start of Phase 4. On collision, resume on existing branch (regression logic ensures best version always wins).
- **Agent definitions**: Three AGENT.md files in `core/agents/`: `qa-tester`, `skill-writer`, `strategy`. New role vocabulary: `qa-tester`, `skill-writer`, `strategy`.
- **Agent interface**: Each subagent receives file content as context (not file paths). Returns structured markdown output.
- **Best-version tracking**: State file records `best_score` and `best_iteration`. Skill Writer always receives the best-scoring version, not the most recent.
- **Score ledger**: `docs/skill-scores.md` — one row appended per completed run: skill, date, test count, baseline, final score, iterations used, target met.

---

## Phase 1: Orchestrator Skeleton + State File

User stories: 1, 21, 23

Resolves the skill slug to a `SKILL.md` path. Checks `docs/skill-improve/` for an existing in-progress state file and resumes if found, otherwise creates a new state file and proceeds to Phase 2. The pipeline is re-entrant from any phase.

Acceptance criteria:

- [ ] `/improve-skill tdd` resolves to the correct SKILL.md path under `core/skills/` or `presets/*/skills/`
- [ ] Invocation with no matching skill aborts with a clear error message naming the slug and searched paths
- [ ] If a `{slug}.state.md` with `status: in_progress` exists, the skill resumes at `current_phase`
- [ ] A new state file is created at `docs/skill-improve/{slug}.state.md` with `status: in_progress` and `current_phase: grill`
- [ ] State file records `skill_path`, `created`, `updated`, `best_score`, `best_iteration` fields on creation

---

## Phase 2: Grill Phase — Test Suite Generation

User stories: 4, 5, 6, 7, 8

Checks for an existing `core/skills/{slug}/tests.md`. If found: shows the user a summary of existing tests and asks what harder or missing cases to append. If not found: runs the full AskUserQuestion interview to generate an initial suite. In both cases, writes or appends to `core/skills/{slug}/tests.md`. T00 (100-line structural test) is always present as the first row. Config (`target_pass_rate`, `max_iterations`) is set and recorded in the state file.

Acceptance criteria:

- [ ] Checks for `core/skills/{slug}/tests.md` before starting interview
- [ ] If tests.md exists: shows test count + scenario summary, then asks what harder/missing cases to append
- [ ] If tests.md does not exist: runs full AskUserQuestion interview (skill purpose, critical behaviors, misuse, edge cases, test count)
- [ ] Falls back to text-based Q&A if AskUserQuestion is unavailable
- [ ] Test suite written/appended to `core/skills/{slug}/tests.md` with columns: ID, Scenario, Expected Behavior, Result, Reason
- [ ] T00 structural test (skill must be ≤100 lines) is always the first row and never duplicated on append
- [ ] `target_pass_rate` and `max_iterations` recorded in state file
- [ ] State file `current_phase` advances to `baseline`

---

## Phase 3: Baseline Scoring — QA Tester

User stories: 9, 10, 11

Dispatches the QA Tester agent (`core/agents/qa-tester/`) with the original skill content and test suite. QA Tester judges each test pass/fail and returns an annotated test table with one-line reasoning per failure. Baseline score is recorded in the state file. If the baseline already meets `target_pass_rate`, the user is asked to raise the target before continuing.

Acceptance criteria:

- [ ] QA Tester agent receives full SKILL.md content and test suite table
- [ ] Returns annotated test table with Result (pass/fail) and Reason columns filled
- [ ] Baseline score recorded in state file as `baseline_score` and added to scores table
- [ ] If `baseline_score >= target_pass_rate`: user is prompted to raise the target; loop does not start until target is raised
- [ ] State file `current_phase` advances to `iterate`

---

## Phase 4: Iterate Loop — Skill Writer + QA Tester + Strategy

User stories: 2, 3, 12, 13, 14, 15, 16, 17, 22

The core improvement loop on the `improve/{slug}` branch. On Phase 4 start: check if branch exists and check out (resume) or create it. Each iteration: Skill Writer agent receives the best-scoring skill and annotated failure table → rewrites SKILL.md → committed to branch → QA Tester scores the rewrite → score recorded. Strategy agent activates when score is unchanged for 2 consecutive iterations, producing a rewrite strategy passed as additional context to Skill Writer. Auto-reverts to best-scoring version on regression. Loop exits when `score >= target_pass_rate` or `current_iteration == max_iterations`. Malformed subagent output triggers one retry, then pauses for user.

Acceptance criteria:

- [ ] If `improve/{slug}` branch exists, check it out and resume; if not, create it
- [ ] Each Skill Writer pass overwrites the working skill file and is committed to the branch
- [ ] Each QA Tester pass returns an annotated test table; score recorded in state file scores table
- [ ] `best_score` and `best_iteration` updated in state file after each iteration
- [ ] Regression detected when `new_score < best_score`: user warned, skill reverted to best version, loop continues
- [ ] Strategy agent dispatched when score unchanged for 2 consecutive iterations; its output passed to Skill Writer as additional context
- [ ] Malformed subagent output triggers one retry; second failure pauses loop with user prompt
- [ ] Loop exits cleanly on target reached or budget exhausted; state file records exit reason
- [ ] State file `current_iteration` incremented after each full iteration

---

## Phase 5: Finalize — Report + PR + Score Ledger

User stories: 18, 19, 20, 24

Writes the best-scoring skill back to its original `skill_path`. Clears the `Result` and `Reason` columns in `core/skills/{slug}/tests.md` (preserving test cases for the next run). Generates a report at `docs/skill-improve/{slug}-report.md` and appends a row to `docs/skill-scores.md`. Commits all artifacts via the `commit` skill, then opens a PR to the default branch. Archives the state file.

Acceptance criteria:

- [ ] Best-scoring skill written to original `skill_path`
- [ ] `Result` and `Reason` columns in `core/skills/{slug}/tests.md` cleared; test cases and T00 preserved for next run
- [ ] Report written to `docs/skill-improve/{slug}-report.md` with: scores-per-iteration table, tests fixed, tests still failing
- [ ] Row appended to `docs/skill-scores.md`: skill, date, test count, baseline score, final score, iterations used, target met (yes/no)
- [ ] All changes committed on `improve/{slug}` branch via `commit` skill
- [ ] PR opened to default branch with title `improve({slug}): benchmark-driven skill improvement` referencing issue #52
- [ ] State file `status` set to `completed`, archived to `docs/archive/skill-improve/`
- [ ] If max iterations hit without reaching target, report notes the gap (e.g., "Reached 80%, target was 90%")

---

## Phase 6: Agent Definitions

User stories: 11, 12, 13 (expansion)

Three AGENT.md files in `core/agents/`, each defining: frontmatter (name, description, role), input contract, output contract, and constraints. These agents are dispatched by the improve-skill orchestrator in Phases 3–4.

`core/agents/qa-tester/AGENT.md`

- Role: `qa-tester`
- Input: SKILL.md content + test suite table (ID, Scenario, Expected Behavior)
- Output: annotated test table with Result (pass/fail) and Reason per row; score summary line
- Constraints: must fill every Result cell; Reason must reference specific skill language

`core/agents/skill-writer/AGENT.md`

- Role: `skill-writer`
- Input: current SKILL.md content + annotated failure table + (optional) strategy guidance
- Output: complete rewritten SKILL.md content only (no other text)
- Constraints: output must be ≤100 lines; preserve skill frontmatter name/description; do not remove passing test behaviors

`core/agents/strategy/AGENT.md`

- Role: `strategy`
- Input: SKILL.md content + full test history (scores per iteration + annotated failure tables)
- Output: a concise rewrite strategy (what the Skill Writer should try that it hasn't tried yet)
- Constraints: must identify a specific pattern in recurring failures; must propose a concrete structural change

Acceptance criteria:

- [ ] `core/agents/qa-tester/AGENT.md` created with role, input/output contract, constraints
- [ ] `core/agents/skill-writer/AGENT.md` created with role, input/output contract, constraints
- [ ] `core/agents/strategy/AGENT.md` created with role, input/output contract, constraints
- [ ] All three agents discoverable by dev-cycle agent-matching algorithm (description-based)
- [ ] Each agent's description clearly states when it should be matched
