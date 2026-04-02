# Phase 3: Baseline — Detailed Instructions

Run the QA Tester agent against the original skill to establish a baseline score.

## Step 1 — Read skill content

Read the full content of `{skill_path}` (resolved in Phase 1).

## Step 2 — Read test suite

Read `core/skills/{slug}/tests.md`. This is the test table with columns:
`| ID | Scenario | Expected Behavior | Result | Reason |`

The Result and Reason columns are blank — either cleared after a previous run or freshly created. Do not modify them before dispatching the QA Tester.

## Step 3 — Dispatch QA Tester

Dispatch a subagent using the `qa-tester` agent identity (defined in Phase 6).

Provide the subagent with:

- The **full SKILL.md content** (paste the entire file text — do not give the path)
- The **full test suite table** (paste the entire table — do not give the path)

Instruct the QA Tester to:

1. For each test row, evaluate whether the skill content would cause Claude to produce the Expected Behavior for the given Scenario.
2. Fill in `Result` as `pass` or `fail` for every row.
3. Fill in `Reason` with a concise one-sentence explanation for every row.
4. Return the fully annotated table.
5. Return a summary line in the format: `Score: {N}/{total} = {pct}%`

Wait for the QA Tester subagent to return before proceeding.

## Step 4 — Record baseline

After the QA Tester returns:

1. **Write the annotated table** back to `core/skills/{slug}/tests.md` (overwrite the file with the annotated version).

2. **Update the state file** (`docs/skill-improve/{slug}.state.md`):
   - Set `baseline_score: {pct}` (integer percentage, e.g. `73`)
   - Add a row to the Scores table: `| 0 | {pct}% | Baseline |`
   - Advance `current_phase` to `iterate`

3. **Append a log entry**:
   ```
   {YYYY-MM-DD} — Baseline score: {pct}%. {N}/{total} tests passed.
   ```

## Step 5 — Check baseline vs target

Compare `baseline_score` to `target_pass_rate` (both from state file).

**If `baseline_score >= target_pass_rate`:**

Inform the user:

> Baseline score ({pct}%) already meets or exceeds the target ({target}%). Please raise the target pass rate before we proceed.
> Current target: {target}%. Suggested new target: {suggested}% (10 percentage points above baseline, capped at 100%).

Wait for the user to provide a new target. Validate that the new target is:

- A percentage between 1 and 100
- Strictly greater than `baseline_score`

Update `target_pass_rate` in the state file with the new value. Append a log entry:

```
{YYYY-MM-DD} — Target raised to {new_target}% (was {old_target}%) because baseline already met target.
```

Do **not** start Phase 4 until the target is raised and validated.

**If `baseline_score < target_pass_rate`:**

Report to the user:

> Baseline: {pct}% ({N}/{total} tests passed). Target: {target}%. Gap: {gap} percentage points. Starting improvement loop.

Proceed immediately to Phase 4.
