# dbt-expert Skill — Design Spec

## Overview

A new `dbt-expert` skill for the `data-pipeline` preset, adapted from [dbt-labs/dbt-agent-skills](https://github.com/dbt-labs/dbt-agent-skills). Provides expert guidance for working with dbt Core (open-source) — modeling, testing, CLI commands, and documentation. Mirrors the existing `dagster-expert` skill in structure and conventions.

### Scope

- **In scope:** 4 upstream skills rewritten for dbt Core open-source: analytics engineering, unit testing, CLI commands, docs fetching
- **Out of scope:** dbt Cloud features (job monitoring, Semantic Layer API, MCP server config), migration skills, DAG visualization (extras)

### Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Approach | Adapt & Rewrite | Match dagster-expert pattern; strip Cloud references; right-sized for open-source dbt |
| Skill structure | Single `dbt-expert` with 4 reference files | Parallels dagster-expert; simpler manifest; topics are tightly related |
| Agent integration | Add to both pipeline-builder and data-quality-reviewer | dbt and Dagster are complementary — both agents need dbt context |
| Source material | 4 of 8 core skills from dbt-agent-skills | Filtered to open-source-only: analytics engineering, commands, unit tests, docs |

---

## File Structure

```
presets/data-pipeline/skills/dbt-expert/
├── SKILL.md
└── references/
    ├── modeling.md
    ├── testing.md
    ├── cli.md
    └── docs.md
```

---

## SKILL.md Design (~50-60 lines)

### Frontmatter

```yaml
---
name: dbt-expert
description:
  Expert guidance for working with dbt Core. ALWAYS use before doing any task that requires
  knowledge specific to dbt, or that references models, tests, sources, SQL transformations,
  or dbt CLI commands. Common tasks include creating or modifying models, writing tests,
  running dbt commands, organizing the DAG, or answering questions about dbt project structure.
---
```

### Sections

| Section | Purpose | Est. Lines |
|---------|---------|------------|
| Frontmatter | Name and description with triggers | 7 |
| Core dbt Concepts | Brief definitions (model, source, ref, test, seed, snapshot) | 8 |
| CLI section | dbt Core commands, selection syntax, common patterns | 8 |
| CRITICAL directive | Always read reference files before answering | 4 |
| Reference Index | Generated index with descriptions | ~20 |
| **Total** | | **~50** |

### Core dbt Concepts

Brief definitions only (detail lives in references):

- **Model**: A SQL `SELECT` statement that dbt materializes as a view, table, or incremental table
- **Source**: A declaration of raw data tables that exist in the warehouse, referenced via `source()`
- **ref()**: The function used to reference other models, building the DAG automatically
- **Test**: An assertion about data (generic tests in YAML, custom tests as SQL, unit tests as YAML mocks)
- **Seed**: A CSV file loaded into the warehouse via `dbt seed`
- **Snapshot**: A table that captures type-2 slowly changing dimension history

### CLI Section

- Default to `dbt build` for combined run + test in dependency order
- Use `--select` and `--exclude` with graph operators (`+model+`) for targeted runs
- Use `--quiet` mode in CI for cleaner logs
- Prefer `dbt show` for quick SQL validation without materializing

### CRITICAL Directive

Same pattern as dagster-expert:
> NEVER answer from memory or guess at dbt syntax, YAML schema, or CLI flags. ALWAYS read the relevant reference file(s) from the Reference Index below before responding.

### Reference Index

```markdown
<!-- BEGIN GENERATED INDEX -->

- [Modeling Patterns](./references/modeling.md) — model types, materializations, ref/source, DAG organization, naming conventions, Jinja patterns
- [Testing](./references/testing.md) — generic tests, unit tests, custom tests, test YAML format, severity levels
- [CLI Commands](./references/cli.md) — dbt build, run, test, show, compile, debug; selection syntax, graph operators
- [Documentation](./references/docs.md) — dbt docs generate, dbt docs serve, llms.txt, markdown URL convention

<!-- END GENERATED INDEX -->
```

---

## Reference File Design

### modeling.md (~150-200 lines)

**Source:** `using-dbt-for-analytics-engineering` skill from dbt-agent-skills

**Content:**
- Model types: view, table, incremental, ephemeral — when to use each
- `ref()` and `source()` usage — never hardcode table names
- DAG layer organization: staging (`stg_`) → intermediate (`int_`) → marts (`fct_`, `dim_`)
- Naming conventions per layer
- Materialization strategies: dev (views for speed) vs prod (tables/incremental for performance)
- Jinja patterns: `{{ config() }}`, conditional logic, macros
- Cost management: `LIMIT` in dev, incremental models in prod, avoiding full-table scans
- Data handling safeguards: never `DROP`/`DELETE`/`TRUNCATE` outside of dbt's materialization

**Strips:** dbt Cloud job scheduling, MCP tool references, Cloud-specific run management

### testing.md (~150-200 lines)

**Source:** `adding-dbt-unit-test` skill from dbt-agent-skills

**Content:**
- Generic tests: `unique`, `not_null`, `accepted_values`, `relationships` — YAML schema
- Unit test YAML format: `given` (mock inputs), `expect` (expected output)
- Input formats: dict, csv, sql — when to use each
- Testing individual models vs testing across the DAG
- Custom tests as SQL statements returning failing rows
- Test severity: `warn` vs `error` — when to use each
- Test selection: `dbt test --select model_name`, tag-based selection
- Test organization: co-located in `schema.yml` vs dedicated test files

**Strips:** dbt Cloud test monitoring, Cloud API for test results, MCP test execution tools

### cli.md (~80-120 lines)

**Source:** `running-dbt-commands` skill from dbt-agent-skills

**Content:**
- Core commands: `build`, `run`, `test`, `show`, `compile`, `debug`, `seed`, `snapshot`, `docs`
- `dbt build` as the preferred command (run + test in DAG order)
- Selection syntax: `--select model_name`, `--select tag:daily`, `--select path:models/staging`
- Graph operators: `+model` (upstream), `model+` (downstream), `+model+` (both)
- `--exclude` for skipping specific models
- `--quiet` / `-q` mode for CI pipelines
- `dbt show` for quick SQL validation without materializing
- `dbt compile` for reviewing generated SQL
- `dbt debug` for connection and configuration validation
- dbt Core vs Fusion CLI: note that Fusion (`dbtf`) is an alternative engine, not required

**Strips:** dbt Cloud CLI (`dbt-cloud`), MCP server tool invocations, Cloud job run management

### docs.md (~40-60 lines)

**Source:** `fetching-dbt-docs` skill from dbt-agent-skills

**Content:**
- `dbt docs generate` — builds documentation site from model descriptions, tests, and DAG
- `dbt docs serve` — local server for browsing docs
- `.md` URL convention: append `.md` to any dbt docs URL to get markdown (useful for AI consumption)
- `llms.txt` and `llms-full.txt` — index files for AI tools to discover dbt documentation
- Writing good model descriptions: what the model represents, key business logic, grain

**Strips:** Cloud-hosted documentation, Cloud API for doc retrieval

---

## Agent Updates

### pipeline-builder/AGENT.md

**Skills change:**
```yaml
skills:
  add: [tdd, commit, dagster-expert, dbt-expert, dignified-python]
```

**New section (~10 lines) — "dbt Transformations":**
- dbt is the default SQL transformation layer within Dagster pipelines
- Organize models in layers: staging → intermediate → marts
- Always reference `dbt-expert` skill before writing models or tests
- Prefer `dbt build` over separate `run` + `test` for consistency
- Use Dagster's dbt integration (`dagster-dbt`) to orchestrate dbt as assets

### data-quality-reviewer/AGENT.md

**Skills change:**
```yaml
skills:
  add: [daa-code-review, dagster-expert, dbt-expert, dignified-python]
```

**New section (~10 lines) — "dbt-Specific Review":**
- Verify models have descriptions and appropriate materialization strategy
- Check that tests cover primary keys, not-null constraints, and accepted values
- Validate ref/source usage — no hardcoded table names
- Ensure model naming follows staging/intermediate/marts convention
- Check that unit tests mock upstream dependencies correctly
- Verify incremental models handle late-arriving data

---

## Manifest Update

**`presets/data-pipeline/manifest.json`:**
```json
{
  "preset_skills": ["dagster-expert", "dbt-expert"]
}
```

Only the `preset_skills` array changes. All other fields remain the same.

---

## Estimated Sizes

| File | Lines |
|------|-------|
| `SKILL.md` | ~50-60 |
| `references/modeling.md` | ~150-200 |
| `references/testing.md` | ~150-200 |
| `references/cli.md` | ~80-120 |
| `references/docs.md` | ~40-60 |
| Agent section additions | ~10 each |
| **Total new content** | **~490-660** |
