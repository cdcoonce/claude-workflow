# data-pipeline

ETL/ELT pipelines, SQL transformations, scheduled data jobs

## Conventions

- SQL keywords lowercase
- Idempotent, re-runnable pipeline stages
- Data-quality checks on every stage

## Skills

| Skill                            | Summary                                                                                                                                                                                                                                                   |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/add-claude-workflow-hook`      | Design and ship a new core hook in this repo (claude-workflow) — fetch the exact event schema, write a stdlib-only fail-open script, TDD it against real subprocess+git behavior, wire it into every affected preset, and push to both GitHub and GitLab. |
| `/commit`                        | Git commit workflow with enforced conventional commit style.                                                                                                                                                                                              |
| `/create-hook`                   | Create and register Claude Code hooks (PreToolUse, PostToolUse) as Python scripts.                                                                                                                                                                        |
| `/daa-code-review`               | AI-powered code quality analysis for Python, Markdown, and Mermaid diagrams.                                                                                                                                                                              |
| `/dagster-expert`                | Expert guidance for working with Dagster and the dg CLI.                                                                                                                                                                                                  |
| `/dbt-expert`                    | Expert guidance for working with dbt Core.                                                                                                                                                                                                                |
| `/design-an-interface`           | Generate multiple radically different interface designs for a module using parallel sub-agents.                                                                                                                                                           |
| `/dev-cycle`                     | Use when user says "dev cycle", "development workflow", "full development pipeline", or invokes /dev-cycle to take a GitHub-issues-driven feature from brainstorm through a merged PR.                                                                    |
| `/dignified-python`              | Production Python coding standards with automatic version detection (3.10-3.13).                                                                                                                                                                          |
| `/github-cli`                    | GitHub CLI (gh) integration for managing issues, pull requests, branches, commits, and code reviews directly from the terminal.                                                                                                                           |
| `/grill-me`                      | Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree.                                                                                                                   |
| `/improve-codebase-architecture` | Explore a codebase to find opportunities for architectural improvement, focusing on making the codebase more testable by deepening shallow modules.                                                                                                       |
| `/improve-skill`                 | Use when user says "improve skill", "benchmark skill", "make skill better", or invokes /improve-skill to raise a skill's benchmark pass rate before merging a PR.                                                                                         |
| `/plan-ceo-review`               | CEO/founder-mode review that rethinks a plan to find the 10-star product.                                                                                                                                                                                 |
| `/prd-to-issues`                 | Break a PRD into independently-grabbable GitHub issues using tracer-bullet vertical slices.                                                                                                                                                               |
| `/prd-to-plan`                   | Turn a PRD into a multi-phase implementation plan using tracer-bullet vertical slices, saved as a local Markdown file in docs/plans/.                                                                                                                     |
| `/project-context`               | Generate or update the `.claude/docs/project.md` file that gives Claude project-specific context.                                                                                                                                                         |
| `/readme-generator`              | Use when the user asks to create, write, generate, update, or improve a README for any project or repository, or asks for project documentation in markdown.                                                                                              |
| `/request-refactor-plan`         | Use when user wants to plan a refactor, create a refactoring RFC, or break a refactor into safe incremental steps.                                                                                                                                        |
| `/security-review`               | Security code review for vulnerabilities with confidence-based reporting.                                                                                                                                                                                 |
| `/setup-pre-commit`              | Set up pre-commit hooks for the current repo.                                                                                                                                                                                                             |
| `/tdd`                           | Test-driven development with red-green-refactor loop.                                                                                                                                                                                                     |
| `/triage-issue`                  | Use when user reports a bug, wants to file an issue, mentions "triage", or wants to investigate and plan a fix for a problem.                                                                                                                             |
| `/write-a-prd`                   | Use when user wants to write a PRD, create a product requirements document, or plan a new feature.                                                                                                                                                        |
| `/write-a-skill`                 | Create new agent skills with proper structure, progressive disclosure, and bundled resources.                                                                                                                                                             |

## Agents

| Agent                 | Role           | Summary                                                                                       |
| --------------------- | -------------- | --------------------------------------------------------------------------------------------- |
| code-reviewer         | `reviewer`     | Reviews code for quality, structure, and correctness                                          |
| data-quality-reviewer | `reviewer`     | Reviews data pipelines for correctness, completeness, and reliability                         |
| pipeline-builder      | `implementer`  | Builds data pipelines with ETL/ELT patterns and orchestration                                 |
| qa-tester             | `qa-tester`    | Evaluates skill instructions against a test suite.                                            |
| skill-analyst         | `analyst`      | Analyzes skill instructions for weaknesses across surface, behavioral, and adversarial tiers. |
| skill-writer          | `skill-writer` | Rewrites Claude Code skills to fix failing test cases.                                        |
| strategy              | `strategy`     | Analyzes stalled skill improvement runs and proposes a concrete rewrite strategy.             |
| tdd-implementer       | `implementer`  | Implements features using test-driven development                                             |

## CLAUDE.md Template

Copy the following into your project's `CLAUDE.md` to reference this plugin:

```
# Project Name

## Plugins

This project uses the data-pipeline plugin for Claude Code configuration.

## Methodology

See plugin documentation for TDD, root cause tracing, and subagent development processes.
```
