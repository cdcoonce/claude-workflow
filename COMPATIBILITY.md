# Platform Compatibility

This document lists the features each supported agent platform depends on.
Update when a breaking change is discovered. See [ROADMAP.md](ROADMAP.md) for
the overall multi-platform goal and design principle.

## Claude Code

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

**Last Verified:** 2026-03-21 — Claude Code with Opus 4.6

## Codex

### Plugin System

- `.codex-plugin/plugin.json` plugin manifest, extended shape:
  `author`, `repository`, `skills` path, and an `interface` block
  (`displayName`, `shortDescription`, `longDescription`, `developerName`,
  `category`, `capabilities`)
- Marketplace listing via `.agents/plugins/marketplace.json`
  (`scripts/build_marketplace.py`)

### Hooks

- Tool-ID matcher names differ from Claude Code's (`edit`, `write`,
  `multi_edit` vs. `Edit`, `Write`, `MultiEdit`) — current hook matchers cover
  both naming conventions in one pattern
- Payload shape and ordering semantics beyond matcher syntax: **not yet
  verified** (see ROADMAP.md open questions)

### Skills

- Not yet verified whether auto-discovery matches Claude Code's convention

**Last Verified:** 2026-07-02 — manifest shape and hook matcher names only
(commit `bde36ea`)

## Cortex Code (CoCo)

### Plugin System

- `.cortex-plugin/plugin.json` — **currently identical in shape to the Codex
  manifest** (same `interface` block, same fields). Verified as of the CoCo
  manifest commit; re-check when CoCo's own plugin spec is confirmed
  independently rather than assumed to track Codex.

### Hooks

- Shares the same widened tool-ID matcher pattern as Codex
  (`edit|write|multi_edit|Edit|Write|MultiEdit`)
- Payload shape and ordering semantics: **not yet verified**

### Skills

- Not yet verified whether auto-discovery matches Claude Code's convention

**Last Verified:** 2026-07-02 — manifest shape and hook matcher names only
(commit `4010d37`)
