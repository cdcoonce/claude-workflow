
## Testing

### Backend
- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=src --cov-report=term-missing`

### Frontend
- Run tests: `npm test`
- Run build: `npm run build`

- Prefer real code over mocks
- Test fixtures in `tests/fixtures/`

## Skills (Preset-Specific)

### `/setup-pre-commit`

**Trigger when:** user wants to add pre-commit hooks, set up Husky, or configure lint-staged.
