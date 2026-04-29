# Security Review Skill — Design Spec

## Overview

A security code review skill adapted from [Sentry's security-review skill](https://github.com/getsentry/skills/tree/main/plugins/sentry-skills/skills/security-review), restructured to match this repo's skill conventions and scoped for analyst/data engineering workflows.

### Source

- **Base:** Sentry `security-review` skill (GitHub, getsentry/skills)
- **Reference content:** Derived from OWASP Cheat Sheet Series (CC BY-SA 4.0)
- **Approach:** Faithful adaptation — preserve Sentry's review methodology and reference content, reformat to match our conventions

### Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Trigger model | Explicit `/security-review` only | Standalone concern, separate from `daa-code-review` |
| Confidence threshold | HIGH = report, MEDIUM = "needs verification", LOW = suppress | Smaller team can verify MEDIUM findings quickly |
| Output | Markdown report to `docs/security-reviews/YYYY-MM-DD-<component>.md` | Audit trail, attachable to MRs |
| Language coverage | Python only | Primary language for analyst/data engineering work |
| Infrastructure coverage | Docker + GitLab CI | Containerized pipelines + GitLab-based CI/CD |
| Dropped content | `javascript.md`, nonexistent files (go, rust, java, k8s, terraform, cloud) | Not relevant to current workflows |

---

## File Structure

```
core/skills/security-review/
├── SKILL.md                          # <100 lines — review process, confidence, output format
└── references/
    ├── api-security.md               # REST, GraphQL, mass assignment
    ├── authentication.md             # Sessions, credentials, password storage
    ├── authorization.md              # IDOR, privilege escalation
    ├── business-logic.md             # Race conditions, workflow bypass
    ├── cryptography.md               # Algorithms, key management, randomness
    ├── csrf.md                       # Cross-site request forgery
    ├── data-protection.md            # Secrets exposure, PII, logging
    ├── deserialization.md            # Pickle, YAML, Java deserialization
    ├── docker.md                     # Container security
    ├── error-handling.md             # Fail-open, information disclosure
    ├── file-security.md              # Path traversal, uploads, XXE
    ├── gitlab-ci.md                  # NEW — GitLab CI/CD pipeline security
    ├── injection.md                  # SQL, NoSQL, OS command, template injection
    ├── logging.md                    # Audit failures, log injection
    ├── misconfiguration.md           # Headers, CORS, debug mode, defaults
    ├── modern-threats.md             # Prototype pollution, LLM injection, WebSocket
    ├── python.md                     # Django, Flask, FastAPI, SQLAlchemy patterns
    ├── report-template.md            # Output format template and file path convention
    ├── ssrf.md                       # Server-side request forgery
    ├── supply-chain.md               # Dependencies, build security
    └── xss.md                        # Reflected, stored, DOM-based XSS
```

21 reference files total: 17 Sentry core vulnerability references + python + docker + 1 new gitlab-ci + 1 new report-template.

---

## SKILL.md Design (~86 lines)

### Frontmatter

```yaml
---
name: security-review
description: >
  Security code review for vulnerabilities with confidence-based reporting.
  Use when the user asks for "security review", "find vulnerabilities", "check
  for security issues", "audit security", "OWASP review", or to review code
  for injection, XSS, authentication, authorization, or cryptography issues.
---
```

### Sections

| Section | Purpose | Est. Lines |
|---------|---------|------------|
| Frontmatter | Name and description with "Use when" triggers | 7 |
| Attribution | OWASP CC BY-SA 4.0 notice | 3 |
| Quick Start | Invocation example + output path | 3 |
| Core Principle | Identify exploitable vulnerabilities, HIGH confidence reporting | 5 |
| Confidence Levels | HIGH = report, MEDIUM = "needs verification", LOW = suppress | 8 |
| Scope Rule | Research entire codebase for context, report only on provided code | 5 |
| Do Not Flag | Server-controlled values, framework-mitigated patterns, test files | 10 |
| Review Process | 4 steps: detect context, load references, research, verify exploitability | 15 |
| Context Detection Table | Maps code type → reference file(s) to load | 18 |
| Severity Classification | Critical/High/Medium/Low table | 8 |
| Output | File path convention + link to `references/report-template.md` | 4 |
| **Total** | | **~86** |

Note: The output format template is extracted into `references/report-template.md` to keep SKILL.md under 100 lines. The standalone reference index is removed — the context detection table already maps code types to reference files, and a separate index would duplicate that content (violating quality criteria).

### Key differences from Sentry SKILL.md

1. **Confidence threshold lowered** — MEDIUM findings included as "Needs verification" section in reports
2. **Output writes to file** — `docs/security-reviews/YYYY-MM-DD-<component>.md`
3. **Detection tables trimmed** — Python only (no JS/Go/Rust/Java rows), Docker + GitLab CI only (no K8s/Terraform/Cloud rows)
4. **Frontmatter simplified** — `name` and `description` only (no `allowed-tools`, `license`)
5. **Quick Patterns Reference removed from SKILL.md** — already covered in per-topic reference files, eliminates duplication
6. **Report template extracted** — moved to `references/report-template.md` to stay under line budget

---

## Reference Files — Adaptation Details

### Unchanged from Sentry (17 files)

All core vulnerability reference files are copied verbatim. No content edits. These are well-written, framework-agnostic OWASP-derived guides.

| File | Source Path |
|------|-------------|
| `api-security.md` | `references/api-security.md` |
| `authentication.md` | `references/authentication.md` |
| `authorization.md` | `references/authorization.md` |
| `business-logic.md` | `references/business-logic.md` |
| `cryptography.md` | `references/cryptography.md` |
| `csrf.md` | `references/csrf.md` |
| `data-protection.md` | `references/data-protection.md` |
| `deserialization.md` | `references/deserialization.md` |
| `error-handling.md` | `references/error-handling.md` |
| `file-security.md` | `references/file-security.md` |
| `injection.md` | `references/injection.md` |
| `logging.md` | `references/logging.md` |
| `misconfiguration.md` | `references/misconfiguration.md` |
| `modern-threats.md` | `references/modern-threats.md` |
| `ssrf.md` | `references/ssrf.md` |
| `supply-chain.md` | `references/supply-chain.md` |
| `xss.md` | `references/xss.md` |

### Relocated from Sentry (2 files)

Moved from subdirectories into flat `references/`. No content edits.

| File | Original Sentry Path |
|------|---------------------|
| `python.md` | `languages/python.md` |
| `docker.md` | `infrastructure/docker.md` |

### Dropped from Sentry

| File | Reason |
|------|--------|
| `javascript.md` | Not relevant to analyst/data engineering workflows |
| `LICENSE` | Not redistributing as separate package |

### New file: `gitlab-ci.md` (~120-150 lines)

Written from scratch. Covers GitLab CI/CD pipeline security patterns:

| Section | Content |
|---------|---------|
| Secrets in Pipelines | Hardcoded secrets in YAML, unmasked/unprotected variables, secrets echoed in logs |
| Variable Security | `CI_JOB_TOKEN` scope, protected vs unprotected variables, variable exposure in MR pipelines from forks |
| Script Injection | Unescaped attacker-controlled CI variables (`$CI_COMMIT_MESSAGE`, `$CI_MERGE_REQUEST_TITLE`) in `script:` blocks |
| Artifact Security | Sensitive data in artifacts, public artifact exposure, artifact passing between stages |
| Runner Security | Shared vs project runners, privileged Docker executors, tag-based access control |
| Include/Extend Risks | Remote includes from untrusted sources, template injection via includes |
| Permissions | Pipeline permissions, protected branches, deploy keys vs tokens |
| Docker-in-Docker | DinD with `--privileged`, socket mounting in CI, image registry auth |
| Grep Patterns | Commands to find common CI security issues |

Sources: GitLab security documentation, OWASP CI/CD security guidance.

### New file: `report-template.md` (~30 lines)

Extracted from the Sentry SKILL.md output format section to keep SKILL.md under 100 lines. Contains the structured markdown report template with finding and verification formats.

---

## Output Format

Reports written to `docs/security-reviews/YYYY-MM-DD-<component>.md`. The full report template (section structure, finding format, verification format) lives in `references/report-template.md`.

### New file: `report-template.md`

Contains the structured report format with:
- Summary section (finding counts, risk level, confidence)
- Findings section with `[VULN-001]` numbering (location, confidence, issue, impact, evidence, fix)
- Needs Verification section with `[VERIFY-001]` numbering (location, question)
- "No high-confidence vulnerabilities identified" fallback when clean

---

## Integration

### Preset manifests

The skill lives in `core/skills/` so it's available to all presets via the `"skills": "all"` directive. No manifest changes needed.

### CLAUDE-base.md

Add a trigger entry:

```markdown
### `/security-review`
**Trigger when:** the user asks for "security review", "find vulnerabilities", "check for security issues", "audit security", "OWASP review", or to review code for injection, XSS, authentication, authorization, or cryptography issues.
```

### Future extensions

- Add `github-actions.md` reference for GitHub Actions CI/CD security (personal projects)
- Add `data-engineering.md` reference for pipeline-specific patterns (Airflow, dbt, notebook security) if gaps emerge in practice
- Add language guides (Go, Rust, Java) if team scope expands
