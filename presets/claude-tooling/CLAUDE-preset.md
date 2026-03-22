
## Testing

- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=scripts --cov-report=term-missing`
- Test the build system: `uv run pytest tests/ -v`

## Claude Tooling Conventions

- Skills follow the structure defined in `core/skills/write-a-skill/`
- Every SKILL.md must have: name, description, trigger conditions
- Hook scripts must read from stdin and follow the Claude Code hook protocol
- Test all build/diff/smoke scripts with pytest before committing
