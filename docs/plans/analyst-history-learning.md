# Plan: Analyst History Learning (Deferred)

> Depends on: improve-skill grill redesign (#61) shipping first
> Priority: P2 | Effort: M

## Context

The skill-analyst agent currently analyzes a SKILL.md in isolation. After the grill redesign ships, the analyst could be enhanced to receive past run reports (score trajectories, failure patterns) as additional context, so it identifies which types of gaps historically yield the most improvement per iteration.

## Why

Makes each successive run smarter. The analyst doesn't just analyze the skill — it knows what worked before. Compounding improvement across runs.

## What to build

Extend the skill-analyst's input contract to accept an optional "run history" section containing:

- Past score trajectories from archived state files
- Failure patterns from past iterations (which tests failed repeatedly)
- Score ledger data for the skill

The analyst uses this to bias toward findings in areas where past runs struggled, and away from areas already well-covered.

## Trade-offs

- **Pros:** Higher-quality test suites on repeated runs, compounding improvement
- **Cons:** More tokens per dispatch, needs run history to be structured/accessible
- **Starting point:** The score ledger (`docs/skill-scores.md`) and archived state files (`docs/archive/skill-improve/`) provide the raw data. The analyst's input contract already supports optional additional context.
