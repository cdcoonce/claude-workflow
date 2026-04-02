# Phase 4: Iterate

Run the benchmark-driven improvement loop on the `improve/{slug}` branch.

## Branch Setup

Check if `improve/{slug}` branch exists:

```
git branch --list improve/{slug}
```

- **Branch exists:** Check it out. Note: "Resuming improvement branch `improve/{slug}`."
- **Branch not found:** Create from current HEAD: `git checkout -b improve/{slug}`. Note: "Created improvement branch `improve/{slug}`."

## Exit Conditions (check at the START of each iteration)

Before running any step, check:

1. `current_score >= target_pass_rate` → exit with reason "target reached"
2. `current_iteration >= max_iterations` → exit with reason "budget exhausted"

On exit: append log entry `{YYYY-MM-DD} — Loop exited: {exit_reason}. Final score: {current_score}%.` Do NOT advance `current_phase` yet — that happens in Phase 5.

## Iteration Steps

Repeat the following steps A–H until an exit condition is met.

### Step A — Read current skill

Read `{skill_path}`. This file always reflects the best version (regression handling in Step G ensures this).

### Step B — Read annotated failures

Read `core/skills/{slug}/tests.md`. Extract all rows where Result = `fail`. These are the failure cases to address.

### Step C — Dispatch Skill Writer

Adopt the `skill-writer` agent identity. Provide:

- Full skill content (from Step A)
- Annotated failure rows (from Step B)
- Strategy guidance (if available from Step H of a previous iteration)

Receive: complete rewritten SKILL.md content (valid Markdown with YAML frontmatter, ≤100 lines).

**Malformed output handling:** If output is not valid Markdown with frontmatter, or exceeds 100 lines, retry once. If the second attempt also fails, pause and prompt the user:

> "Skill Writer produced malformed output twice. Please inspect and advise before continuing."

### Step D — Commit rewrite

Overwrite `{skill_path}` with the Skill Writer output. Commit to the improve branch:

```
feat({slug}): skill improvement iteration {n}
```

### Step E — Dispatch QA Tester

Adopt the `qa-tester` agent identity. Provide the full skill content and the full test suite from `core/skills/{slug}/tests.md`.

Receive: annotated test table (with Result and Reason columns filled) and a score summary line.

**Malformed output handling:** If output lacks a valid table or score summary, retry once. If the second attempt also fails, pause and prompt the user:

> "QA Tester produced malformed output twice. Please inspect and advise before continuing."

### Step F — Record score

1. Write the annotated table back to `core/skills/{slug}/tests.md` (overwrite).
2. Add a row to the Scores table in the state file: `| {n} | {pct}% | |`
3. Increment `current_iteration` in the state file.
4. Append log entry: `{YYYY-MM-DD} — Iteration {n}: {pct}%. Previous best: {best_score}%.`

### Step G — Update best / handle regression

Compare `new_score` to `best_score`:

- **Improvement** (`new_score > best_score`): Update `best_score` and `best_iteration` in state file. Note: "New best: {pct}%."
- **Regression** (`new_score < best_score`): Warn the user. Revert `{skill_path}` to the previous best version:
  ```
  git checkout HEAD~1 -- {skill_path}
  ```
  Note: "Regression ({new_pct}% < {best_pct}%). Reverted to best version."
- **No change** (`new_score == best_score`): Increment internal stall count. Note: "No improvement. Stall count: {stall_count}."

### Step H — Strategy agent check

If the score has been unchanged for 2 consecutive iterations (stall count ≥ 2):

1. Adopt the `strategy` agent identity. Provide:
   - Full current skill content
   - All iteration scores from the Scores table
   - All annotated failure tables from this run
2. Receive: a concrete rewrite strategy (plain text).
3. Store strategy text to pass as additional context in the next Step C call.
4. Reset the stall count to 0.
5. Note: "Strategy agent dispatched. Stall count reset."

Return to top of loop and check exit conditions before the next iteration.
