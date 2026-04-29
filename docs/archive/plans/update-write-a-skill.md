# Plan: Update Write-a-Skill Skill

> Source PRD: https://github.com/cdcoonce/claude-workflow/issues/13

## Architectural decisions

Durable decisions that apply across all phases:

- **File layout**: `core/skills/write-a-skill/SKILL.md` (main, under 100 lines) + `core/skills/write-a-skill/references/` directory with `skill-grill-domains.md`, `blueprint-template.md`, and `quality-criteria.md`
- **Reference linking**: SKILL.md uses relative markdown links to reference files (e.g., `[domains](references/skill-grill-domains.md)`)
- **Skill invocation**: The skill instructs the agent to invoke `grill-me` via the Skill tool — same delegation pattern used by `dev-cycle` and `write-a-prd`
- **AskUserQuestion usage**: All structured questions use the `AskUserQuestion` tool with options and recommendations. First option is always `(Recommended)`. Batch related questions (up to 4 per call).
- **Fallback (AskUserQuestion)**: When `AskUserQuestion` is unavailable, fall back to text-based questions — same pattern as `grill-me`
- **Fallback (grill-me)**: When `grill-me` is not installed, run an inline mini-grill using `AskUserQuestion` directly with the skill-tailored domains from `references/skill-grill-domains.md`
- **Pipeline**: Linear 4-phase, no looping: Gather → Grill → Plan → Implement (with 4b Review)

---

## Phase 1: Reference Files — Grill Domains & Blueprint Template

**User stories**: 5, 6, 10

### What to build

Create the two reference files that the main SKILL.md will link to. These are standalone documents that define:

1. **`references/skill-grill-domains.md`** — A skill-tailored subset of grill-me interrogation domains. Defines 4 domains relevant to skill design: Intent & Success Criteria, Scope & Boundaries, Design Decisions & Trade-offs, Edge Cases & Error Handling. Each domain includes sample questions, "explore before asking" hints, and batching guidance — mirroring the format in `grill-me/references/interrogation-domains.md` but focused on skill authoring concerns (not data flow, deployment, etc.).

2. **`references/blueprint-template.md`** — The template for the structured skill blueprint that Phase 3 (Plan) produces. Defines the sections: proposed file tree, SKILL.md section outline with headings, list of reference files with purpose, key instructions per section, and proposed description text. This template is presented in conversation context, not written to disk.

3. **`references/quality-criteria.md`** — Description Requirements (max 1024 chars, third person, trigger phrases, good/bad examples) and the post-implementation review checklist (both auto-verify criteria and subjective items). Extracted from the current SKILL.md to free line budget for the pipeline instructions.

### Acceptance criteria

- [ ] `references/skill-grill-domains.md` exists with 4 domains, each containing: domain name, purpose, sample questions, explore-before-asking hints, batching guidance
- [ ] `references/blueprint-template.md` exists with sections for: file tree, SKILL.md outline, reference file list, key instructions, description text
- [ ] `references/quality-criteria.md` exists with: description format rules, good/bad examples, auto-verify criteria, subjective review checklist
- [ ] All files follow the format conventions of existing reference files in the repo (e.g., `grill-me/references/interrogation-domains.md`)
- [ ] No reference file exceeds 150 lines

---

## Phase 2: Core Pipeline — Rewrite SKILL.md

**User stories**: 1, 2, 3, 4, 9, 11, 12

### What to build

Replace the current flat 3-step SKILL.md with a 4-phase pipeline. The new SKILL.md defines:

- **Frontmatter**: Updated `name` and `description` (preserved trigger phrases, under 1024 chars)
- **Phase 1: Gather** — Instructions to use `AskUserQuestion` with domain-batched questions across 4 domains (Purpose, Use Cases, Structure, Tooling). Each domain gets 1 AskUserQuestion call with 2-4 options and a recommendation.
- **Phase 2: Grill** — Instructions to invoke the `grill-me` skill, passing the gathered requirements and pointing to the skill-tailored domains defined in `references/skill-grill-domains.md`. The grill focuses on the 4 skill-relevant domains only. Includes a fallback: if `grill-me` is unavailable, run an inline mini-grill using `AskUserQuestion` directly with the same domains.
- **Phase 3: Plan** — Instructions to produce a structured skill blueprint using the template in `references/blueprint-template.md`. The blueprint is presented in conversation context for user approval before proceeding.
- **Phase 4: Implement** — Instructions to create all skill files following the approved blueprint. Fully automated, no user writing.
- **Skill Structure section** — Preserved from current version (file tree showing SKILL.md, references, scripts)
- **Quality criteria** — Referenced from `references/quality-criteria.md` (Description Requirements + review checklist moved there to stay under 100-line budget)

### Acceptance criteria

- [ ] SKILL.md is under 100 lines
- [ ] Description in frontmatter is under 1024 chars and includes "Use when" trigger phrases
- [ ] 4 pipeline phases are clearly documented with step-by-step instructions
- [ ] Phase 1 (Gather) specifies 4 AskUserQuestion domains with example question structures
- [ ] Phase 2 (Grill) references `skill-grill-domains.md`, instructs Skill tool invocation, and includes inline mini-grill fallback
- [ ] Phase 3 (Plan) references `blueprint-template.md` and specifies conversation-context output
- [ ] Phase 4 (Implement) specifies fully automated file creation
- [ ] Skill Structure section is preserved; Description Requirements moved to `quality-criteria.md` and referenced
- [ ] Links to reference files use correct relative paths

---

## Phase 3: Post-Implementation Review & AskUserQuestion Fallback

**User stories**: 7, 8

### What to build

Add two capabilities to the SKILL.md:

1. **Phase 4b: Review** — After implementation, the agent runs a post-implementation review using criteria from `references/quality-criteria.md`:
   - Auto-verify measurable criteria: SKILL.md under 100 lines, description under 1024 chars, description includes "Use when" trigger phrase, references are one level deep
   - Present subjective checklist items to user via AskUserQuestion: covers use cases? consistent terminology? concrete examples? no time-sensitive info?
   - If auto-verification fails, fix and re-verify before presenting subjective items
   - If user rejects on subjective items, iterate on the specific concern before proceeding

2. **AskUserQuestion fallback** — Add a fallback section (mirroring `grill-me`'s approach) for environments where `AskUserQuestion` is unavailable. In fallback mode, questions are presented as text with "Recommended" labels and lettered alternatives.

### Acceptance criteria

- [ ] Phase 4b review logic is documented in SKILL.md, referencing `quality-criteria.md` for criteria details
- [ ] Auto-verify criteria match PRD: line count, description length, trigger phrases
- [ ] Subjective review uses AskUserQuestion with a confirmation-style question
- [ ] Blueprint rejection is handled: user can request changes before proceeding to implement
- [ ] Fallback section exists with text-based question format matching `grill-me`'s pattern
- [ ] SKILL.md remains under 100 lines (Description Requirements now in `quality-criteria.md`)

---

## Phase 4: Build & Smoke Test Verification

**User stories**: Testing decisions from PRD

### What to build

Verify the updated skill works correctly within the build system:

1. Extend `scripts/smoke_test.py` to validate intra-skill reference links: scan each SKILL.md in the build output for markdown links to files within the skill directory and verify those files exist
2. Run `uv run python scripts/smoke_test.py` for any presets that include `write-a-skill` to ensure the new reference files are picked up
3. Run `uv run pytest` to ensure no existing tests break
4. Verify the build output (`uv run python scripts/build_preset.py`) includes the new `references/` directory in the output

### Acceptance criteria — Phase 4

- [ ] `smoke_test.py` includes intra-skill reference link validation (new check)
- [ ] Smoke tests pass for all presets containing `write-a-skill`
- [ ] `pytest` suite passes with no regressions
- [ ] Build output for relevant presets includes `write-a-skill/SKILL.md` and `write-a-skill/references/` with all three reference files
