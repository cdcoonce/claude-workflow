# Plan: Improve-Skill Grill Phase Redesign

> Source PRD: https://github.com/cdcoonce/claude-workflow/issues/61

## Architectural decisions

Durable decisions that apply across all phases:

- **Agent pattern**: `core/agents/{name}/AGENT.md` with YAML frontmatter (name, description, role, skills.add/remove) — follows existing qa-tester/skill-writer/strategy pattern
- **Reference file pattern**: Phase instructions extracted to `core/skills/improve-skill/references/phase-{n}-{name}.md`, delegated from SKILL.md with "Read this file and follow its instructions exactly"
- **Test suite format**: `| ID | Scenario | Expected Behavior | Result | Reason |` — unchanged, consumed identically by QA Tester and Skill Writer
- **Agent input contract**: Full file content pasted inline (not paths) — same as existing agents
- **Agent output contract**: Structured Markdown with defined sections — parseable by the orchestrator
- **Malformed output handling**: Retry once, then prompt user — consistent with phases 3-4
- **Phase 2 logging**: Analyst dispatch, challenge results, and grill completion logged to state file

---

## Phase 1: Skill Analyst Agent

**User stories**: #7 (minimum findings per tier), #10 (independently testable)

### What to build

Create the `skill-analyst` agent — a new agent that analyzes a skill's SKILL.md for weaknesses across three tiers: Surface Gaps, Behavioral Edge Cases, and Adversarial Probes. The agent receives the full skill content (and optionally existing test summaries) and returns a structured weakness report with proposed test cases at each tier.

Also create the agent's own `tests.md` test suite so the agent can be improved via the improve-skill pipeline itself.

### Acceptance criteria

- [ ] `core/agents/skill-analyst/AGENT.md` exists with valid YAML frontmatter (name, description, role: analyst, skills.add/remove)
- [ ] Agent defines clear input contract: full SKILL.md content pasted inline, optional existing test summaries
- [ ] Agent defines clear output contract: three-tier report (Surface Gaps, Behavioral Edge Cases, Adversarial Probes) with findings containing proposed tests and "why it matters" context
- [ ] Agent enforces minimum 2 findings per tier
- [ ] Agent enforces that proposed tests must be pass/fail evaluable (not vague)
- [ ] Agent enforces that findings must not restate what the skill already explicitly handles
- [ ] `core/agents/skill-analyst/tests.md` exists with test cases covering output format, minimum findings, test specificity, no-restatement constraint, and existing-tests handling

---

## Phase 2: Extract Phase 2 to Reference File

**User stories**: None directly — structural refactor enabling Phase 3

### What to build

Move the current Phase 2 (Grill) instructions from SKILL.md into a new `references/phase-2-grill.md` file. Replace the inline Phase 2 content in SKILL.md with: "Read `references/phase-2-grill.md` using the Read tool, then follow its instructions exactly." This is a behavior-preserving refactor — the grill phase works identically before and after.

### Acceptance criteria

- [ ] `core/skills/improve-skill/references/phase-2-grill.md` exists with the full current Phase 2 instructions
- [ ] SKILL.md Phase 2 section is replaced with a delegation line matching the pattern used by Phases 3, 4, and 5
- [ ] SKILL.md remains under 100 lines
- [ ] No behavioral change — the grill phase operates identically to before the refactor

---

## Phase 3: Redesign Phase 2 Flow

**User stories**: #1, #2, #3, #4, #5, #6, #8, #9

### What to build

Rewrite `references/phase-2-grill.md` to replace the fixed 6-question interview with the analyst-driven flow: dispatch skill-analyst agent, present findings tier-by-tier for user challenge, assemble test suite from accepted findings, set config, commit.

The analyst always runs — even when tests.md already exists. When existing tests are present, the analyst receives both the SKILL.md and existing test summaries so it identifies gaps not already covered. Accepted findings are appended as new test rows; existing rows are preserved.

Update SKILL.md Phase 6 to include `skill-analyst` in the agent list. Update the improve-skill test suite (T06-T10, T16-T17) to reflect the new grill behavior.

### Acceptance criteria

- [ ] `references/phase-2-grill.md` implements: Step 1 (Dispatch Skill Analyst), Step 2 (User Challenge Loop), Step 3 (Assemble Test Suite), Step 4 (Set Config), Step 5 (Commit)
- [ ] Step 1 dispatches skill-analyst with full SKILL.md content; when tests.md exists, also sends existing test summaries. Malformed output (missing tiers, <2 findings/tier) triggers retry once, then prompts user.
- [ ] Step 1 logs: analyst dispatched, findings count per tier
- [ ] Step 2 presents findings tier-by-tier; uses AskUserQuestion with multiSelect when available, falls back to text
- [ ] Step 2 allows user to deselect irrelevant findings and add domain-specific gaps per tier
- [ ] Step 2 guards against full rejection: if zero findings accepted across all tiers, re-run analyst with user guidance on what gaps they're looking for
- [ ] Step 2 logs: accepted/rejected counts, user additions
- [ ] Step 3 places T00 first, groups accepted findings by tier, appends to existing tests when present, confirms total count
- [ ] SKILL.md Phase 6 lists `skill-analyst` alongside `qa-tester`, `skill-writer`, `strategy`
- [ ] Tests T06-T10 updated: T06 tests analyst dispatch, T07 tests text fallback for challenge loop, T08 tests analyst runs when no tests.md exists, T09 tests analyst identifies gaps when tests.md exists, T10 tests T00 placement
- [ ] Tests T16-T17 updated as needed for new flow (zero-test re-prompt, commit step)
- [ ] T24 added: malformed analyst output triggers retry once, then prompts user
- [ ] T25 added: full rejection of all findings triggers analyst re-run with user guidance
