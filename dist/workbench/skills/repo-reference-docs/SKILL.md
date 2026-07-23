---
name: repo-reference-docs
description: >
  Create and maintain a thorough, human-readable Markdown reference-docs set for
  a repository under docs/reference/ — architecture overview, module/directory
  map, data and control flow, conventions and glossary, plus an index. Use when
  someone wants deep repo documentation, a reference-docs set, an architecture
  doc, a "where does X live" module map, a data-flow write-up, or wants existing
  repo reference docs refreshed, updated, or checked for staleness against the
  code. Not for a single front-door README (use readme-generator) or the
  Claude-facing project.md (use project-context).
---

# Repo reference docs

Build and keep current a multi-file, human-readable reference set that explains
how a repository actually works, for engineers onboarding to it. Output lives
only under `docs/reference/`. Every claim is grounded in real source that you
read first — never describe code you have not opened.

**Stay in your lane.** Write only under `docs/reference/`. Never edit `README.md`
(that is `readme-generator`) or `.claude/docs/project.md` (that is
`project-context`); link to them instead.

## The doc set

Produce these under `docs/reference/` (see
[references/doc-templates.md](references/doc-templates.md) for each layout):

- `README.md` — index: one-line summary per doc and a suggested reading order.
- `architecture.md` — what the repo is, major components, how they fit; a
  Mermaid component diagram where it clarifies.
- `module-map.md` — per top-level package/directory: responsibility, key files,
  public surface. The "where does X live" doc.
- `data-flow.md` — how data and control move end to end; key sequences, with a
  Mermaid sequence/flow diagram where it clarifies.
- `conventions.md` — naming, recurring patterns, and a glossary of domain terms.

Trim docs that do not apply to the repo; note the omission in the index rather
than shipping an empty file.

## Modes

Detect which applies from the repo state:

- **Create / update (default).** If `docs/reference/` is absent, generate the
  full set. If present, update only the docs whose covered source changed since
  their baseline (see freshness below); leave untouched docs alone.
- **Check / staleness.** Read-only. Run `scripts/check_docs.py` to report docs
  whose covered paths moved, disappeared, or changed since baseline. Writes
  nothing and exits non-zero on drift, so it works in CI and on any clone.

Follow [references/analysis-method.md](references/analysis-method.md) for how to
analyze a repo, ground each section, and scope an incremental update.

## Freshness & provenance

Each doc ends with a provenance footer the updater and checker both read:

```
<!-- repo-reference-docs: baseline=<commit-sha> covers=<comma,separated,paths> -->
```

`covers` lists the source paths that doc is derived from; `baseline` is the
commit it was last synced to. This lives in-repo so staleness is visible to
everyone and to CI. A richer local analysis cache may be kept under
`~/.workshop/repo-reference-docs/<repo-key>/` purely to speed incremental
updates — it is an optimization, never the source of truth.

## Guardrails

- Read source before writing; cite the paths each section covers. No guessing.
- One reference set per repo; keep docs focused and non-overlapping.
- Regenerate the provenance footer whenever you rewrite a doc.
- Prefer updating in place over full regeneration so human edits survive.
- Do not touch files outside `docs/reference/`.
