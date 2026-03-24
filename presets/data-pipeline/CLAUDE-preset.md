
## Testing

- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=src --cov-report=term-missing`
- Prefer real code over mocks
- Test fixtures in `tests/fixtures/`
- For SQL transformations, test with sample data in fixtures

## Orchestration

- Default orchestrator: Dagster
- Use `uv run dg` CLI for project interaction (scaffold, launch, list, check)
- Define assets for each meaningful data artifact
- Use the `dagster-expert` skill for CLI commands, patterns, and integration references

## Skills

### `/dagster-expert`

**Trigger when:** doing any task involving Dagster — creating projects, adding definitions, working with assets, automation, components, integrations, or the `dg` CLI. ALWAYS use before answering Dagster-specific questions.

## Data Pipeline Conventions

- SQL files use lowercase keywords
- Pipeline stages should be idempotent where possible
- Log row counts at each transformation stage
