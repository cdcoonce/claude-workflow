
## Testing

- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=src --cov-report=term-missing`
- Prefer real code over mocks
- Test fixtures in `tests/fixtures/`
- For SQL transformations, test with sample data in fixtures

## Data Pipeline Conventions

- SQL files use lowercase keywords
- Pipeline stages should be idempotent where possible
- Log row counts at each transformation stage
