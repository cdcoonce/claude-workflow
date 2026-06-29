# draw.io Generation Guide

> **Source:** Vendored from Anthropic's `drawio-general` skill (the `anthropic-skills`
> collection). Adapted into a reference for the `diagram` skill by stripping the
> standalone-skill frontmatter; the body content is otherwise that skill's. Kept in sync
> manually — re-pull from the upstream skill when it updates.

The draw.io engine for the `diagram` skill. Produces valid, well-formed draw.io
(diagrams.net) XML for any diagram type. Prioritizes understanding intent before
generating anything, so the first output is worth using rather than a guess that needs
rework. Reach for draw.io over Mermaid when the diagram is a standalone artifact:
hand-tuned layout, precise positioning, a large canvas, a stakeholder deliverable, or
something edited later in the draw.io GUI. Save output as `*.drawio` or `*.drawio.xml`.

---

## Workflow

1. **Elicit intent** — Ask the questions in the Intent Elicitation section
   before writing any XML. Skip only if the user's request fully answers them.
2. **Classify the diagram** — Identify the type and check the Diagram Type
   Matrix to select the right shapes, layout direction, and edge style.
3. **Decide on shape libraries** — Use the Shape Library Decision rules to
   determine whether generic shapes suffice or domain-specific ones are needed.
4. **Plan the layout on paper first** — Sketch node positions, grouping, and
   edge routing mentally before writing XML. Never generate XML without a plan.
5. **Generate well-formed XML** — Follow all rules in this guide exactly.
6. **Deliver and explain** — Wrap the XML in a fenced code block. Add a brief
   plain-English description of the structure and any notes (e.g., shape
   libraries to enable).

---

## Intent Elicitation

Before generating XML, resolve every unknown below. Ask only what isn't
clear from context — don't interrogate users who gave you a fully-specified
request. Group multiple questions into one message.

### What to clarify

**Diagram type** — If ambiguous, name the two most likely types and ask.
A "process flow" could be a swimlane BPMN, a simple linear flowchart, or a
state machine. These produce very different diagrams.

**Scope and nodes** — How many nodes are expected? A 5-node flowchart and a
50-node org chart need completely different layout strategies.

**Audience and purpose** — Is this for a quick internal sketch, a
presentation, or a published document? Affects label verbosity, color usage,
and whether annotations are needed.

**Direction** — Should the diagram read top-to-bottom, left-to-right, or is
radial/hierarchical layout preferred?

**Grouping** — Are there logical clusters or phases that should be visually
grouped (containers, swimlanes, color bands)?

**Labels and detail level** — Short node names only, or does each node also
need a subtitle, status, owner, or other metadata?

**Existing content** — If the user has a list, table, description, or prose
they want diagrammed, ask for it before generating anything.

### Clarification threshold

If answering the above would require more than two questions, make reasonable
assumptions, state them explicitly at the top of the response, and proceed.
Don't stall a user who wants a quick draft.

---

## Diagram Type Matrix

| Diagram Type | Layout Direction | Primary Shapes | Edge Style | Use Containers? |
|---|---|---|---|---|
| Flowchart | Top-to-bottom | Rounded rect (process), diamond (decision), circle/oval (start/end) | orthogonalEdgeStyle | No (unless lanes) |
| Swimlane / Cross-functional | Left-to-right or top-to-bottom | Swimlane containers, rounded rects inside | orthogonalEdgeStyle | Yes — swimlane per actor |
| State machine | Top-to-bottom or radial | Rounded rect (state), oval (start/end), self-loop edges | elbowEdgeStyle | No |
| Sequence diagram | Left-to-right | Swimlane per actor (vertical), horizontal arrows | orthogonalEdgeStyle | Yes — one swimlane per lifeline |
| ERD | Left-to-right | Rectangle per entity, lines with cardinality edge labels | orthogonalEdgeStyle | No (use groups for aggregates) |
| Org chart | Top-to-bottom | Rounded rect or mxgraph.org shapes | orthogonalEdgeStyle | No |
| Mind map | Radial from center | Rounded rect, ellipse for root | elbowEdgeStyle | No |
| Process / Value stream | Left-to-right | Rounded rect, arrows with labels for handoffs | orthogonalEdgeStyle | Optional swimlanes |
| Decision tree | Top-to-bottom | Diamond (branch), rounded rect (leaf) | orthogonalEdgeStyle | No |
| Timeline | Left-to-right | Rect per milestone on a horizontal axis line | No arrows (axis line only) | Optional grouping by phase |
| Class diagram (UML) | Left-to-right | Rectangle with 3 compartments (name/attrs/methods) | orthogonalEdgeStyle with labels | Optional packages as containers |
| BPMN (basic) | Left-to-right | Circle (event), rounded rect (task), diamond (gateway) | orthogonalEdgeStyle | Yes — pool + lanes |

When the diagram type doesn't appear in the table, select the most
structurally similar type and note the adaptation.

---

## XML Skeleton

Every draw.io file follows this structure exactly:

```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- shapes and edges with parent="1" or a layer/container id -->
  </root>
</mxGraphModel>
```

- `id="0"` — document root; always present, never modified
- `id="1"` — default layer; always present
- All top-level shapes: `parent="1"`
- `adaptiveColors="auto"` — enables dark mode support

---

## Core Shape Reference

### Rounded Rectangle (default process / node)
```xml
<mxCell id="n1" value="Step Name" style="rounded=1;whiteSpace=wrap;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="140" height="60" as="geometry"/>
</mxCell>
```

### Diamond — decision / gateway
```xml
<mxCell id="n2" value="Condition?" style="rhombus;whiteSpace=wrap;" vertex="1" parent="1">
  <mxGeometry x="100" y="220" width="140" height="90" as="geometry"/>
</mxCell>
```

### Oval / Circle — start, end, event
```xml
<mxCell id="n3" value="Start" style="ellipse;whiteSpace=wrap;" vertex="1" parent="1">
  <mxGeometry x="100" y="40" width="80" height="60" as="geometry"/>
</mxCell>
```

### Filled circle — BPMN start event / terminal
```xml
<mxCell id="n4" value="" style="ellipse;fillColor=#000000;strokeColor=#000000;" vertex="1" parent="1">
  <mxGeometry x="130" y="40" width="20" height="20" as="geometry"/>
</mxCell>
```

### Database / Cylinder
```xml
<mxCell id="n5" value="Users DB" style="shape=cylinder3;whiteSpace=wrap;" vertex="1" parent="1">
  <mxGeometry x="100" y="340" width="80" height="70" as="geometry"/>
</mxCell>
```

### Document shape
```xml
<mxCell id="n6" value="Report" style="shape=mxgraph.flowchart.document;whiteSpace=wrap;" vertex="1" parent="1">
  <mxGeometry x="100" y="440" width="100" height="60" as="geometry"/>
</mxCell>
```

### Text / Annotation
```xml
<mxCell id="n7" value="Note text here" style="text;whiteSpace=wrap;html=1;" vertex="1" parent="1">
  <mxGeometry x="300" y="100" width="120" height="40" as="geometry"/>
</mxCell>
```

### Edge (connector) — ALWAYS expanded form, never self-closing
```xml
<mxCell id="e1" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="n1" target="n2" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### Labeled edge
```xml
<mxCell id="e2" value="Yes" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="n2" target="n3" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### Edge with explicit waypoints (prevents overlaps)
```xml
<mxCell id="e3" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="n1" target="n5" parent="1">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="300" y="150"/>
      <mxPoint x="300" y="360"/>
    </Array>
  </mxGeometry>
</mxCell>
```

---

## Style Properties Reference

| Property | Values | Purpose |
|---|---|---|
| `rounded=1` | 0 or 1 | Rounded corners on rects |
| `whiteSpace=wrap` | wrap | Text wraps inside shape |
| `fillColor=#dae8fc` | hex | Background fill |
| `strokeColor=#6c8ebf` | hex | Border color |
| `fontColor=#333333` | hex | Label text color |
| `dashed=1` | 0 or 1 | Dashed border or edge line |
| `edgeStyle=orthogonalEdgeStyle` | — | Right-angle connectors (default) |
| `edgeStyle=elbowEdgeStyle` | — | Elbow connectors (good for state machines) |
| `exitX` / `exitY` | 0–1 | Which side an edge leaves its source |
| `entryX` / `entryY` | 0–1 | Which side an edge enters its target |
| `rounded=1` (on edges) | — | Smooth bends |
| `jettySize=auto` | — | Better port spacing on orthogonal edges |
| `container=1;pointerEvents=0` | — | Any shape acting as a container |
| `swimlane;startSize=30` | — | Titled swimlane / pool container |
| `group` | — | Invisible grouping container |
| `startArrow` / `endArrow` | open, block, classic, none, etc. | Arrowhead types |

---

## Edge Rules (CRITICAL)

1. **Every edge must have a `<mxGeometry relative="1" as="geometry"/>` child.** Self-closing edge `mxCell` tags are invalid and silently break rendering.
2. Space nodes at least 60px apart; prefer 200px horizontal / 120px vertical.
3. Use `exitX`/`exitY`/`entryX`/`entryY` to route edges out different sides of a node and prevent stacking.
4. Leave at least 20px of straight segment before an arrowhead. If source and target are close or nearly axis-aligned, the auto-router may place a bend right against the shape — fix by spacing nodes further apart or adding explicit waypoints.
5. Add `Array as="points"` waypoints when edges would otherwise cross or overlap.
6. Use `jettySize=auto` for cleaner port spacing on `orthogonalEdgeStyle` edges.
7. Do not wrap edge `value` labels in HTML markup to change font size — edge labels are already rendered at 11px (vs 12px for vertices).

---

## Containers and Grouping

### When to use a container vs. just grouping visually

Use **swimlanes** when the container represents an actor, phase, or domain that itself has connections, or when a title bar is needed for clarity.

Use an **invisible group** when shapes should move together but need no visual boundary.

Use a **custom container** (any shape with `container=1;pointerEvents=0;`) for color-banded regions, phases, or zones with a visible background but no title bar.

### Swimlane (titled, connectable header)
```xml
<mxCell id="sw1" value="Phase 1: Discovery" style="swimlane;startSize=30;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="400" height="200" as="geometry"/>
</mxCell>
<mxCell id="c1" value="Research" style="rounded=1;whiteSpace=wrap;" vertex="1" parent="sw1">
  <mxGeometry x="20" y="50" width="120" height="60" as="geometry"/>
</mxCell>
```

### Invisible group
```xml
<mxCell id="grp1" value="" style="group;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="300" height="180" as="geometry"/>
</mxCell>
<mxCell id="gc1" value="Node A" style="rounded=1;whiteSpace=wrap;" vertex="1" parent="grp1">
  <mxGeometry x="10" y="20" width="120" height="60" as="geometry"/>
</mxCell>
```

**Key rule:** Always include `pointerEvents=0;` on containers that should not capture connection rewiring. Swimlane handles this internally — omit it only there.

---

## Layers

Use layers when a diagram has distinct conceptual groups viewers may want to toggle independently (e.g., "Happy Path" vs. "Error Paths", "Current State" vs. "Future State"):

```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="L2" value="Error Paths" parent="0"/>
    <mxCell id="10" value="Submit Order" style="rounded=1;" vertex="1" parent="1">
      <mxGeometry x="100" y="100" width="140" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="20" value="Payment Failed" style="rounded=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="L2">
      <mxGeometry x="300" y="200" width="140" height="60" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>
```

Add `visible="0"` to a layer cell to hide it by default.

---

## Tags

Tags let viewers filter elements by cross-cutting category (e.g., "happy-path", "error", "optional"). A single element can carry multiple tags. Requires wrapping `mxCell` in `<object>`:

```xml
<object id="n10" label="Verify Payment" tags="happy-path critical">
  <mxCell style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
    <mxGeometry x="100" y="100" width="140" height="60" as="geometry"/>
  </mxCell>
</object>
```

The `label` attribute on `<object>` replaces `value` on `mxCell`. Tags are space-separated.

---

## Metadata and Placeholders

Use metadata when nodes represent real entities (people, systems, statuses) and you want structured data visible in the label or accessible in the sidebar:

```xml
<object id="n11" label="&lt;b&gt;%name%&lt;/b&gt;&lt;br&gt;Owner: %owner%&lt;br&gt;Status: %status%"
        placeholders="1" name="Risk Review" owner="Legal" status="Pending">
  <mxCell style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
    <mxGeometry x="100" y="100" width="160" height="80" as="geometry"/>
  </mxCell>
</object>
```

Built-in placeholders (no custom attrs needed): `%id%`, `%width%`, `%height%`, `%date%`, `%time%`, `%timestamp%`, `%page%`, `%pagenumber%`, `%pagecount%`, `%filename%`

---

## Dark Mode

`adaptiveColors="auto"` on `<mxGraphModel>` enables automatic dark mode adaptation:
- Colors left as `"default"` render black in light mode, white in dark mode.
- Explicit hex colors are auto-inverted (RGB inverse at 93%, hue rotated 180°).
- Use `light-dark(#lightColor,#darkColor)` only when the auto-inversion is wrong: `fontColor=light-dark(#1a1a1a,#ffffff)`

---

## Shape Library Decision

**Skip shape search** — use basic geometry for:
- Flowcharts, process maps, decision trees
- UML (class, sequence, state, activity)
- ERD, org charts, mind maps, timelines, Venn diagrams, swimlane BPMN
- Any diagram using rectangles, diamonds, circles, cylinders, arrows

**Use domain-specific shapes** (note which library; user must enable it in draw.io) for:
- Cloud architecture: AWS (`shape=mxgraph.aws4.*`), Azure, GCP
- Network topology: Cisco (`shape=mxgraph.cisco.*`), rack equipment
- P&ID: valves, instruments, vessels (`shape=mxgraph.pid2valves.*`)
- Electrical / circuit diagrams, Kubernetes, BPMN with specific task type icons

---

## Common Diagram Patterns

### Flowchart
- Direction: top-to-bottom
- Start oval → rounded rect steps → diamond decisions (labeled "Yes"/"No" edges) → end oval
- Space 100–150px vertically between nodes
- Route "No" branches to the right, "Yes" continues downward

### Swimlane / Cross-functional
- One `swimlane` container per actor/department, children use `parent="swimlaneId"`
- Horizontal swimlanes: diagram reads top-to-bottom within each lane
- Connect nodes across lanes with `orthogonalEdgeStyle` edges
- Keep lane widths uniform; adjust height per lane to fit content

### State Machine
- States as rounded rectangles; start state as small filled circle; end state as double circle
- Self-loops: set `exitX=1;exitY=0;entryX=1;entryY=1` and add a waypoint above the node
- Label every edge with the transition trigger and/or guard condition

### Sequence Diagram
- One vertical swimlane per actor (lifeline); width ~120px, height spans full diagram
- Messages flow left-to-right as edges between swimlanes, labeled with method/event name
- Activation boxes: narrow rectangles inside a lifeline swimlane

### ERD
- One rectangle per entity, labeled with entity name
- Attributes listed below the entity name (use line breaks in `value` with `html=1`)
- Edge labels for cardinality: "1", "*", "0..1", "1..*"
- Position entities to minimize edge crossings

### Org Chart
- Root node at top center; children spread horizontally below
- Use `orthogonalEdgeStyle` with `exitX=0.5;exitY=1` → `entryX=0.5;entryY=0`
- Keep node sizes uniform; use `fillColor` to distinguish levels or departments

### Decision Tree
- Root diamond at top; branches labeled with conditions
- Leaf nodes (outcomes) as rounded rectangles with distinct fill
- Prefer left/right branching at each diamond rather than multiple downward branches

### Mind Map
- Central topic as a prominent ellipse or rounded rect
- Branches radiate outward; use `elbowEdgeStyle` for organic feel
- Group subtopics by color; keep labels short

### Timeline
- Horizontal axis as a plain line or thin rectangle
- Milestone nodes positioned at proportional x-coordinates along the axis
- Vertical lines connecting milestones to labels above/below the axis
- Phase bands as wide, low-opacity background rectangles behind the axis

---

## Readability Guidelines

These are not optional aesthetics — unreadable diagrams require rework.

- **Consistent node sizes within a type.** All process boxes the same width; all decision diamonds the same size.
- **Align to a 10px grid.** All `x`, `y`, `width`, `height` values must be multiples of 10.
- **Label length.** Node labels ≤4 words where possible. If more context is needed, use metadata placeholders or a separate annotation layer.
- **Color with purpose.** Use fill color to encode meaning (e.g., green = happy path, red = error, grey = external). Never use color purely decoratively.
- **Suggested palette (neutral defaults):**
  - Process / default: `fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333`
  - Highlight / success: `fillColor=#d5e8d4;strokeColor=#82b366`
  - Warning / decision: `fillColor=#fff2cc;strokeColor=#d6b656`
  - Error / failure: `fillColor=#f8cecc;strokeColor=#b85450`
  - External / out-of-scope: `fillColor=#dae8fc;strokeColor=#6c8ebf`
- **Edge density.** If more than 3 edges leave or enter a single node, reconsider whether that node should be decomposed into sub-steps or a sub-diagram.
- **Direction consistency.** Flow in one dominant direction. Mixed directions (e.g., some edges going right, some left) within the same layer signal a layout problem.

---

## XML Well-Formedness Rules (CRITICAL)

1. **NO XML comments** (`<!-- -->`) anywhere in the output — they are forbidden.
2. Escape special characters in attribute values: `&amp;` `&lt;` `&gt;` `&quot;`
3. Every `mxCell` must have a unique `id`.
4. Every edge `mxCell` must use expanded form with a `<mxGeometry relative="1" as="geometry"/>` child — never self-close an edge.
5. Align all node coordinates to multiples of 10.
6. Do not use HTML markup on edge labels to reduce font size — they are already 11px by default.

---

## Output Format

Deliver the XML in a fenced code block:

```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    ...
  </root>
</mxGraphModel>
```

Follow with:
1. A 2–3 sentence plain-English summary of what was generated and why key structural choices were made.
2. Any caveats: shape libraries to enable, nodes the user should rename, or layout adjustments expected for very large graphs.
3. An offer to refine: "Let me know if you'd like to adjust the layout, add more nodes, or switch to a different diagram type."
