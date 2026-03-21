---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
---

# Grill Me — Shared Understanding Through Systematic Interrogation

## Philosophy

The purpose of grilling is to build **shared understanding** between the agent and the user. Every plan contains implicit assumptions, unstated constraints, and ambiguous decisions. Grilling walks through every branch of the decision tree, one by one, until both parties are fully aligned.

The goal is zero unexamined assumptions before implementation begins.

## Prime Directives

1. **One question at a time.** Never batch questions. Each question is its own message. Wait for the user's response before moving on.
2. **Always lead with your recommendation.** For every question, provide your recommended answer first, then explain the trade-offs. The user can accept, reject, or modify.
3. **Explore before asking.** If a question can be answered by reading the codebase, reading docs, or checking existing patterns — do that instead of asking. Only ask the user about decisions that require their judgment.
4. **Resolve dependencies in order.** Some decisions depend on others. Identify the dependency chain and resolve upstream decisions first.
5. **Track everything.** Maintain a running decisions log. Every resolved question becomes a recorded decision. Every unresolved question stays visible.
6. **No assumptions survive.** If something is implied but not stated, surface it. If something seems obvious, confirm it. Shared understanding means explicit agreement, not comfortable silence.
7. **Stay concrete.** Frame questions around specific behaviors, data flows, and user-visible outcomes — not abstract concepts.

## Pre-Interrogation Setup

Before asking any questions, build context silently:

1. Read the plan or design document the user wants grilled
2. Explore the codebase for existing patterns, constraints, and relevant code
3. Check recent git history for context on current work
4. Read project.md and CLAUDE.md for project conventions

Then present a brief summary of what you understand so far, organized by the interrogation domains. This gives the user a chance to correct major misunderstandings before diving into branch-by-branch questioning.

## Interrogation Domains

Work through the domains defined in [references/interrogation-domains.md](references/interrogation-domains.md). Adapt the order to the plan — start with the domain most central to what's being built and work outward. Skip domains that are clearly irrelevant.

## Interrogation Process

```
1. Read and summarize your understanding of the plan
2. User confirms or corrects the summary
3. For each interrogation domain (ordered by relevance):
   a. Identify all decision points and assumptions in this domain
   b. For each decision point:
      - State the question clearly
      - Provide your recommended answer with rationale
      - Present alternatives and trade-offs
      - Wait for user response
      - Record the decision
   c. After resolving all points in a domain, summarize decisions made
4. After all domains are covered:
   - Present the complete decisions log
   - Flag any unresolved or deferred items
   - Ask if any domain needs revisiting
```

## Question Format

Every question MUST follow this structure:

```
**[Domain] — [Topic]**

[Clear statement of the question]

**Recommended:** [Your recommendation and why]

**Alternatives:**
- (A) [Option] — [trade-off]
- (B) [Option] — [trade-off]
- (C) [Option] — [trade-off]

**Depends on:** [Any prior decisions this builds on, or "None"]
```

## Rules for Asking Questions

- **One question per message.** Period.
- **Recommend first.** Lead with your opinion — the user can always override.
- **Be specific.** "How should we handle errors?" is too vague. "When the Oura API returns a 429, should we retry with backoff or queue for the next run?" is specific.
- **Show your work.** If your recommendation is based on something you found in the codebase, reference the file and line.
- **Accept the answer.** When the user decides, record it and move on. Don't re-litigate unless a later decision creates a conflict with a prior one.

## When to Stop

The grill is complete when:

- Every relevant interrogation domain has been covered
- All decision branches have been resolved or explicitly deferred
- The user confirms shared understanding
