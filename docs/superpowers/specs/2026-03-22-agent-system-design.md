# Agent System for Claude Workflow Templates

**Date:** 2026-03-22
**Status:** Approved

## Overview

Add specialized agents as a first-class build artifact to the template system. Agents are domain-expert roles (`.claude/agents/*.md`) that orchestrate skills and get dispatched programmatically — implementer agents write code, reviewer agents check it. Projects built from presets ship with pre-configured agents ready for use by dev-cycle, subagent-development, and parallel-agents workflows.

## Key Decisions

| Decision            | Choice                                        | Rationale                                                                                              |
| ------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Agent purpose       | Both implementers and reviewers               | Maps to dev-cycle's distinct implementation and review phases                                          |
| Selection mechanism | Convention-based matching via descriptions    | Mirrors skill trigger pattern; orchestrators scan agents and match by relevance                        |
| Composability       | Flat dispatch only                            | Orchestrator dispatches agents; agents do not dispatch other agents. Predictable, avoids nested chains |
| Skill access        | Role-based defaults with per-agent add/remove | Reduces boilerplate; most implementers need tdd+commit, most reviewers need daa-code-review            |
| Architecture        | First-class build artifact (Approach C)       | Own directory, manifest field, and build step — distinct from skills                                   |
| Core agents         | 2 generics: tdd-implementer, code-reviewer    | Cover today's behavior as named entities; fallback when no specialist matches                          |
| Preset agents       | 2-3 per preset                                | Lean starting set; preset authors can add more later                                                   |

## Directory Structure

### Source layout

```text
core/
├── agents/
│   ├── code-reviewer/
│   │   └── AGENT.md
│   ├── tdd-implementer/
│   │   └── AGENT.md
│   └── ...
├── agent-role-defaults.json
├── skills/          (unchanged)
├── docs/            (unchanged)
└── hooks/           (unchanged)

presets/<preset-name>/
├── agents/
│   ├── <agent-name>/
│   │   └── AGENT.md
│   └── ...
├── skills/          (unchanged)
└── ...
```

### Build output

```text
dist/<preset>/.claude/
├── agents/
│   ├── <core-agents>/
│   │   └── AGENT.md
│   ├── <preset-agents>/
│   │   └── AGENT.md
│   └── ...
├── agent-role-defaults.json
├── skills/               (unchanged)
├── docs/                 (unchanged)
└── hooks/                (unchanged)
```

## Agent File Format

Each agent is an `AGENT.md` file with YAML frontmatter inside a named directory:

```markdown
---
name: api-builder
description: >
  Build REST API endpoints following project conventions.
  Use when implementing issues involving route handlers,
  request validation, or response formatting.
role: implementer
skills:
  add: []
  remove: []
---

# API Builder Agent

[System prompt / domain expertise / conventions]
```

### Required fields

- **`name`** — Unique identifier, matches directory name
- **`description`** — Trigger description used for convention-based matching. Orchestrators compare task content against this to select the right agent
- **`role`** — Either `implementer` or `reviewer`. Determines default skill set

### Optional fields

- **`skills.add`** — Skills to add on top of role defaults (e.g., `[deploy]`)
- **`skills.remove`** — Skills to remove from role defaults

### Conventions

- Each agent gets its own directory, allowing future expansion with `references/` or `scripts/` subdirectories
- Preset agents override core agents on name collision (same as skills)
- `AGENT.md` filename parallels `SKILL.md`

## Role Defaults

Defined in `core/agent-role-defaults.json`:

```json
{
  "implementer": {
    "skills": ["tdd", "commit"]
  },
  "reviewer": {
    "skills": ["daa-code-review"]
  }
}
```

Copied to `dist/<preset>/.claude/agent-role-defaults.json`. Orchestrators read this to resolve an agent's effective skill set:

```text
effective_skills = role_defaults[agent.role].skills + agent.skills.add - agent.skills.remove
```

### Role defaults are universal

Role defaults are **not customizable per preset**. The per-agent `skills.add` / `skills.remove` fields are the escape hatch for preset-specific needs. This keeps the system simple — one file to understand, not a merge chain.

### Skill reference validation

Role defaults and agent `skills.add` fields are **advisory at build time** — the build pipeline does not validate that referenced skills exist in the output. The **smoke tests** catch unresolved skill references post-build, consistent with how other cross-references are validated today.

## Manifest Schema

The manifest gains an `agents` field:

```json
{
  "name": "python-api",
  "description": "Python API projects",
  "core": {
    "skills": "all",
    "docs": "all",
    "hooks": ["protect-files.py"],
    "agents": "all"
  },
  "preset_skills": ["deploy"],
  "preset_hooks": ["post-edit-lint.py"],
  "preset_agents": ["api-builder", "security-reviewer"],
  "exclude": []
}
```

- `"agents": "all"` copies all core agents
- A list like `["code-reviewer", "tdd-implementer"]` copies only those
- **If `core.agents` is omitted**, it defaults to `"all"` — matching the behavior of `core.skills` and `core.docs`. Existing manifests will ship all core agents without modification
- `preset_agents` lists preset-specific agents to include. Defaults to `[]` if omitted
- `exclude` can remove agents from output using the path format `agents/<agent-name>` (e.g., `"exclude": ["agents/code-reviewer"]`), consistent with the existing `skills/<skill-name>` convention

## Build Pipeline Changes

Three new steps added to `build_preset.py`:

1. **Copy core agents** (after core hooks step) — Copy agents listed in manifest from `core/agents/` to `dist/<preset>/.claude/agents/`
2. **Copy preset agents** (after preset hooks step) — Copy preset agents. Override core agent on name collision (delete core, copy preset)
3. **Copy role defaults** — Copy `core/agent-role-defaults.json` to `dist/<preset>/.claude/`

Exclusions (existing step) extended to also cover agents.

### Manifest validation

Fail fast if:

- `preset_agents` references an agent that doesn't exist in `presets/<name>/agents/`
- `core.agents` lists a name that doesn't exist in `core/agents/`

## Orchestrator Integration

### Agent discovery and matching

When an orchestrator dispatches a subagent:

1. **Check available `subagent_type` values** — the Agent tool's system prompt lists all registered agent types (e.g., `data-pipeline:tdd-implementer:tdd-implementer`, `data-pipeline:code-reviewer:code-reviewer`). These are built from `AGENT.md` files during `build_preset` and registered as plugin agent types
2. **Filter by role** — `tdd-implementer` types for implementation tasks, `code-reviewer` types for review tasks
3. **Match by description** — the orchestrator reads all filtered agent type descriptions and uses its judgment to select the best fit based on relevance to the task/issue content. If two types seem equally relevant, prefer the more specialized one
4. **Fallback** — if no agent type matches well (or no specialized types are available), use `general-purpose` as the subagent type. The system never forces a bad match

> **Important:** Do NOT scan `.claude/agents/` directory. Agent definitions are compiled into `subagent_type` values on the Agent tool at build time, not read from disk at runtime.

### Dispatch prompt construction

When using a registered `subagent_type`, the agent's system prompt and skills are injected automatically by the Agent tool — the orchestrator only needs to provide the task description in the `prompt` parameter:

```
Agent tool:
  subagent_type: "data-pipeline:tdd-implementer:tdd-implementer"
  description: "Implement Issue #N: title"
  prompt: |
    Task: {task description from plan/issue}
```

The agent's identity, system prompt, and skill list are resolved by the framework from the `subagent_type` — do not manually inject them.

### Changes per orchestrator

| Orchestrator             | Change                                                                                                                          |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| **dev-cycle** (Phase 5)  | Match `subagent_type` before dispatching per-issue subagents. Use matched implementer type. Use matched reviewer type between dispatches |
| **subagent-development** | Add `subagent_type` resolution step between "Load Plan" and "Execute Task"                                                      |
| **parallel-agents**      | Resolve `subagent_type` for each parallel task. Each dispatch can use a different agent type based on domain                    |

### What does NOT change

- User invokes `/dev-cycle` the same way
- Skills are invoked the same way
- Flat dispatch model stays
- Generic fallback means projects with zero agents work identically to today

## Core Agents

| Agent             | Role        | Description                                                                                                                              |
| ----------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `tdd-implementer` | implementer | General-purpose implementation following TDD. Fallback for any issue that doesn't match a specialized implementer                        |
| `code-reviewer`   | reviewer    | General code quality review — structure, naming, SOLID, test coverage. Fallback for any review that doesn't match a specialized reviewer |

## Preset Agents

### python-api

| Agent               | Role        | Description                                                                                      |
| ------------------- | ----------- | ------------------------------------------------------------------------------------------------ |
| `api-builder`       | implementer | REST endpoint implementation — route handlers, Pydantic models, error envelopes, auth middleware |
| `security-reviewer` | reviewer    | Auth patterns, input validation, dependency vulnerabilities, OWASP top 10                        |

### full-stack

| Agent              | Role        | Description                                                                  |
| ------------------ | ----------- | ---------------------------------------------------------------------------- |
| `frontend-builder` | implementer | React/Next.js components, state management, accessibility, responsive layout |
| `backend-builder`  | implementer | API contracts, data validation, database queries                             |
| `ux-reviewer`      | reviewer    | Accessibility, component structure, user flow consistency                    |

### data-pipeline

| Agent                   | Role        | Description                                                          |
| ----------------------- | ----------- | -------------------------------------------------------------------- |
| `pipeline-builder`      | implementer | ETL stages, schema evolution, idempotent transforms, backfill safety |
| `data-quality-reviewer` | reviewer    | Schema validation, null handling, type coercion, deduplication       |

### analysis

| Agent              | Role        | Description                                                             |
| ------------------ | ----------- | ----------------------------------------------------------------------- |
| `analysis-builder` | implementer | Notebook structure, statistical methods, visualization, reproducibility |

### claude-tooling

| Agent            | Role        | Description                                                                   |
| ---------------- | ----------- | ----------------------------------------------------------------------------- |
| `skill-builder`  | implementer | Skill file structure, trigger descriptions, SKILL.md conventions              |
| `skill-reviewer` | reviewer    | Skill quality — trigger accuracy, instruction clarity, reference completeness |

## Testing Strategy

### Build pipeline tests (extending test_build.py)

- Core agents copied when manifest says `"agents": "all"`
- Preset agents added to output
- Preset agent overrides core on name collision
- Agent exclusions work
- Selective core agents (list instead of "all")
- Role defaults file copied
- Manifest validation fails on nonexistent agent references

### Smoke tests (extending smoke_test.py)

- All agents in `preset_agents` have directories in `presets/<name>/agents/`
- Every `AGENT.md` has required frontmatter: `name`, `description`, `role`
- `role` is either `implementer` or `reviewer`
- Skills in `add` exist in the project's skill set
- Agent frontmatter `name` matches its directory name

### No runtime/integration tests

Agent dispatch is Claude's reasoning layer — not unit-testable. Validated by clear agent descriptions and matching logic in methodology docs. Build tests ensure correct file placement.
