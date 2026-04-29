# Sync Remotes Skill — Design Spec

## Overview

A workflow skill that syncs merged GitHub PRs to GitLab and cleans up feature branches. Lives in `.claude/skills/` only — not in `core/` or `presets/` since it's specific to this repo's dual-remote topology.

### Topology

- `origin` (GitHub): `main` branch (personal), `gitlab-workflows` branch (work)
- `gitlab` (GitLab): `main` branch (mirrors `origin/gitlab-workflows`)
- Feature branches: based on whichever environment they target

### Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Skill name | `sync-remotes` | Descriptive, not ambiguous |
| Location | `.claude/skills/` only | Repo-specific workflow, not a universal skill |
| GitLab MR | Create only, don't auto-merge | User stays in control on GitLab side |
| Branch cleanup | Included | One less manual step after merge |
| References | None needed | Simple procedural skill, fits in <100 lines |

---

## File Structure

```
.claude/skills/sync-remotes/
└── SKILL.md
```

Single file, no references directory.

---

## SKILL.md Design (~60 lines)

### Frontmatter

```yaml
---
name: sync-remotes
description: >
  Syncs merged GitHub PRs to GitLab and cleans up feature branches.
  Use when the user says "sync remotes", "sync to gitlab", "push to gitlab",
  or after merging a PR on GitHub that targets the gitlab-workflows branch.
---
```

### Sections

| Section | Purpose | Est. Lines |
|---------|---------|------------|
| Frontmatter | Name and description with triggers | 7 |
| Prerequisites | gh/glab authenticated, clean working tree | 5 |
| Workflow | 4-step process: detect, sync, MR, cleanup | 30 |
| Branch Mapping | Which base branch triggers GitLab sync | 5 |
| Error Handling | PR not merged, auth failures, branch not found | 10 |
| **Total** | | **~55** |

### Workflow Detail

**Step 0 — Prerequisites:**
- Verify working tree is clean (`git status --porcelain`) — if dirty, stop: "Commit or stash changes first."
- Verify `gh auth status` and `glab auth status` succeed

**Step 1 — Detect context:**
- Identify current branch
- If already on a base branch (`gitlab-workflows` or `main`): skip Step 4 (cleanup), run Steps 2-3 only. Use `gh pr list --state merged --base <branch> --limit 1 --json title,body` to get the most recent merged PR info.
- If on a feature branch: gather PR info via `gh pr view --json baseRefName,state,title,body`. Verify PR state is `MERGED` — if not, stop and inform user.

**Step 2 — Sync to GitLab:**
- `git checkout <base-branch>` (e.g. `gitlab-workflows`)
- `git pull origin <base-branch>` (pull merged changes from GitHub)
- `git push gitlab <base-branch>` (push to GitLab remote)

**Step 3 — Create MR on GitLab (conditional):**
- Only if base branch is `gitlab-workflows` (work environment)
- Skip if base branch is `main` (personal projects — no GitLab sync needed)
- Use PR title and body from Step 1 (already fetched)
- `glab mr create --source-branch gitlab-workflows --target-branch main --title <pr-title> --description <pr-body>`
- If an MR already exists for `gitlab-workflows` → `main`, report the existing URL instead of creating a duplicate

**Step 4 — Cleanup:**
- `git branch -D <feature-branch>` (force delete local — `-D` needed because GitHub squash merges don't preserve branch commit history, so `-d` would fail)
- `git push origin --delete <feature-branch>` (delete on GitHub remote)
- Skip GitLab remote deletion (feature branches are never pushed there)
- If branch already deleted on remote (GitHub auto-delete), skip gracefully

### Branch Mapping

| PR Base Branch | GitLab Sync | MR Target | Cleanup |
|---------------|-------------|-----------|---------|
| `gitlab-workflows` | Yes — push to `gitlab` remote | `main` | Local + origin |
| `main` | No — personal project | N/A | Local + origin |

### Error Handling

| Error | Response |
|-------|----------|
| PR not merged | Stop: "PR is not merged yet. Merge the PR on GitHub first." |
| No PR found for branch | Stop: "No PR found for branch `<name>`. Create and merge a PR first." |
| `gh` not authenticated | Stop: "GitHub CLI not authenticated. Run `gh auth login`." |
| `glab` not authenticated | Stop: "GitLab CLI not authenticated. Run `glab auth login`." |
| Feature branch already deleted on remote | Skip deletion silently, continue |
| GitLab MR already exists | Report existing MR URL, skip creation |
| Dirty working tree | Stop: "Commit or stash your changes before syncing." |
| GitLab push fails (non-fast-forward) | Stop: "GitLab remote has diverged. Pull from GitLab and resolve manually." |

---

## Integration

### CLAUDE-base.md

Not added — this skill lives in `.claude/skills/` only and is auto-detected by Claude. No `core/CLAUDE-base.md` entry needed since it's not a core skill.

### Future

If the dual-remote pattern becomes common across repos, this could be promoted to `core/skills/` or a preset. For now it stays repo-local.
