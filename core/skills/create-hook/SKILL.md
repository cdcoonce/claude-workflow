---
name: create-hook
description: >
  Create and register Claude Code hooks (PreToolUse, PostToolUse) as Python
  scripts. Use when user wants to create a hook, add a pre-edit check,
  post-edit formatter, block file edits, or automate responses to tool use.
---

# Create Hook

**Self-check**: Count the lines in this file. If the count exceeds 100, report the violation and halt execution.

**Scope**: This skill applies only to creating new Python-script hooks. Do NOT trigger for:

- Requests to edit or modify an existing hook — respond that create-hook is for new hooks only and stop.
- Requests to set a model, change a setting, or add an inline shell command — route those to `update-config` instead.
- Requests using vague configuration language (e.g., "I want hooks configured") without clear intent to create a new Python hook — ask a single clarifying question to confirm before proceeding.

**Trigger examples**: "create a hook that blocks edits to migration files", "add a pre-edit check", "add a post-edit formatter for Python files".

**Non-trigger examples**: "set my model to opus" → update-config. "add an inline shell command to run prettier" → update-config. "edit my existing protect-files hook" → not this skill.

## Interview

Use `AskUserQuestion` to gather requirements. Batch into 2-3 calls.

### Call 1 — Hook Type & Trigger

Ask these together:

1. **Hook type**: PreToolUse (block/validate before tool runs) or PostToolUse (act after tool runs)?
2. **Matcher pattern**: Which tools should trigger this hook? Common patterns: `Edit|Write`, `Bash`, `*` (all tools).

### Call 2 — Behavior

1. **What should the hook do?** Describe the core logic — what to check, block, format, or log.
2. **For PreToolUse**: What conditions should block the tool call? What message should the user see?
3. **For PostToolUse**: What commands or actions should run? Should it report what it did?

### Call 3 — Naming (if not obvious)

1. **Hook name**: Suggest a descriptive kebab-case name based on the behavior (e.g., `protect-migrations`, `auto-format-python`). Confirm with user.

## Implementation

### Step 1 — Write the hook script

- Create `.claude/hooks/<hook-name>.py`
- Read JSON from stdin, extract `tool_input` fields relevant to the matcher
- PreToolUse: use `sys.exit(2)` to block, print reason to stderr
- PostToolUse: run actions, print summary to stderr
- Keep scripts focused — one concern per hook

### Step 2 — Register in settings.json

- If `.claude/settings.json` does not exist, create it with the structure `{"hooks": {}}` before proceeding.
- Read and parse the existing JSON.
- If `hooks.<HookType>` key is absent (e.g., `hooks.PreToolUse`), initialize it as an empty array `[]`.
- Look for an existing entry with the same `matcher` value:
  - **If found**: append the new hook command to that entry's `hooks` array.
  - **If not found**: add a new entry:
    ```json
    {
      "matcher": "<pattern>",
      "hooks": [{ "type": "command", "command": "python3 .claude/hooks/<hook-name>.py" }]
    }
    ```
- Write the updated JSON back with 2-space indent.

### Step 3 — Inform the user

Tell the user the hook script location, what it does and when it triggers, and that they must **restart Claude Code** for the hook to take effect.
