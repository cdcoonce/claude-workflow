# Plan: Grill-Me AskUserQuestion Integration

> Source PRD: [#2](https://github.com/cdcoonce/claude-workflow/issues/2)

## Architectural decisions

Durable decisions that apply across all phases:

- **Tool usage**: All interrogation questions use `AskUserQuestion`. If AskUserQuestion is unavailable in the runtime, fall back to the text question format (see fallback template in SKILL.md)
- **Option filtering**: When a question has more than 4 valid options, present the 3 most relevant based on codebase context. Users select "Other" for anything not listed
- **Decisions log storage**: Maintained in Claude's conversation context only (no file I/O). Presented as a structured table at session end
- **Recommendation convention**: First option in every question carries `(Recommended)` suffix, matching both the skill's "lead with your recommendation" directive and AskUserQuestion's built-in convention
- **Tool constraints**: 2-4 options per question, 1-4 questions per invocation, optional `preview` field, optional `multiSelect: true`
- **Files modified**: `core/skills/grill-me/SKILL.md` (primary), `core/skills/grill-me/references/interrogation-domains.md` (domain-specific question guidance)
- **"Other" for free-form**: AskUserQuestion always includes an automatic "Other" option — the skill relies on this for open-ended questions rather than falling back to text output

---

## Phase 1: Core AskUserQuestion integration

**User stories**: 1, 2, 3, 10

### What to build

Rewrite the grill-me SKILL.md to replace plain-text question output with `AskUserQuestion` tool calls. Update:

- **Prime Directives**: Change "One question at a time" to "Use AskUserQuestion for every question." Change "Always lead with your recommendation" to reference the first-option-with-Recommended convention.
- **Question Format**: Replace the current markdown template with an AskUserQuestion JSON structure showing `question`, `header`, `options` (with `label`, `description`), and `multiSelect`.
- **Interrogation Process**: Update step 3b to describe invoking AskUserQuestion instead of "state the question, present alternatives, wait for response."
- **Rules for Asking Questions**: Update to reference AskUserQuestion constraints (2-4 options, header max 12 chars). Keep "explore before asking" and "accept the answer" rules.

### Acceptance criteria

- [ ] SKILL.md instructs Claude to use AskUserQuestion for every interrogation question
- [ ] Question format template shows the AskUserQuestion JSON structure with all required fields
- [ ] First option in the template carries "(Recommended)" suffix
- [ ] "Explore before asking" directive is preserved
- [ ] Free-form questions are handled via the built-in "Other" option
- [ ] A minimal text-based fallback template is included for environments without AskUserQuestion
- [ ] Option filtering guidance: present 3 best options when >4 valid choices exist

---

## Phase 2: Batching and multi-select

**User stories**: 4, 7, 8

### What to build

Update the batching and multi-select behavior:

- **Prime Directives**: Replace "one question at a time" with "batch up to 4 related questions within the same interrogation domain; separate cross-domain questions into distinct invocations."
- **Interrogation Process**: Update step 3 to describe grouping related decision points within a domain into a single AskUserQuestion call (max 4 questions per call).
- **Multi-select guidance**: Add instruction for when to use `multiSelect: true` — when options are not mutually exclusive (e.g., "which testing approaches?", "which domains need coverage?").
- **Header guidance**: Add instruction that every question must have a short `header` (max 12 chars) indicating the topic.
- **Interrogation domains reference**: Update each domain in `interrogation-domains.md` with guidance on which questions within that domain are natural candidates for batching and which warrant multi-select.

### Acceptance criteria

- [ ] SKILL.md instructs batching up to 4 related questions per AskUserQuestion invocation within a domain
- [ ] Cross-domain questions are explicitly separated into distinct invocations
- [ ] Multi-select usage guidance is documented with examples
- [ ] Header field guidance with max 12 char constraint is documented
- [ ] `interrogation-domains.md` has per-domain batching hints

---

## Phase 3: Previews and structured decisions log

**User stories**: 5, 6, 9

### What to build

Add preview support and rewrite the decisions log format:

- **Preview guidance**: Add a section explaining when to use the `preview` field — when comparing concrete artifacts like code snippets, architecture diagrams, schema shapes, or configuration options. Include an example showing preview content in the question format template.
- **Structured decisions log**: Replace the current "running decisions log" concept with a structured format that records `{domain, header/topic, selected_option_label, custom_text_if_other}` for each resolved question. Update the "track everything" directive and the "after all domains" summary step.
- **Interrogation domains reference**: Add notes per domain on which question types benefit from previews (e.g., Domain 3 "Design Decisions" is a natural fit for comparing code patterns).

### Acceptance criteria

- [ ] SKILL.md documents when and how to use the `preview` field with an example
- [ ] Decisions log format is structured (domain, topic, selected option, custom text)
- [ ] The "after all domains" summary step presents structured decisions, not prose
- [ ] `interrogation-domains.md` has per-domain preview guidance where relevant
- [ ] Preview is explicitly noted as single-select only (not compatible with multiSelect)

---

## Manual Test Scenario

Invoke `/grill-me` against an existing plan file (e.g., `docs/plans/grill-me-askuserquestion.md`). Verify:

1. All questions arrive via AskUserQuestion (not plain text)
2. First option in each question has "(Recommended)" suffix
3. Related questions within the same domain are batched (up to 4)
4. Cross-domain questions are separate invocations
5. At least one question uses preview for comparing concrete options
6. Final summary presents a structured decisions table, not prose
7. Multi-select is used for at least one non-mutually-exclusive question
