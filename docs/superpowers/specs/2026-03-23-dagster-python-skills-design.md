# Add dignified-python (Core) and dagster-expert (Data-Pipeline Preset) Skills

**Date:** 2026-03-23
**Source:** https://github.com/dagster-io/skills/tree/master

## Summary

Port two skills from the dagster-io/skills repository into this template system:

1. **dignified-python** — Production Python coding standards (core skill, all presets)
2. **dagster-expert** — Comprehensive Dagster development guidance (data-pipeline preset skill)

Both are full ports (Approach A) — all reference files copied verbatim, with only structural adaptations to match this repo's conventions.

The two skills are independent and can be implemented in either order. No ordering dependency between them.

## Scope and Non-Goals

**In scope:**
- Port both skills with all reference files
- Wire into core and preset agents via source file edits
- Update data-pipeline manifest, CLAUDE-base.md, and CLAUDE-preset.md
- Update pipeline-builder and data-quality-reviewer agents to be Dagster-first

**Non-goals:**
- No changes to `agent-role-defaults.json` — `dignified-python` is added per-agent, not per-role
- No changes to other presets (python-api, full-stack, analysis, claude-tooling)
- No new test files — existing smoke tests and build validation cover the changes
- No changes to `settings-preset.json`
- No build system (`build_preset.py`) code changes

## Motivation

- **dignified-python** enforces modern Python patterns (LBYL, pathlib, type syntax, API design) across all generated project templates. Wired into both core agents so implementers and reviewers follow the same standards.
- **dagster-expert** provides reference-backed Dagster guidance (CLI commands, asset patterns, automation, 40+ integrations) that prevents Claude from hallucinating APIs. The data-pipeline preset leans into Dagster as the default orchestrator.

## Implementation Order

Steps must be executed in this order to avoid build validation failures:

1. Create `core/skills/dignified-python/` directory and all files
2. Create `presets/data-pipeline/skills/dagster-expert/` directory and all files
3. Update `presets/data-pipeline/manifest.json` to add `"dagster-expert"` to `preset_skills` (directory must exist first or `_validate_manifest` will fail)
4. Edit source agent files (core and preset)
5. Update `core/CLAUDE-base.md` with `/dignified-python` skill index entry
6. Update `presets/data-pipeline/CLAUDE-preset.md` with `/dagster-expert` skill index entry and orchestration section
7. Run build and smoke tests to verify

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

**Source mapping:** Files come from `skills/dignified-python/skills/dignified-python/` in the upstream repo. This double-nesting (`skills/<name>/skills/<name>/`) is intentional in the upstream repo's plugin structure. The `references/` subdirectory in upstream maps directly to `references/` here. Top-level files (`cli-patterns.md`, `subprocess.md`, `dignified-python-core.md`) sit alongside `SKILL.md`.

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
    │   ├── api/
    │   │   ├── INDEX.md
    │   │   ├── general.md
    │   │   ├── agent/                # get.md, list.md
    │   │   ├── alert-policy/         # list.md, sync.md
    │   │   ├── artifact/             # download.md, upload.md
    │   │   ├── asset/                # get.md, get-evaluations.md, get-events.md, get-health.md, list.md
    │   │   ├── code-location/        # add.md, delete.md, get.md, list.md
    │   │   ├── deployment/           # delete.md, get.md, list.md, settings-get.md, settings-set.md
    │   │   ├── organization/         # saml-remove.md, saml-upload.md, settings-get.md, settings-set.md
    │   │   ├── run/                  # get.md, get-events.md, get-logs.md, list.md
    │   │   ├── schedule/             # get.md, get-ticks.md, list.md
    │   │   ├── secret/               # get.md, list.md
    │   │   └── sensor/               # get.md, get-ticks.md, list.md
    │   ├── list/
    │   │   ├── INDEX.md
    │   │   ├── component-tree.md
    │   │   ├── envs.md
    │   │   └── projects.md
    │   ├── plus/
    │   │   ├── INDEX.md
    │   │   ├── login.md
    │   │   ├── config/               # set.md, view.md
    │   │   ├── create/               # ci-api-token.md
    │   │   ├── deploy/               # configure.md, deploy.md
    │   │   ├── integrations/         # dbt-manage-manifest.md
    │   │   └── pull/                 # env.md
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
        ├── INDEX.md
        ├── dagster-airbyte/INDEX.md
        ├── dagster-airlift/INDEX.md
        ├── dagster-aws/INDEX.md
        ├── dagster-azure/INDEX.md
        ├── dagster-celery/INDEX.md
        ├── dagster-celery-docker/INDEX.md
        ├── dagster-celery-k8s/INDEX.md
        ├── dagster-census/INDEX.md
        ├── dagster-dask/INDEX.md
        ├── dagster-databricks/INDEX.md
        ├── dagster-datadog/INDEX.md
        ├── dagster-datahub/INDEX.md
        ├── dagster-dbt/INDEX.md
        ├── dagster-dbt/asset-checks.md
        ├── dagster-dbt/component-based-integration.md
        ├── dagster-dbt/dbt-cloud.md
        ├── dagster-dbt/dependencies.md
        ├── dagster-dbt/pythonic-integration.md
        ├── dagster-dbt/scaffolding.md
        ├── dagster-deltalake/INDEX.md
        ├── dagster-deltalake-pandas/INDEX.md
        ├── dagster-deltalake-polars/INDEX.md
        ├── dagster-dlt/INDEX.md
        ├── dagster-docker/INDEX.md
        ├── dagster-duckdb/INDEX.md
        ├── dagster-duckdb-pandas/INDEX.md
        ├── dagster-duckdb-polars/INDEX.md
        ├── dagster-duckdb-pyspark/INDEX.md
        ├── dagster-embedded-elt/INDEX.md
        ├── dagster-fivetran/INDEX.md
        ├── dagster-gcp/INDEX.md
        ├── dagster-gcp-pandas/INDEX.md
        ├── dagster-gcp-pyspark/INDEX.md
        ├── dagster-github/INDEX.md
        ├── dagster-great-expectations/INDEX.md
        ├── dagster-hightouch/INDEX.md
        ├── dagster-iceberg/INDEX.md
        ├── dagster-jupyter/INDEX.md
        ├── dagster-k8s/INDEX.md
        ├── dagster-looker/INDEX.md
        ├── dagster-mlflow/INDEX.md
        ├── dagster-msteams/INDEX.md
        ├── dagster-mysql/INDEX.md
        ├── dagster-omni/INDEX.md
        ├── dagster-openai/INDEX.md
        ├── dagster-pagerduty/INDEX.md
        ├── dagster-pandas/INDEX.md
        ├── dagster-pandera/INDEX.md
        ├── dagster-papertrail/INDEX.md
        ├── dagster-polars/INDEX.md
        ├── dagster-polytomic/INDEX.md
        ├── dagster-postgres/INDEX.md
        ├── dagster-powerbi/INDEX.md
        ├── dagster-prometheus/INDEX.md
        ├── dagster-pyspark/INDEX.md
        ├── dagster-sigma/INDEX.md
        ├── dagster-slack/INDEX.md
        ├── dagster-sling/INDEX.md
        ├── dagster-snowflake/INDEX.md
        ├── dagster-snowflake-pandas/INDEX.md
        ├── dagster-snowflake-polars/INDEX.md
        ├── dagster-snowflake-pyspark/INDEX.md
        ├── dagster-spark/INDEX.md
        ├── dagster-ssh/INDEX.md
        ├── dagster-tableau/INDEX.md
        ├── dagster-twilio/INDEX.md
        └── dagster-wandb/INDEX.md
```

## Agent Wiring

All agent wiring is done by editing source AGENT.md files directly. The build system copies these files verbatim — no build-time transformation of agent frontmatter occurs.

### Core Agents (all presets get these changes)

Edit `core/agents/tdd-implementer/AGENT.md` frontmatter:
```yaml
skills:
  add: [tdd, commit, dignified-python]
```

Edit `core/agents/code-reviewer/AGENT.md` frontmatter:
```yaml
skills:
  add: [daa-code-review, dignified-python]
```

No changes to agent body content for core agents.

### Data-Pipeline Preset Agents

Edit `presets/data-pipeline/agents/pipeline-builder/AGENT.md` frontmatter:
```yaml
skills:
  add: [tdd, commit, dagster-expert, dignified-python]
```

**Body rewrite — Orchestration section:** Remove the Airflow (lines 56-62), Dagster (lines 64-70), and Prefect (lines 72-78) subsections. Replace with a single Dagster-first section. The current Dagster subsection (lines 64-70) is the starting point. Expand it to replace the full Orchestration section with 8-10 bullet points covering:

- Assets as the primary abstraction for pipeline outputs
- Resources for external system connections
- IO managers for consistent read/write patterns
- Partitions for time-series data
- Sensors for event-driven triggers
- Declarative automation for condition-based scheduling
- `dg` CLI as the primary tool for project interaction
- Defer to `dagster-expert` skill for detailed CLI commands, patterns, and integration references

Keep all other sections (ETL/ELT Patterns, Data Validation, Schema Evolution, Idempotency, Backfill Strategies, Monitoring and Alerting) unchanged.

Edit `presets/data-pipeline/agents/data-quality-reviewer/AGENT.md` frontmatter:
```yaml
skills:
  add: [daa-code-review, dagster-expert, dignified-python]
```

**Body addition — new "Dagster-Specific Review" section** after existing sections. Content as bullet points:

- Verify assets have meaningful metadata (descriptions, tags, group assignments)
- Check partition definitions align with data arrival patterns and query access patterns
- Validate IO manager configuration matches the target storage system
- Ensure resources are properly scoped (not shared mutable state)
- Check that asset dependencies form a valid DAG with no unnecessary coupling
- Verify sensors have appropriate minimum interval and error handling
- Confirm automation conditions match the intended materialization frequency
- Defer to `dagster-expert` skill for detailed Dagster API validation

## CLAUDE Markdown Updates

### core/CLAUDE-base.md — Add skill index entry

Add after the existing `/security-review` entry (before `## Project Context`):

```markdown
### `/dignified-python`

**Trigger when:** writing, reviewing, or refactoring Python code. Also when user asks about type hints, LBYL patterns, pathlib, code quality, or "make this pythonic".
```

### presets/data-pipeline/CLAUDE-preset.md — Add skill index and orchestration

Add new sections:

```markdown
## Orchestration

- Default orchestrator: Dagster
- Use `uv run dg` CLI for project interaction (scaffold, launch, list, check)
- Define assets for each meaningful data artifact
- Use the `dagster-expert` skill for CLI commands, patterns, and integration references

## Skills

### `/dagster-expert`

**Trigger when:** doing any task involving Dagster — creating projects, adding definitions, working with assets, automation, components, integrations, or the `dg` CLI. ALWAYS use before answering Dagster-specific questions.
```

Keep existing conventions (Testing, Data Pipeline Conventions).

## Manifest Change

**Edit `presets/data-pipeline/manifest.json`** — add `"dagster-expert"` to `preset_skills`:
```json
{
  "preset_skills": ["dagster-expert"]
}
```

This must happen AFTER the `presets/data-pipeline/skills/dagster-expert/` directory exists, or `_validate_manifest` will fail at build time.

No change needed for `dignified-python` — `core.skills: "all"` picks it up automatically.

## Adaptations from Upstream

### What stays verbatim
- All reference files (dagster-expert and dignified-python)
- `dignified-python-core.md`, version files, advanced references
- The reference index in `dagster-expert/SKILL.md`

### What gets adapted

1. **SKILL.md frontmatter** — reformatted to match this repo's `name`/`description` convention (no `plugin.json`)
2. **dignified-python SKILL.md** — remove the "When to Use This Skill vs. Others" table rows that reference `/dagster-best-practices` and `/dg` (upstream-internal skill names). Replace with a row pointing to `/dagster-expert` for Dagster-specific patterns. Delete, do not leave stubs.
3. **`@` include syntax** — convert `@dignified-python-core.md` to a relative markdown link: `[dignified-python-core.md](dignified-python-core.md)`, matching the convention used in existing SKILL.md files in this repo
4. **dagster-expert SKILL.md internal links** — verify all relative links in the reference index resolve correctly after porting. The upstream `./references/` prefix maps directly to `references/` in our structure, so links should work as-is, but must be validated.
5. **pipeline-builder AGENT.md** — rewrite Orchestration section to be Dagster-first (see Agent Wiring above for detailed content)
6. **data-quality-reviewer AGENT.md** — add Dagster-specific review section (see Agent Wiring above for detailed content)

### No build system changes
`build_preset.py` already handles `preset_skills` copying and `core.skills: "all"` inclusion. No code changes needed.

## Verification

- `uv run python -m scripts.build_preset data-pipeline` succeeds
- `dist/data-pipeline/.claude/skills/dignified-python/SKILL.md` exists
- `dist/data-pipeline/.claude/skills/dagster-expert/SKILL.md` exists
- Parse frontmatter of `dist/data-pipeline/.claude/agents/pipeline-builder/AGENT.md` and verify `dagster-expert` and `dignified-python` appear in `skills.add`
- Parse frontmatter of `dist/data-pipeline/.claude/agents/tdd-implementer/AGENT.md` and verify `dignified-python` appears in `skills.add`
- `uv run pytest` passes
- `uv run python -m scripts.smoke_test data-pipeline` passes with zero link resolution errors
