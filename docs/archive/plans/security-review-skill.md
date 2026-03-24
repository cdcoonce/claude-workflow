# Plan: Security Review Skill

> Source PRD: [GitLab Issue #1](https://gitlab.com/Charles.Coonce/claude-workflow/-/work_items/1)
> Design Spec: `docs/superpowers/specs/2026-03-23-security-review-design.md`

## Architectural decisions

Durable decisions that apply across all phases:

- **Skill location**: `core/skills/security-review/` (core skill, auto-included in all presets)
- **Reference structure**: flat `references/` directory, one level deep, no subdirectories
- **Output location**: `docs/security-reviews/YYYY-MM-DD-<component>.md` (in target project, not in core)
- **Build integration**: automatic via `"skills": "all"` in preset manifests — no manifest changes needed
- **CLAUDE-base.md**: add `/security-review` trigger entry following existing pattern
- **Attribution**: OWASP Cheat Sheet Series CC BY-SA 4.0 comment in SKILL.md
- **Confidence model**: HIGH = report, MEDIUM = "needs verification", LOW = suppress

---

## Phase 1: SKILL.md + Report Template

**User stories**: Core skill invocation, structured report output

### What to build

The main skill file (`SKILL.md`, <100 lines) and the report template reference (`references/report-template.md`). SKILL.md contains the review process, confidence levels, severity classification, context detection table, and "do not flag" rules — adapted from the Sentry original but compressed to fit the line budget. The report template defines the structured markdown output format with VULN/VERIFY numbering.

After this phase, the skill directory exists and is invocable. It produces correctly-formatted reports but has no vulnerability reference material yet.

### Acceptance criteria

- [ ] `core/skills/security-review/SKILL.md` exists and is under 100 lines
- [ ] Frontmatter has `name` and `description` (with "Use when" triggers, under 1024 chars)
- [ ] OWASP CC BY-SA 4.0 attribution comment present
- [ ] Quick Start section with invocation example
- [ ] Confidence levels table: HIGH/MEDIUM/LOW with actions
- [ ] Context detection table maps code types to reference files
- [ ] Severity classification table: Critical/High/Medium/Low
- [ ] `references/report-template.md` exists with VULN-001/VERIFY-001 format
- [ ] Output path convention documented: `docs/security-reviews/YYYY-MM-DD-<component>.md`
- [ ] SKILL.md instructs agent to create `docs/security-reviews/` directory if it doesn't exist

---

## Phase 2: Core Vulnerability References

**User stories**: Review code for standard OWASP vulnerability categories

### What to build

All 17 OWASP-derived core vulnerability reference files, copied verbatim from the Sentry skill's `references/` directory. No content modifications — these are battle-tested reference material.

Files: `api-security.md`, `authentication.md`, `authorization.md`, `business-logic.md`, `cryptography.md`, `csrf.md`, `data-protection.md`, `deserialization.md`, `error-handling.md`, `file-security.md`, `injection.md`, `logging.md`, `misconfiguration.md`, `modern-threats.md`, `ssrf.md`, `supply-chain.md`, `xss.md`.

After this phase, the skill can review code against all standard vulnerability categories.

### Acceptance criteria

- [ ] All 17 reference files exist in `core/skills/security-review/references/`
- [ ] Content matches Sentry source verbatim (no modifications)
- [ ] Each file is valid markdown with a top-level heading
- [ ] All files referenced in SKILL.md context detection table are present

---

## Phase 3: Python Language Guide

**User stories**: Framework-aware Python security review (Django, Flask, FastAPI, SQLAlchemy)

### What to build

The Python language guide (`references/python.md`), relocated from the Sentry skill's `languages/python.md`. No content modifications. This enables framework-specific pattern detection — knowing what Django auto-escapes, what Flask-SQLAlchemy parameterizes, what FastAPI/Pydantic validates.

After this phase, the skill understands Python-specific security patterns and can distinguish safe framework usage from vulnerable patterns.

### Acceptance criteria

- [ ] `references/python.md` exists with Django, Flask, FastAPI, SQLAlchemy sections
- [ ] Content matches Sentry `languages/python.md` verbatim
- [ ] SKILL.md context detection table correctly references `python.md` for Python indicators

---

## Phase 4: Docker + GitLab CI References

**User stories**: Infrastructure security review for containers and CI/CD pipelines

### What to build

Two reference files:

1. `references/docker.md` — relocated from Sentry's `infrastructure/docker.md`, no content modifications. Covers Dockerfile security, runtime config, compose, registry patterns.

2. `references/gitlab-ci.md` — **written from scratch**. Covers GitLab CI/CD pipeline security: secrets in pipelines, variable security (`CI_JOB_TOKEN` scope, protected vs unprotected), script injection via attacker-controlled CI variables, artifact security, runner security, include/extend risks, permissions, Docker-in-Docker patterns, and grep patterns for common issues.

After this phase, the skill can review Dockerfiles, docker-compose configs, and `.gitlab-ci.yml` files for security issues.

### Acceptance criteria

- [ ] `references/docker.md` exists, matches Sentry `infrastructure/docker.md` verbatim
- [ ] `references/gitlab-ci.md` exists (~120-150 lines)
- [ ] `gitlab-ci.md` covers: secrets, variable security, script injection, artifacts, runners, includes, permissions, DinD
- [ ] `gitlab-ci.md` includes grep patterns for finding common CI security issues
- [ ] SKILL.md context detection table correctly references both files

---

## Phase 5: CLAUDE-base.md Integration + Quality Verification

**User stories**: Skill discoverability and quality compliance

### What to build

Add the `/security-review` trigger entry to `core/CLAUDE-base.md` following the existing pattern. Then run quality criteria auto-verify to confirm the skill meets all conventions.

After this phase, the skill is fully integrated, discoverable, and quality-verified.

### Acceptance criteria

- [ ] `core/CLAUDE-base.md` has `/security-review` trigger entry
- [ ] SKILL.md under 100 lines
- [ ] Description under 1024 characters with "Use when" triggers
- [ ] References one level deep (no nested directories)
- [ ] All 21 reference files listed in SKILL.md exist on disk
- [ ] No duplicate content between SKILL.md and reference files
- [ ] No time-sensitive information
- [ ] Build smoke test passes: `uv run python -m scripts.smoke_test` (if applicable)
