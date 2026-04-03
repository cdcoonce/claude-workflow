# Phase 2: Grill

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
