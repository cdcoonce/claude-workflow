# Subagent-Driven Development

Execute a plan by dispatching a fresh subagent per task, with code review after each.

**Core principle:** Fresh subagent per task + review between tasks = high quality, fast iteration

## When to Use

- Staying in current session
- Tasks are mostly independent
- Want continuous progress with quality gates

## When NOT to Use

- Need to review plan first
- Tasks are tightly coupled (manual execution better)
- Plan needs revision

## The Process

### 1. Load Plan

Read plan file, create TodoWrite with all tasks.

### 2. Agent Discovery

Before dispatching each subagent, resolve the best-fit agent type from the Agent tool's available `subagent_type` values:

1. **Check system prompt:** The Agent tool description lists all available `subagent_type` values (e.g., `data-pipeline:tdd-implementer:tdd-implementer`, `data-pipeline:code-reviewer:code-reviewer`)
2. **Filter by role:** Use types containing `tdd-implementer` or similar for implementation tasks, `code-reviewer` for review tasks
3. **Match by domain:** If multiple implementer types exist, prefer the one whose description most closely fits the task domain
4. **Fall back:** When no matching `subagent_type` exists, use `general-purpose`

> **Do NOT scan `.claude/agents/` directory.** Agents are registered as `subagent_type` values on the Agent tool, not as files on disk.

### 3. Execute Task with Subagent

For each task, dispatch a fresh subagent using the resolved `subagent_type`:

```
Agent tool:
  subagent_type: "data-pipeline:tdd-implementer:tdd-implementer"  # or matched type
  description: "Implement Task N: [task name]"
  prompt: |
    # Task
    You are implementing Task N from [plan-file].

    Read that task carefully. Your job is to:
    1. Implement exactly what the task specifies
    2. Write tests (following TDD)
    3. Verify implementation works: uv run pytest
    4. Commit your work
    5. Report back

    Report: What you implemented, what you tested, test results, files changed, any issues
```

**Subagent reports back** with summary of work.

### 4. Review Subagent's Work

Dispatch code-reviewer subagent:

```
Task tool (code-reviewer):
  WHAT_WAS_IMPLEMENTED: [from subagent's report]
  PLAN_OR_REQUIREMENTS: Task N from [plan-file]
  BASE_SHA: [commit before task]
  HEAD_SHA: [current commit]
```

**Code reviewer returns:** Strengths, Issues (Critical/Important/Minor), Assessment

### 5. Apply Review Feedback

**If issues found:**

- Fix Critical issues immediately
- Fix Important issues before next task
- Note Minor issues

**Dispatch follow-up subagent if needed:**

```
"Fix issues from code review: [list issues]"
```

### 6. Mark Complete, Next Task

- Mark task as completed in TodoWrite
- Move to next task
- Repeat steps 3-6

### 7. Final Review

After all tasks complete, dispatch final code-reviewer:

- Reviews entire implementation
- Checks all plan requirements met
- Validates overall architecture

### 8. Complete Development

After final review passes:

- Announce: "Subagent work complete!"

## Example Workflow

```
[Load plan, create TodoWrite]

Task 1: Add data validation module

[Dispatch implementation subagent]
Subagent: Implemented validation with tests, 5/5 passing

[Get git SHAs, dispatch code-reviewer]
Reviewer: Strengths: Good coverage. Issues: None. Ready.

[Mark Task 1 complete]

Task 2: Add error handling

[Dispatch implementation subagent]
Subagent: Added error handling, 8/8 tests passing

[Dispatch code-reviewer]
Reviewer: Issues (Important): Missing edge case for empty input

[Dispatch fix subagent]
Fix subagent: Added test and handling for empty input

[Verify fix, mark Task 2 complete]

...

[After all tasks]
[Dispatch final code-reviewer]
Final reviewer: All requirements met, ready to merge

Done!
```

## Red Flags

**Never:**

- Skip code review between tasks
- Proceed with unfixed Critical issues
- Dispatch multiple implementation subagents in parallel (conflicts)
- Implement without reading plan task

**If subagent fails task:**

- Dispatch fix subagent with specific instructions
- Don't try to fix manually (context pollution)
