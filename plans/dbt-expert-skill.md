# Plan: dbt-expert Skill for data-pipeline Preset

> Source PRD: GitLab #11 — "PRD: Add dbt-expert skill to data-pipeline preset"
> Design Spec: `docs/superpowers/specs/2026-03-24-dbt-expert-skill-design.md`

## Architectural decisions

Durable decisions that apply across all phases:

- **Skill location**: `presets/data-pipeline/skills/dbt-expert/` (preset-specific, not core)
- **SKILL.md format**: YAML frontmatter + sections + `BEGIN/END GENERATED INDEX` reference index (mirrors `dagster-expert`)
- **Reference structure**: `references/{topic}.md` — flat directory with 4 files: `modeling.md`, `testing.md`, `cli.md`, `docs.md`
- **Content source**: Rewritten from [dbt-labs/dbt-agent-skills](https://github.com/dbt-labs/dbt-agent-skills), stripped of all dbt Cloud/MCP references, adapted for dbt Core (open-source)
- **dagster-dbt boundary**: Integration content stays in `dagster-expert` (`references/integrations/dagster-dbt/`). `dbt-expert` covers dbt-native concepts only.
- **Agent wiring**: Both `pipeline-builder` and `data-quality-reviewer` add `dbt-expert` to `skills.add`
- **Build system**: `manifest.json` `preset_skills` array gets `dbt-expert` added

---

## Phase 1: Tracer bullet — SKILL.md + modeling reference + build verification

**User stories**: Skill is discoverable by the build system, has one working reference file, passes smoke test end-to-end

### What to build

Create the `dbt-expert` skill skeleton with its SKILL.md (frontmatter, core concepts, CLI section, CRITICAL directive, reference index) and the first reference file (`modeling.md` — the largest and most important reference covering model types, DAG organization, materializations, ref/source, naming conventions, and Jinja patterns). Update `manifest.json` to include `dbt-expert` in `preset_skills`. Run smoke test to verify the build pipeline discovers and includes the new skill.

### Acceptance criteria

- [ ] `presets/data-pipeline/skills/dbt-expert/SKILL.md` exists with YAML frontmatter, core concepts, CLI section, CRITICAL directive, and reference index
- [ ] `presets/data-pipeline/skills/dbt-expert/references/modeling.md` exists with ~150-200 lines covering model types, materializations, ref/source, DAG layers, naming conventions, Jinja patterns
- [ ] `manifest.json` `preset_skills` includes `"dbt-expert"`
- [ ] `uv run python -m scripts.smoke_test data-pipeline` passes
- [ ] No dbt Cloud or MCP references in any new file

---

## Phase 2: Complete reference content — testing, CLI, docs

**User stories**: All dbt topics covered with reference material for the agent to consult

### What to build

Add the remaining 3 reference files: `testing.md` (generic tests, unit tests, custom tests, severity, test selection), `cli.md` (core commands, selection syntax, graph operators, quiet mode), and `docs.md` (docs generate/serve, llms.txt, markdown URL convention). Update the SKILL.md reference index to include all 4 files. All content rewritten from upstream dbt-agent-skills, stripped of Cloud references.

### Acceptance criteria

- [ ] `references/testing.md` exists (~150-200 lines) covering generic tests, unit test YAML format, custom tests, severity, test selection
- [ ] `references/cli.md` exists (~80-120 lines) covering dbt build/run/test/show/compile/debug, selection syntax, graph operators, quiet mode
- [ ] `references/docs.md` exists (~40-60 lines) covering dbt docs generate/serve, llms.txt convention, markdown URL convention (noting these are docs.getdbt.com features)
- [ ] SKILL.md reference index lists all 4 reference files with accurate descriptions
- [ ] No dbt Cloud or MCP references in any new file
- [ ] `uv run python -m scripts.smoke_test data-pipeline` still passes

---

## Phase 3: Agent integration + final verification

**User stories**: Both pipeline agents load dbt-expert and have dbt-specific guidance sections, full test suite passes

### What to build

Update `pipeline-builder/AGENT.md`: add `dbt-expert` to `skills.add`, add a "dbt Transformations" section (~10 lines) covering model organization, `dbt build` preference, and dagster-dbt bridge. Update `data-quality-reviewer/AGENT.md`: add `dbt-expert` to `skills.add`, add a "dbt-Specific Review" section (~10 lines) covering model descriptions, test coverage, ref/source validation, naming conventions, and unit test mocking. Run full test suite and smoke test.

### Acceptance criteria

- [ ] `pipeline-builder/AGENT.md` `skills.add` includes `dbt-expert`
- [ ] `pipeline-builder/AGENT.md` has "dbt Transformations" section
- [ ] `data-quality-reviewer/AGENT.md` `skills.add` includes `dbt-expert`
- [ ] `data-quality-reviewer/AGENT.md` has "dbt-Specific Review" section
- [ ] `uv run pytest` passes
- [ ] `uv run python -m scripts.smoke_test data-pipeline` passes
