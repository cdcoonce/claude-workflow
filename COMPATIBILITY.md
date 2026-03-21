# Claude Code Compatibility

This document lists Claude Code features this template system depends on.
Update when a breaking change is discovered.

## Required Features

### Hooks
- `PreToolUse` hook type — used for file protection
- `PostToolUse` hook type — used for auto-linting
- `Edit|Write` matcher syntax
- `$CLAUDE_PROJECT_DIR` environment variable in hook commands
- Hook scripts receive tool input as JSON on stdin

### Skills
- `.claude/skills/*/SKILL.md` auto-discovery
- Skill `name` and `description` frontmatter for triggering
- `references/` subdirectory loading

### Agent Features
- `Agent` tool with `subagent_type` parameter
- `TodoWrite` tool for task tracking
- `EnterPlanMode` / `ExitPlanMode` tools

### Settings
- `.claude/settings.json` project-level settings
- Hook arrays in settings with `matcher` and `hooks` fields

## Last Verified

2026-03-21 — Claude Code with Opus 4.6
