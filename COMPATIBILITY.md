# Claude Code Compatibility

This document lists Claude Code features this template system depends on.
Update when a breaking change is discovered.

## Required Features

### Plugin System
- `.claude-plugin/plugin.json` plugin manifest
- Plugin-level `skills/`, `agents/`, `hooks/` directories
- `$CLAUDE_PLUGIN_ROOT` environment variable in hook commands

### Hooks
- `PreToolUse` hook type — used for file protection
- `PostToolUse` hook type — used for auto-linting
- `Edit|Write` matcher syntax
- `hooks/hooks.json` for plugin hook configuration
- Hook scripts receive tool input as JSON on stdin

### Skills
- `skills/*/SKILL.md` auto-discovery within plugin
- Skill `name` and `description` frontmatter for triggering
- `references/` subdirectory loading

### Agent Features
- `Agent` tool with `subagent_type` parameter
- `TodoWrite` tool for task tracking
- `EnterPlanMode` / `ExitPlanMode` tools

### Settings
- `settings.json` at plugin root (non-hook settings)
- Hook arrays in hooks.json with `matcher` and `hooks` fields

## Last Verified

2026-03-21 — Claude Code with Opus 4.6
