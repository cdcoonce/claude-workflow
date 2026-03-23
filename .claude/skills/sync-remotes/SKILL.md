---
name: sync-remotes
description: >
  Syncs merged GitHub PRs to GitLab and cleans up feature branches.
  Use when the user says "sync remotes", "sync to gitlab", "push to gitlab",
  or after merging a PR on GitHub that targets the gitlab branch.
---

# Sync Remotes

Syncs the `origin` (GitHub) → `gitlab` (GitLab) remote after a PR merge, creates an MR on GitLab, and cleans up the feature branch.

## Prerequisites

Before starting, verify:
- Working tree is clean (`git status --porcelain`) — if dirty, stop: "Commit or stash changes first."
- `gh auth status` succeeds — if not: "Run `gh auth login`."
- `glab auth status` succeeds — if not: "Run `glab auth login`."

## Workflow

### Step 1 — Detect context

Identify the current branch.

**If on a feature branch:**
- Run `gh pr view --json baseRefName,state,title,body`
- If no PR found → stop: "No PR found for this branch. Create and merge a PR first."
- If PR state is not `MERGED` → stop: "PR is not merged yet. Merge the PR on GitHub first."
- Save `baseRefName` (base branch), `title`, and `body` for later steps.

**If already on a base branch (`gitlab` or `main`):**
- Skip Step 4 (cleanup). Run Steps 2-3 only.
- Run `gh pr list --state merged --base <branch> --limit 1 --json title,body` for MR description.

### Step 2 — Sync to GitLab

```
git checkout <base-branch>          # e.g. gitlab
git pull origin <base-branch>       # pull merged changes from GitHub
git push gitlab <base-branch>       # push to GitLab remote
```

If `git push` fails with non-fast-forward → stop: "GitLab remote has diverged. Pull from GitLab and resolve manually."

### Step 3 — Create MR on GitLab (conditional)

| Base Branch | Action |
|-------------|--------|
| `gitlab` | Create MR: `glab mr create --source-branch gitlab --target-branch main --title <title> --description <body>` |
| `main` | Skip — personal project, no GitLab sync needed. Report: "Synced to GitLab. No MR needed (personal branch)." |

Before creating, check if an MR already exists for `gitlab` → `main`. If so, report the existing URL and skip creation.

### Step 4 — Cleanup (skip if invoked from base branch)

```
git branch -D <feature-branch>                # force-delete local (squash merges need -D)
git push origin --delete <feature-branch>      # delete on GitHub remote
```

- Skip GitLab remote deletion — feature branches are never pushed there.
- If branch already deleted on remote (GitHub auto-delete), skip gracefully.

## Error Summary

| Error | Response |
|-------|----------|
| Dirty working tree | Stop: "Commit or stash your changes before syncing." |
| `gh` not authenticated | Stop: "Run `gh auth login`." |
| `glab` not authenticated | Stop: "Run `glab auth login`." |
| No PR found for branch | Stop: "Create and merge a PR on GitHub first." |
| PR not merged | Stop: "Merge the PR on GitHub first." |
| GitLab push non-fast-forward | Stop: "GitLab remote has diverged. Resolve manually." |
| Feature branch already deleted | Skip deletion, continue. |
| GitLab MR already exists | Report existing MR URL, skip creation. |
