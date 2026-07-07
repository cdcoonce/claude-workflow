# Plan: Remove .claude/ content that overlaps with claude-tooling plugin

> Source PRD: https://github.com/cdcoonce/claude-workflow/issues/47

## Architectural decisions

Durable decisions that apply across all phases:

- **Source of truth**: The `claude-tooling@claude-workflow` plugin provides all universal workflow tools (skills, agents, hooks, methodology docs)
- **Repo-specific retention**: `.claude/` keeps only content the plugin does not provide: `security-review` skill, `docs/project.md`, `settings.local.json`
- **CLAUDE.md scope**: Project-specific context only — architecture, commands, code style, planning, skill/agent documentation for the template system
- **settings.json**: Retains only `enabledPlugins` block after hook config removal

---

## Phase 1: Remove duplicate skills

**User stories**: 1 (single source of truth), 7 (fewer files to maintain)

### What to build

Delete 17 skill directories from `.claude/skills/` that the plugin already provides. Keep only `security-review` (not in plugin). After removal, verify the plugin still provides all removed skills in the active session.

Skills to remove: `commit`, `daa-code-review`, `design-an-interface`, `dev-cycle`, `github-cli`, `grill-me`, `improve-codebase-architecture`, `plan-ceo-review`, `prd-to-issues`, `prd-to-plan`, `project-context`, `readme-generator`, `request-refactor-plan`, `tdd`, `triage-issue`, `write-a-prd`, `write-a-skill`

### Acceptance criteria

- [ ] `.claude/skills/` contains only `security-review`
- [ ] Plugin skills still appear in the session (spot-check 2-3 skill names)
- [ ] `uv run pytest` green

---

## Phase 2: Remove duplicate agents, hooks, docs, metadata, and hook config

**User stories**: 1 (single source of truth), 2 (hooks execute once), 7 (fewer files)

### What to build

Delete the entire `.claude/agents/` directory (4 agents duplicated by plugin). Delete `.claude/hooks/` directory (2 hook scripts duplicated by plugin). Strip `PreToolUse` and `PostToolUse` hook entries from `.claude/settings.json` (keep only `enabledPlugins`) — this must happen in the same phase as hook script deletion to avoid broken references. Delete 4 methodology docs from `.claude/docs/` (`tdd.md`, `root-cause-tracing.md`, `subagent-development.md`, `parallel-agents.md`) — keep `project.md`. Delete `.claude/.template-version`. Remove `.claude/worktrees/` if empty.

**CEO Review finding:** Hook scripts and hook config must be removed together to prevent settings.json from referencing nonexistent scripts between phases.

### Acceptance criteria

- [ ] `.claude/agents/` directory does not exist
- [ ] `.claude/hooks/` directory does not exist
- [ ] `.claude/settings.json` contains only `enabledPlugins` (no hook config)
- [ ] `.claude/docs/` contains only `project.md`
- [ ] `.claude/.template-version` does not exist
- [ ] `.claude/worktrees/` removed if empty
- [ ] Plugin agents and hooks still function (plugin is source of truth)
- [ ] `uv run pytest` green

---

## Phase 3: Clean up CLAUDE.md

**User stories**: 3 (CLAUDE.md focuses on project context)

### What to build

Remove the Methodology section from `CLAUDE.md` (TDD, Root Cause Tracing, Subagent-Driven Development, Parallel Agent Dispatch subsections). All other CLAUDE.md sections remain unchanged.

### Acceptance criteria

- [ ] `CLAUDE.md` has no Methodology section
- [ ] `CLAUDE.md` retains: What This Repo Is, Architecture, Commands, Code Style, Planning, Skills, Agents
- [ ] Plugin hooks still fire on edit/write events
- [ ] `uv run pytest` green
