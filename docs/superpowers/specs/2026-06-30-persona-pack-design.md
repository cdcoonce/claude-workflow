# Persona Pack — Output-Style Personalities for Claude Code

**Date:** 2026-06-30 (revised 2026-07-01)
**Status:** Shipped — pivoted from one output-styles plugin to five hook-plugins
**Home:** `claude-workflow` (distributed as five `persona-*` marketplace plugins)

## Update 2026-07-01 — pivot to hook-plugins (uv)

The original design shipped one `personas` plugin whose `output-styles/*.md` files
Claude Code would auto-discover. That works for the **terminal** `/output-style`
picker but **not for the desktop/web app** — the app surfaces output styles only as
**plugins that ship a hook**, and doesn't read a plugin's `output-styles/` dir into
its style picker. (Anthropic's own `explanatory-output-style` / `learning-output-style`
are exactly this: a plugin whose `SessionStart` hook prints the style text as
`additionalContext`. Their description even says "mimics the *deprecated* Explanatory
output style.")

**Revised shape:** one plugin per persona — `persona-terse-staff-eng`,
`persona-staff-eng-deep`, `persona-pair-programmer`, `persona-thinking-partner`,
`persona-ship-it` — each a toggle in the app (enable one, disable the rest, exactly
like switching explanatory vs learning). Each plugin ships:

- its `output-styles/<slug>.md` (single source of truth; still serves the CLI picker), and
- a shared `SessionStart` hook, `core/hooks/inject_persona.py`, invoked via **`uv run`**
  (cross-platform Python + PEP 723 inline metadata — deliberately *not* Anthropic's
  bash `session-start.sh`, which is macOS/Linux-only and off-convention here). The hook
  reads the plugin's one `output-styles/*.md`, strips frontmatter, and emits the body as
  `additionalContext` — **purely additive**, so the engineering base is preserved for free.

**Build changes:** `build_preset.py` gains (1) `base_settings: false` so a style-only
plugin skips the shared `protect-files` PreToolUse guard (otherwise every persona would
impose file-edit guarding), and (2) `agent-matching.md` is copied only when the plugin
actually ships agents. The old `personas` preset + `dist/personas` are retired.

## Goal

Let the user pick a **personality** for a Claude Code session — most importantly one
that is **much less verbose** — toggle it on/off, and have the choice stick from one
session to the next. Ship a small, curated **distribution** of these personalities so
the team gets them by installing one plugin.

## Mechanism — native output styles (no custom machinery)

Each persona is a Claude Code **output style**: a markdown file with `name` +
`description` frontmatter whose body is appended to the system prompt every turn.

This gives us everything the request asked for, natively:

- **Trigger / toggle:** `/output-style <persona>` switches; `/output-style default` turns off.
- **Persist for the session:** output styles are re-injected every turn (top of context),
  so they don't decay the way a one-shot skill invocation would.
- **Persist across sessions:** the active style is saved in project settings
  (`.claude/settings.local.json` → `outputStyle`), so a new session boots with it until changed.

We explicitly rejected two earlier directions:

- **A custom skill that writes personas into an instructions file** — hacky; only needed to
  *fake* output styles on agents that lack them.
- **Agent-agnostic (Codex/Gemini/etc.)** — dropped. Portability forced the hack above.
  Decision: **make it excellent in Claude Code**, not portable-but-compromised.

## Layering — keep the engineering base

Every persona **keeps Claude Code's built-in software-engineering instructions** and layers
voice + a default verbosity on top. None of them replace the base. (Output styles can drop
the base; we choose not to — this is eng work.)

## Roster (5)

| Persona | Voice | Default verbosity |
|---|---|---|
| **`terse-staff-eng`** ⭐ | Senior staff engineer. Answer-first, no preamble, no "Great question!", no unsolicited summaries. Assumes expert user. | Terse — the headline "much less verbose" |
| **`staff-eng-deep`** | Same expert voice, but thorough — reasoning shown, alternatives weighed, edge cases named. The verbose end of the same dial. | Deep |
| **`pair-programmer`** | Collaborative pair-programmer. Narrates just enough to keep the user in the loop; casual; brief think-aloud. | Medium |
| **`thinking-partner`** | Socratic. Asks sharp questions, reflects reasoning back, helps the user *decide* rather than deciding for them. | Medium, question-heavy |
| **`ship-it`** | Momentum-first. Blunt, bias-to-action, picks a default and moves, risks flagged in one line. | Terse |

`terse-staff-eng` is the non-negotiable core; the rest are flavor. `terse-staff-eng` +
`staff-eng-deep` together form a genuine terse↔deep toggle on one personality.

Deliberately **excluded:** explainer / mentor — Claude Code already ships `explanatory` and
`learning` styles, so that lane is covered natively.

## Verbosity model

Single-select is a constraint of output styles (one active at a time, no composition). So
verbosity is handled as: **each persona ships a sensible default level**, and the user
**nudges inline** ("shorter", "go deep") anytime. The `terse`/`deep` staff-eng pair gives a
persistent dial for the flagship voice without a combinatorial matrix.

## Distribution

Ship as a standalone **`personas`** plugin in the `claude-workflow` marketplace:

```
personas/
├── .claude-plugin/plugin.json      # { "name": "personas", ... }
└── output-styles/
    ├── terse-staff-eng.md
    ├── staff-eng-deep.md
    ├── pair-programmer.md
    ├── thinking-partner.md
    └── ship-it.md
```

`output-styles/` is auto-discovered by convention (no plugin.json field needed), matching
Anthropic's own `explanatory-output-style` plugin. Installable by URL, works in any project,
independent of the domain presets.

For immediate personal use, the same files can also live in `~/.claude/output-styles/`.

## Build/implementation checklist

1. Author the 5 output-style `.md` files (frontmatter + body).
2. Drop copies in `~/.claude/output-styles/` for immediate use this session.
3. Wire a `personas` preset into the build (`presets/`, `manifest.json`, `marketplace.json`,
   `build_preset.py`/`build_marketplace.py`) so it emits `dist/personas`. — needs a read of
   the build scripts first.
4. Smoke-test: `/output-style terse-staff-eng`, confirm it activates and persists across a restart.

## Non-goals

- No agent portability (Claude Code only).
- No custom skill, hook, or file-writing glue — native output styles only.
- No mentor/explainer persona (covered by built-in styles).
