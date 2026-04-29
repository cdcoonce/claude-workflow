# Plan: Agent System for Template Presets

> Source PRD: https://github.com/cdcoonce/claude-workflow/issues/34
> Design Spec: `docs/superpowers/specs/2026-03-22-agent-system-design.md`

## Architectural decisions

Durable decisions that apply across all phases:

- **Agent file format**: `AGENT.md` with YAML frontmatter (`name`, `description`, `role`, `skills.add`, `skills.remove`) inside a named directory
- **Directory structure**: `core/agents/<name>/AGENT.md` for universal agents, `presets/<preset>/agents/<name>/AGENT.md` for preset-specific
- **Build output**: `.claude/agents/<name>/AGENT.md` alongside existing `.claude/skills/`, `.claude/docs/`, `.claude/hooks/`
- **Role defaults**: `core/agent-role-defaults.json` → `.claude/agent-role-defaults.json`. Implementers get `[tdd, commit]`, reviewers get `[daa-code-review]`
- **Manifest fields**: `core.agents` (default `"all"`), `preset_agents` (default `[]`). Exclusion path format: `agents/<name>`
- **Override semantics**: Preset agent with same name as core agent replaces it (same as skills)
- **Roles**: `implementer` or `reviewer` — determines default skill set

---

## Phase 1: Core Agent Infrastructure

**User stories**: Build pipeline can assemble and validate agents from core

### What to build

End-to-end build pipeline support for core agents. Create `core/agents/` with two placeholder agents (minimal `AGENT.md` with valid frontmatter), `core/agent-role-defaults.json`, and extend `build_preset.py` to copy core agents and role defaults into dist output. Extend `_validate_manifest` for agent references. Update `conftest.py` test fixture to include core agents in the temporary repo structure. Write build tests verifying core agents are copied, role defaults are copied, exclusions work for agents, and selective agent lists work.

**CEO Review additions:**

- Gracefully skip core agent copy when `core/agents/` directory doesn't exist (backward compatibility with repos that haven't added agents yet)
- Gracefully skip `agent-role-defaults.json` copy when file doesn't exist
- Add path containment check to exclusion step: verify resolved path is within `claude_dir` before deleting (pre-existing gap, fix while we're here)
- Preset agent override should print WARNING, consistent with existing skill override behavior

### Acceptance criteria

- [ ] `core/agents/tdd-implementer/AGENT.md` and `core/agents/code-reviewer/AGENT.md` exist with valid frontmatter (placeholder body content is fine)
- [ ] `core/agent-role-defaults.json` exists with implementer and reviewer defaults
- [ ] `build_preset.py` copies core agents to `dist/<preset>/.claude/agents/` when manifest has `core.agents: "all"` or lists specific names
- [ ] `build_preset.py` copies `agent-role-defaults.json` to `dist/<preset>/.claude/`
- [ ] `build_preset.py` defaults to `"all"` when `core.agents` is omitted from manifest
- [ ] `build_preset.py` gracefully skips core agent copy when `core/agents/` doesn't exist
- [ ] `build_preset.py` gracefully skips `agent-role-defaults.json` copy when file doesn't exist
- [ ] Exclusion path containment check: resolved path must be within `claude_dir`
- [ ] Exclusions with `agents/<name>` path format remove agents from output
- [ ] `conftest.py` `tmp_repo` fixture includes core agents and role defaults
- [ ] All new build tests pass; all existing tests still pass
- [ ] `uv run pytest` green

---

## Phase 2: Preset Agent Support

**User stories**: Preset-specific agents are assembled into build output alongside core agents

### What to build

Extend `build_preset.py` to handle `preset_agents` manifest field — copy preset agents from `presets/<name>/agents/` to dist output, with override-on-collision logic (preset agent replaces core agent of same name). Add manifest validation that `preset_agents` references exist. Update `conftest.py` fixture to include a preset agent. Write build tests for preset agent copying, override behavior, and validation failure on missing references.

### Acceptance criteria

- [ ] `build_preset.py` copies preset agents listed in `preset_agents` to dist output
- [ ] Preset agent with same name as core agent deletes core and copies preset version
- [ ] Manifest validation fails fast if `preset_agents` references nonexistent agent directory
- [ ] `preset_agents` defaults to `[]` when omitted from manifest
- [ ] Validation catches agents listed in both `preset_agents` and `exclude`
- [ ] `conftest.py` fixture includes a sample preset agent
- [ ] Build tests cover: preset agent copied, override on collision, validation failure
- [ ] All existing tests still pass
- [ ] `uv run pytest` green

---

## Phase 3: Core Agent Content

**User stories**: Universal agents carry meaningful domain expertise

### What to build

Replace placeholder content in `core/agents/tdd-implementer/AGENT.md` and `core/agents/code-reviewer/AGENT.md` with full system prompts. The TDD implementer agent should carry conventions for test-first development, file organization, and commit practices. The code reviewer agent should carry a review checklist covering structure, naming, SOLID principles, test coverage, and common issues.

### Acceptance criteria

- [ ] `tdd-implementer/AGENT.md` has a complete system prompt covering TDD workflow, test organization, implementation approach, and commit conventions
- [ ] `code-reviewer/AGENT.md` has a complete system prompt covering review checklist, severity classification, and feedback format
- [ ] Both agents have accurate `description` fields suitable for convention-based matching
- [ ] Frontmatter is valid (name, description, role, skills fields present)
- [ ] `uv run pytest` green (no regressions)

---

## Phase 4: Preset Agent Content

**User stories**: Each preset ships domain-specific agents for its project type

### What to build

Create `AGENT.md` files for all 5 presets with full system prompts. Update each preset's `manifest.json` to include the `preset_agents` field. Create the agent directories under each preset.

Preset agents:

- **python-api**: `api-builder` (implementer), `security-reviewer` (reviewer)
- **full-stack**: `frontend-builder` (implementer), `backend-builder` (implementer), `ux-reviewer` (reviewer)
- **data-pipeline**: `pipeline-builder` (implementer), `data-quality-reviewer` (reviewer)
- **analysis**: `analysis-builder` (implementer)
- **claude-tooling**: `skill-builder` (implementer), `skill-reviewer` (reviewer)

### Acceptance criteria

- [ ] All 11 preset agent `AGENT.md` files exist with full system prompts
- [ ] Each agent has accurate `description` for convention-based matching
- [ ] Each agent has correct `role` and appropriate `skills.add`/`skills.remove`
- [ ] All 5 `manifest.json` files updated with `preset_agents` field
- [ ] `uv run python -m scripts.build_preset <preset>` succeeds for all 5 presets
- [ ] `uv run pytest` green

---

## Phase 5: Smoke Test Extensions

**User stories**: Smoke tests validate agent integrity post-build

### What to build

Extend `smoke_test.py` to validate agents in built output:

- Every `AGENT.md` has required frontmatter fields (`name`, `description`, `role`)
- `role` is either `implementer` or `reviewer`
- Agent frontmatter `name` matches its directory name
- Skills in `skills.add` exist in the built `.claude/skills/` directory

### Acceptance criteria

- [ ] Smoke test checks all `AGENT.md` files in `.claude/agents/` for required frontmatter
- [ ] Smoke test validates `role` is `implementer` or `reviewer`
- [ ] Smoke test validates `name` matches directory name
- [ ] Smoke test validates `skills.add` references resolve to existing skills
- [ ] `uv run python -m scripts.smoke_test <preset>` passes for all 5 presets
- [ ] Smoke test correctly fails when given malformed agent frontmatter (test this)
- [ ] `uv run pytest` green

---

## Phase 6: Orchestrator Doc Updates

**User stories**: Orchestrating docs describe agent-aware dispatch

### What to build

Update three methodology/skill docs to include agent discovery, matching, and dispatch:

- **`core/docs/subagent-development.md`**: Add agent discovery step between "Load Plan" and "Execute Task." Describe scan/filter/match/fallback pattern. Update dispatch prompt template to include agent identity and resolved skills.
- **`core/docs/parallel-agents.md`**: Add agent discovery step. Note that each parallel dispatch can use a different agent based on domain.
- **`core/skills/dev-cycle/SKILL.md`**: Update Phase 5 to describe agent-aware dispatch — scan agents before dispatching per-issue subagents, use matched implementer for implementation, use matched reviewer between dispatches.

### Acceptance criteria

- [ ] `subagent-development.md` includes agent discovery step with scan/filter/match/fallback
- [ ] `subagent-development.md` dispatch prompt template includes agent identity injection
- [ ] `parallel-agents.md` includes agent discovery step
- [ ] `dev-cycle/SKILL.md` Phase 5 describes agent-aware dispatch
- [ ] All three docs preserve backward compatibility (generic fallback when no agents exist)
- [ ] `uv run python -m scripts.smoke_test <preset>` still passes (no broken links)
- [ ] `uv run pytest` green
