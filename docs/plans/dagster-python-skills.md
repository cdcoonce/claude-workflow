# Plan: Add dignified-python and dagster-expert Skills

> Source PRD: GitLab issue #7 — feat: add dignified-python (core) and dagster-expert (data-pipeline) skills
> Design spec: `docs/superpowers/specs/2026-03-23-dagster-python-skills-design.md`

## Architectural decisions

Durable decisions that apply across all phases:

- **dignified-python location**: `core/skills/dignified-python/` — universal, included in all presets via `core.skills: "all"`
- **dagster-expert location**: `presets/data-pipeline/skills/dagster-expert/` — preset-specific, included only in data-pipeline builds
- **Source**: Full port from `https://github.com/dagster-io/skills/tree/master` — all reference files copied verbatim, only SKILL.md frontmatter and cross-references adapted
- **Agent wiring**: Skills added via `skills.add` in individual AGENT.md files, not via `agent-role-defaults.json`
- **Build system**: No code changes — existing `build_preset.py` handles `preset_skills` and `core.skills: "all"` correctly
- **Ordering constraint**: Skill directories must exist before manifest references them (`_validate_manifest` checks directory existence)

---

## Phase 1: dignified-python Core Skill

**User stories**: Python coding standards across all presets, agent-level enforcement for implementers and reviewers

### What to build

Port the `dignified-python` skill from the dagster-io/skills repo into `core/skills/dignified-python/`. This includes the main SKILL.md (adapted frontmatter, `@` includes converted to relative markdown links, upstream-internal skill references replaced), the core standards file, CLI patterns, subprocess patterns, 4 Python version files, and 6 advanced reference files. Wire it into both core agents by editing their AGENT.md frontmatter. Add a `/dignified-python` trigger entry to `core/CLAUDE-base.md`. Verify end-to-end by building any preset and confirming the skill appears in dist output.

### Acceptance criteria

- [ ] `core/skills/dignified-python/SKILL.md` exists with adapted frontmatter (name/description, no plugin.json)
- [ ] `dignified-python-core.md`, `cli-patterns.md`, `subprocess.md` sit alongside SKILL.md
- [ ] `versions/` directory contains python-3.10.md through python-3.13.md
- [ ] `references/advanced/` contains api-design.md, exception-handling.md, interfaces.md, typing-advanced.md
- [ ] `references/checklists.md` and `references/module-design.md` exist
- [ ] SKILL.md has no `@` include syntax — uses relative markdown links
- [ ] SKILL.md has no references to `/dagster-best-practices` or `/dg` — replaced with `/dagster-expert`
- [ ] `core/agents/tdd-implementer/AGENT.md` frontmatter: `skills.add` includes `dignified-python`
- [ ] `core/agents/code-reviewer/AGENT.md` frontmatter: `skills.add` includes `dignified-python`
- [ ] `core/CLAUDE-base.md` has `/dignified-python` skill index entry before `## Project Context`
- [ ] `uv run python -m scripts.build_preset data-pipeline` succeeds
- [ ] `dist/data-pipeline/.claude/skills/dignified-python/SKILL.md` exists in build output

---

## Phase 2: dagster-expert Preset Skill

**User stories**: Dagster-first data pipelines, reference-backed CLI guidance, preset agent Dagster rewrites

### What to build

Port the `dagster-expert` skill from the dagster-io/skills repo into `presets/data-pipeline/skills/dagster-expert/`. This is a large skill (~100 reference files) covering assets, automation, CLI commands, components, and 40+ integration directories. Copy all reference files verbatim, adapt only the SKILL.md frontmatter. Update the data-pipeline manifest to register the preset skill. Rewrite the `pipeline-builder` agent to be Dagster-first (remove Airflow/Prefect, expand Dagster section). Add a Dagster-specific review section to `data-quality-reviewer`. Both preset agents get `dagster-expert` and `dignified-python` in their skill lists. Update `CLAUDE-preset.md` with an orchestration section and `/dagster-expert` skill entry.

### Acceptance criteria

- [ ] `presets/data-pipeline/skills/dagster-expert/SKILL.md` exists with adapted frontmatter
- [ ] `references/` tree contains all upstream files: assets.md, env-vars.md, automation/*, cli/*, components/*, integrations/*
- [ ] All internal links in SKILL.md reference index resolve to existing files
- [ ] `presets/data-pipeline/manifest.json` has `"preset_skills": ["dagster-expert"]`
- [ ] `pipeline-builder/AGENT.md` frontmatter: `skills.add` includes `dagster-expert` and `dignified-python`
- [ ] `pipeline-builder/AGENT.md` body: Airflow/Prefect sections removed, Dagster-first orchestration section (8-10 bullets)
- [ ] `data-quality-reviewer/AGENT.md` frontmatter: `skills.add` includes `dagster-expert` and `dignified-python`
- [ ] `data-quality-reviewer/AGENT.md` body: new Dagster-specific review section (8 bullets)
- [ ] `presets/data-pipeline/CLAUDE-preset.md` has `## Orchestration` section with Dagster as default
- [ ] `presets/data-pipeline/CLAUDE-preset.md` has `/dagster-expert` skill index entry
- [ ] `uv run python -m scripts.build_preset data-pipeline` succeeds
- [ ] `dist/data-pipeline/.claude/skills/dagster-expert/SKILL.md` exists in build output

---

## Phase 3: Cross-Preset Verification

**User stories**: Both skills work correctly, no regressions across all 5 presets

### What to build

Run the full test suite and build all 5 presets to verify no regressions. Confirm dignified-python appears in all preset builds (it's a core skill). Confirm dagster-expert appears only in data-pipeline builds. Validate smoke tests pass with zero link resolution errors.

### Acceptance criteria

- [ ] `uv run pytest` passes (all existing tests)
- [ ] `uv run python -m scripts.smoke_test data-pipeline` passes
- [ ] `uv run python -m scripts.build_preset python-api` succeeds — dignified-python present, dagster-expert absent
- [ ] `uv run python -m scripts.build_preset full-stack` succeeds — dignified-python present, dagster-expert absent
- [ ] `uv run python -m scripts.build_preset analysis` succeeds — dignified-python present, dagster-expert absent
- [ ] `uv run python -m scripts.build_preset claude-tooling` succeeds — dignified-python present, dagster-expert absent
- [ ] Build output agent files have correct skill lists in frontmatter
