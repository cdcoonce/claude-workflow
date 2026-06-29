# Mermaid Diagrams in READMEs

Mermaid diagrams are one of the most valuable parts of a good README. They make complex
systems, data flows, and processes immediately understandable in a way that paragraphs of
text cannot. Use them generously — if something involves flow, sequence, or relationships
between components, a diagram is almost always better than a written description.

> **How to actually build the diagram** (engine choice, syntax, best practices, examples)
> lives in the `diagram` skill — see its [mermaid reference](../../diagram/references/mermaid.md).
> This file covers only the README-specific question: *how many diagrams, and where.*

## When to include a diagram

Include one for any of these that apply to the project:

- **System architecture** — how components connect (almost every README should have one)
- **Data flow / pipelines** — how data moves from source to destination
- **Request/response sequences** — what happens when a user takes an action
- **Decision trees / workflows** — multi-step processes with branches
- **Module dependencies** — how internal modules import from each other
- **CI/CD pipelines** — build/test/deploy stages
- **State machines** — entities with multiple states and transitions
- **UI layout** — dashboard/page structure showing how sections relate

A typical comprehensive README has **3-6 diagrams**; complex projects (data pipelines,
multi-service systems) might have **6-10+**. Don't hold back.

## How many, by project type

### Data pipeline — aim for 4-6:
1. Architecture — sources, processing, outputs
2. Data flow — raw sources through transformations to final output
3. Sequence — what happens when a pipeline run is triggered
4. Module dependency graph
5. Data validation / quality checks flow
6. Scheduling / orchestration

### Web application — aim for 3-5:
1. Architecture — frontend, backend, database, external services
2. Request flow — a key user action end to end
3. CI/CD — build and deployment pipeline
4. Dashboard / UI layout

### CLI tool — aim for 2-4:
1. Architecture — how the CLI interacts with external systems
2. Command flow — what happens when key commands run
3. Configuration resolution — files, env vars, defaults

## Placement

Put the architecture diagram near the top, right after the project description, so readers
get the mental model before the details. Scatter flow/sequence diagrams into the sections
they illustrate rather than clumping them at the end.
