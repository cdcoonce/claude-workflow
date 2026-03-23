# Plan: Fix broken link in python-api deploy skill

> Source: https://github.com/cdcoonce/claude-workflow/issues/23

## Problem

`presets/python-api/skills/deploy/SKILL.md` references `../../../docs/plans/chat-agent/aws-setup.md` in two places (lines 102 and 107). This file doesn't exist — it was carried over from the source project this skill was templated from.

## Fix approach

Remove the project-specific references. This is a generic deploy template, not a specific project's deploy skill:

1. **Line 102** (troubleshooting table): Replace the `aws-setup.md` reference with a generic instruction like "use `aws lambda create-function` to create the function first"
2. **Line 107** (reference documentation section): Remove the entire reference link line since the doc doesn't exist in this repo

## Phase 1: Fix broken references

### What to build

Edit `presets/python-api/skills/deploy/SKILL.md`:

- Remove the broken `aws-setup.md` link from the troubleshooting table entry
- Remove the reference documentation section that links to the nonexistent file

### Acceptance criteria

- [ ] `uv run python -m scripts.smoke_test python-api` passes
- [ ] No references to `chat-agent/aws-setup.md` remain in the file
- [ ] `uv run pytest` green
