---
name: diagram
description: >
  Create diagrams — flowcharts, architecture, data flow, sequence, state machines,
  ERDs, org charts, mind maps. Routes between Mermaid (text-first, renders inline in
  markdown) and draw.io (rich editable XML) based on where the diagram will live. Use
  when the user wants to diagram, chart, visualize, draw, or map a system, flow, or
  relationship.
---

# Diagramming

One skill, two engines. The job is to produce the *right kind* of diagram for where it
will live — not to default to one tool. Decide the engine first, then generate.

## Step 1 — Scope before drawing

Ask up to 2-3 quick questions unless the answer is already obvious from context:

1. **What is being diagrammed?** (architecture, data flow, sequence, decision tree,
   state machine, ERD, org chart, mind map…)
2. **Where will it live?** (a README/PR/markdown doc → favors Mermaid; a standalone
   artifact, deck, or hand-tuned diagram → favors draw.io)
3. **Who is the audience?** (engineers reading docs vs. stakeholders wanting a polished
   editable picture)

Don't over-ask. If the user says "add a diagram to the README," you already know.

## Step 2 — Pick the engine

| Situation | Engine |
|-----------|--------|
| Goes in a README, PR, markdown doc, or any docs-as-code surface | **Mermaid** |
| Architecture / data flow / sequence / state / ERD that lives in repo docs | **Mermaid** |
| Renders on GitHub/GitLab/Obsidian without tooling; must diff cleanly in git | **Mermaid** |
| Rich or hand-tuned layout, precise positioning, large complex canvas | **draw.io** |
| Stakeholder deliverable, exported to PNG/SVG, or edited later in a GUI | **draw.io** |
| User explicitly names a tool | **that tool** |
| Ambiguous | **default Mermaid**, and offer draw.io |

Rule of thumb: **Mermaid is the default** because the docs-as-code grain wins most of the
time — text in the repo, renders everywhere, no external app. Reach for draw.io when the
diagram is an *artifact in its own right* rather than documentation.

## Step 3 — Generate

- **Mermaid** → follow [references/mermaid.md](references/mermaid.md). Emit a fenced
  ```mermaid block, keep each diagram focused (split at ~15 nodes), label every edge,
  use descriptive node IDs.
- **draw.io** → follow [references/drawio.md](references/drawio.md). Elicit intent first,
  classify against the Diagram Type Matrix, then emit an uncompressed
  `<mxGraphModel adaptiveColors="auto">` document so it imports directly into draw.io /
  diagrams.net. Save as `*.drawio` (or `*.drawio.xml`).

## Step 4 — Verify

- **Mermaid:** check syntax mentally — balanced brackets, valid diagram-type keyword,
  no reserved-word node IDs (`end`, `class`). When this runs inside a code review, the
  `daa-code-review` skill's mermaid-checks reference is the authority on validation.
- **draw.io:** apply the reference's well-formedness rules — unique `mxCell` ids; edges
  in expanded form with an `mxGeometry` child (never self-closed); coordinates on a 10px
  grid; no XML comments; escaped special characters; valid XML.

## Notes

- Prefer **one diagram that explains one thing well** over a sprawling everything-map.
  Multiple focused diagrams beat a single dense one.
- This skill is the single home for diagram-generation guidance. Other skills (e.g.
  `readme-generator`) decide *how many* diagrams and *where* they go, then defer here for
  *how* to build them.
- **Attribution:** the draw.io engine reference is vendored from Anthropic's
  `drawio-general` skill — see the source note at the top of
  [references/drawio.md](references/drawio.md).
