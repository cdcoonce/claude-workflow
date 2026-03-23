# Add dignified-python (Core) and dagster-expert (Data-Pipeline Preset) Skills

**Date:** 2026-03-23
**Source:** https://github.com/dagster-io/skills/tree/master

## Summary

Port two skills from the dagster-io/skills repository into this template system:

1. **dignified-python** — Production Python coding standards (core skill, all presets)
2. **dagster-expert** — Comprehensive Dagster development guidance (data-pipeline preset skill)

Both are full ports (Approach A) — all reference files copied verbatim, with only structural adaptations to match this repo's conventions.

## Motivation

- **dignified-python** enforces modern Python patterns (LBYL, pathlib, type syntax, API design) across all generated project templates. Wired into both core agents so implementers and reviewers follow the same standards.
- **dagster-expert** provides reference-backed Dagster guidance (CLI commands, asset patterns, automation, 40+ integrations) that prevents Claude from hallucinating APIs. The data-pipeline preset leans into Dagster as the default orchestrator.

## File Structure

### dignified-python (Core Skill)

```
core/skills/dignified-python/
├── SKILL.md                          # Main skill definition
├── dignified-python-core.md          # Core standards (always loaded)
├── cli-patterns.md                   # Click/argparse patterns
├── subprocess.md                     # Subprocess patterns
├── versions/
│   ├── python-3.10.md
│   ├── python-3.11.md
│   ├── python-3.12.md
│   └── python-3.13.md
└── references/
    ├── advanced/
    │   ├── api-design.md
    │   ├── exception-handling.md
    │   ├── interfaces.md
    │   └── typing-advanced.md
    ├── checklists.md
    └── module-design.md
```

**Source mapping:** Files come from `skills/dignified-python/skills/dignified-python/` in the upstream repo. The `references/` subdirectory in upstream maps directly to `references/` here. Top-level files (`cli-patterns.md`, `subprocess.md`, `dignified-python-core.md`) sit alongside `SKILL.md`.

### dagster-expert (Data-Pipeline Preset Skill)

```
presets/data-pipeline/skills/dagster-expert/
├── SKILL.md                          # Main skill definition with reference index
└── references/
    ├── assets.md                     # Asset patterns, dependencies, metadata
    ├── env-vars.md                   # Environment variable configuration
    ├── automation/
    │   ├── choosing-automation.md
    │   ├── schedules.md
    │   ├── declarative-automation/
    │   │   ├── INDEX.md
    │   │   ├── advanced.md
    │   │   ├── core-concepts.md
    │   │   ├── customization.md
    │   │   ├── operands.md
    │   │   └── operators.md
    │   └── sensors/
    │       ├── asset-sensors.md
    │       ├── basic-sensors.md
    │       └── run-status-sensors.md
    ├── cli/
    │   ├── asset-selection.md
    │   ├── check.md
    │   ├── create-dagster.md
    │   ├── dev.md
    │   ├── launch.md
    │   ├── list-components.md
    │   ├── list-defs.md
    │   ├── api/                      # Dagster Plus API (agent, asset, run, etc.)
    │   │   ├── INDEX.md
    │   │   ├── general.md
    │   │   ├── agent/
    │   │   ├── alert-policy/
    │   │   ├── artifact/
    │   │   ├── asset/
    │   │   ├── code-location/
    │   │   ├── deployment/
    │   │   ├── organization/
    │   │   ├── run/
    │   │   ├── schedule/
    │   │   ├── secret/
    │   │   └── sensor/
    │   ├── list/                     # dg list subcommands
    │   │   ├── INDEX.md
    │   │   ├── component-tree.md
    │   │   ├── envs.md
    │   │   └── projects.md
    │   ├── plus/                     # Dagster Plus CLI
    │   │   ├── INDEX.md
    │   │   ├── login.md
    │   │   ├── config/
    │   │   ├── create/
    │   │   ├── deploy/
    │   │   ├── integrations/
    │   │   └── pull/
    │   ├── scaffold/
    │   │   ├── component.md
    │   │   └── defs.md
    │   └── utils/
    │       ├── INDEX.md
    │       ├── inspect-component.md
    │       ├── integrations.md
    │       └── refresh-defs-state.md
    ├── components/
    │   ├── creating-components.md
    │   ├── designing-component-integrations.md
    │   ├── resolved-framework.md
    │   ├── subclassing-components.md
    │   ├── template-variables.md
    │   └── state-backed/
    │       ├── creating.md
    │       └── using.md
    └── integrations/
        ├── INDEX.md                  # Master index of 40+ integrations
        ├── dagster-airbyte/
        ├── dagster-airlift/
        ├── dagster-aws/
        ├── dagster-azure/
        ├── dagster-dbt/              # Has 6 sub-files (checks, components, cloud, etc.)
        ├── dagster-duckdb/
        ├── dagster-gcp/
        ├── dagster-postgres/
        ├── dagster-snowflake/
        ├── dagster-slack/
        ├── dagster-sling/
        └── ... (40+ total integration directories, each with INDEX.md)
```

## Agent Wiring

### Core Agents (all presets get these changes)

**tdd-implementer** — add `dignified-python`:
```yaml
skills:
  add: [tdd, commit, dignified-python]
```

**code-reviewer** — add `dignified-python`:
```yaml
skills:
  add: [daa-code-review, dignified-python]
```

### Data-Pipeline Preset Agents

**pipeline-builder** — add both skills, rewrite to be Dagster-first:
```yaml
skills:
  add: [tdd, commit, dagster-expert, dignified-python]
```

Changes to agent body:
- Remove Airflow and Prefect orchestration sections
- Replace with Dagster asset-centric patterns
- Add: "Use the `dagster-expert` skill for CLI commands, asset patterns, and integration references"
- Keep general ETL/ELT patterns (idempotency, validation, backfill) — these are orchestrator-agnostic

**data-quality-reviewer** — add both skills, add Dagster awareness:
```yaml
skills:
  add: [daa-code-review, dagster-expert, dignified-python]
```

Changes to agent body:
- Add Dagster-specific review section: asset metadata validation, partition correctness, IO manager usage, resource configuration
- Keep all existing general data quality checks

## Manifest Change

**presets/data-pipeline/manifest.json** — register the preset skill:
```json
{
  "preset_skills": ["dagster-expert"]
}
```

No change needed for `dignified-python` — `core.skills: "all"` picks it up automatically.

## CLAUDE-preset.md Update

Add Dagster as default orchestrator to `presets/data-pipeline/CLAUDE-preset.md`:

```markdown
## Orchestration

- Default orchestrator: Dagster
- Use `uv run dg` CLI for project interaction (scaffold, launch, list, check)
- Define assets for each meaningful data artifact
- Use the `dagster-expert` skill for CLI commands, patterns, and integration references
```

Keep existing conventions (lowercase SQL, idempotent stages, row count logging).

## Adaptations from Upstream

### What stays verbatim
- All reference files (dagster-expert and dignified-python)
- `dignified-python-core.md`, version files, advanced references
- The reference index in `dagster-expert/SKILL.md`

### What gets adapted

1. **SKILL.md frontmatter** — reformatted to match this repo's `name`/`description` convention (no `plugin.json`)
2. **dignified-python SKILL.md** — remove references to `/dagster-best-practices` and `/dg` (upstream-internal skill names); the `dagster-expert` skill in this repo handles that
3. **`@` include syntax** — convert `@dignified-python-core.md` to standard relative markdown links; this repo's skill system uses `Read` tool references, not `@` includes
4. **pipeline-builder AGENT.md** — rewrite Orchestration section to be Dagster-first
5. **data-quality-reviewer AGENT.md** — add Dagster-specific review concerns

### No build system changes
`build_preset.py` already handles `preset_skills` copying and `core.skills: "all"` inclusion. No code changes needed.

## Verification

- `uv run python -m scripts.build_preset data-pipeline` succeeds
- Output contains `dignified-python` in `.claude/skills/`
- Output contains `dagster-expert` in `.claude/skills/`
- Agent files in output have updated skill lists
- `uv run pytest` passes (existing tests + any new validation)
- `uv run python -m scripts.smoke_test data-pipeline` passes
