## Testing

- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=src --cov-report=term-missing`
- Prefer real code over mocks
- Test fixtures in `tests/fixtures/`

## Skills (Preset-Specific)

### `/deploy`

**Trigger when:** user asks to deploy, redeploy, push to Lambda, update the service, or after updating lambda_function.py.
