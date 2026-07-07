# claude-workflow cross-agent preset installer — design

_Date: 2026-06-09_

## Problem

claude-workflow is a complete Claude Code plugin (skills + agents + commands + hooks + methodology), preset-configurable, distributed via the plugin marketplace ("paste the repo URL into Claude, pick a preset"). That install path is **Claude-Code-only**, requires the coworker to know the marketplace URL and presets, and the `dist/` artifacts are gitignored (manual copy needs a build first).

The goal: make claude-workflow **frictionless to install for teammates** and usable across **multiple coding agents** (Claude Code, Snowflake Cortex Code, and others later), so the same skill system can back a coworker's repo, the second-brain vault, and afk. Modeled on graphify's CLI-installer distribution (`uv tool install` + a single `install` command that registers the skills into the detected agent).

## Decisions (from brainstorming, 2026-06-09)

- **First piece:** the CLI installer. (The companion "vault + afk consume claude-workflow presets" refactor is a separate follow-on spec.)
- **MVP audience:** work coworkers on the **governed GitLab claude-workflow** — private distribution, GitLab auth. (Not public PyPI.)
- **Install scope:** **project-scoped default** (into the repo's tree, committed, so the whole team inherits it on clone) with a `--user` opt-in (into the per-developer home).
- **Mechanism:** the installer **places the bundle itself** (it does not wrap any agent's native install command — that would be Claude-only and interactive).
- **MVP agent adapters:** **Claude Code + Cortex Code.** Claude Code is the richest target (proves the full bundle); Cortex Code proves the cross-agent abstraction on a genuinely different platform.

## Architecture

Three units, each independently testable.

### 1. The canonical bundle (agent-agnostic content)

A preset is agent-agnostic content: skills (markdown), methodology docs, agent-role definitions, command definitions, and hook scripts. Presets are built **once** by the existing `build_preset.py` and **bundled inside the wheel** at package-build time, so `uv tool install git+https://gitlab…/claude-workflow` carries every preset with no runtime fetch.

- **Interface:** a `Bundle` is "a named preset's content on disk inside the installed package" — `name`, plus typed accessors for its skills / agents / commands / hooks / methodology.
- **Depends on:** the existing preset build output (`dist/<preset>/`), packaged into the wheel (hatchling `force-include` or a build hook that runs `build_preset.py`).

### 2. The agent-adapter seam (the cross-agent core)

A small, pluggable interface — the substrate-agnostic seam (same shape as afk's pluggable seams):

```
class AgentAdapter:
    name: str                                  # "claude-code" | "cortex-code"
    def detect(self, target: Path) -> bool     # is this agent present/configured here?
    def install(self, bundle: Bundle, target: Path, scope: Scope) -> InstallReport
    def uninstall(self, target: Path, preset: str) -> InstallReport
```

- **`InstallReport`** records what was installed AND **what was skipped and why** (capability gaps). Honest degradation — never a silent half-install.
- **`Scope`** = `project` (the repo tree) or `user` (the developer's home).
- **ClaudeCodeAdapter** (full fidelity): copies the preset into `<target>/.claude/plugins/<preset>/`; Claude Code auto-discovers plugins there, and the bundled `plugin.json` declares skills/agents/commands/hooks. No `settings.json` surgery. Idempotent (clean overwrite on re-install).
- **CortexCodeAdapter** (research-gated — see Open Items): installs the bundle into Cortex Code's local skill/context mechanism. Expected to be a **subset** — skills + methodology as agent context; hooks and sub-agent roles reported as _skipped_ in the `InstallReport` if Cortex Code has no equivalent.

Adapters are registered in a small registry; adding Cursor / Gemini / Codex later is a new adapter class + registry entry, no core change.

### 3. The CLI (orchestration)

- `claude-workflow install [--preset NAME] [--agent NAME] [--user] [--dry-run]`
  - Resolves the target (cwd repo for project scope; home for `--user`).
  - Resolves the agent: auto-detect via adapters' `detect()`; `--agent` forces one.
  - Resolves the preset: `--preset` or an interactive/error if ambiguous.
  - Calls the adapter's `install`; prints the `InstallReport` (installed + skipped-with-reason).
  - `--dry-run` prints the report without writing.
  - Idempotent: re-running re-installs cleanly.
- `claude-workflow list` — available presets + detected agents in the current directory.
- Uninstall is exposed via the adapter (`claude-workflow uninstall --preset NAME` is a thin CLI over `adapter.uninstall`).

## Data flow

`uv tool install git+https://gitlab…/claude-workflow` → package (with bundled presets) on PATH → `claude-workflow install --preset data-pipeline` → CLI resolves (target=cwd repo, agent=auto-detected Claude Code, preset=data-pipeline) → `ClaudeCodeAdapter.install(bundle, repo, project)` → copies `dist/data-pipeline/` → `repo/.claude/plugins/data-pipeline/` → prints `InstallReport`.

## Error handling

- Unknown preset / unknown agent / no agent detected → clear error listing valid options (fail loud).
- Target not writable / not a git repo (project scope) → clear error.
- A capability the agent can't support → **not** an error; recorded as a skip in the `InstallReport` with the reason.
- Re-install over an existing install → overwrite idempotently (or `--dry-run` to preview).

## Testing

- **Per-adapter** (real temp dirs, no network): install a fixture bundle, assert the agent-specific structure (Claude: `.claude/plugins/<preset>/` with `plugin.json`; Cortex: its structure), assert `uninstall` removes it cleanly, assert capability gaps appear in the `InstallReport`.
- **CLI:** `install` / `list` / `--dry-run` against temp dirs with a fake adapter (assert target/agent/preset resolution + report rendering, no real filesystem coupling).
- **Packaging:** a smoke test that the built wheel actually contains the preset artifacts (so `install` has something to place).

## Open items (flagged, non-blocking)

- **Cortex Code mechanism (research first).** Confirm Snowflake Cortex Code's local skill/extension/config mechanism before implementing `CortexCodeAdapter`. If it has no local-config hook, the adapter degrades to a documented **context-file install** (drop the skills/methodology as a context doc Cortex reads), or we substitute Cursor in the MVP set. The adapter _interface_ is unaffected either way.
- **Build-time preset bundling.** Decide the exact hatchling mechanism (run `build_preset.py` in a build hook vs `force-include` a committed `dist/`). Affects packaging only, not the runtime install logic.

## Non-goals (this spec)

- The "vault + afk consume claude-workflow presets" refactor (separate follow-on spec).
- Cursor / Gemini / Codex adapters (the seam supports them; not in the MVP build set).
- MCP server mode and git-hook auto-update (graphify has these; deferred — not part of "easy install" MVP).
- Public PyPI distribution (private/governed for now).
