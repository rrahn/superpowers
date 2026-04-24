---
name: git-workflow
description: >
  Git version control conventions — conventional commit format (type/scope/subject),
  commit message discipline (why not what, atomic partitions), branch naming strategy
  (feature/, bugfix/, hotfix/), PR best practices (<400 LOC, one concern per PR),
  CHANGELOG maintenance (Keep a Changelog), setuptools_scm tag-driven versioning,
  pre-commit hook stack (ruff, pip-audit, trailing-whitespace), and CI/CD patterns.
  Load when: .git/ directory exists and you are preparing changes for @committer,
  writing commit messages, creating or reviewing PRs, updating CHANGELOG.md, naming
  branches, configuring .pre-commit-config.yaml, or setting up GitHub Actions workflows.
  Marker files: .git/, .pre-commit-config.yaml, CHANGELOG.md, .github/workflows/.
markers:
  - .git/
  - .pre-commit-config.yaml
  - CHANGELOG.md
  - .github/workflows/
globs:
  - "**/.pre-commit-config.yaml"
  - "**/CHANGELOG.md"
  - ".github/workflows/**/*.yml"
alwaysApply: false
tier: 4
---
# Git Workflow

Generalizable git and CI/CD practices for consistent, professional version control.

---

## Conventional Commits

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no logic change
- `refactor`: Restructuring without behaviour change
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Maintenance (deps, build config)
- `ci`: CI/CD pipeline changes

### Subject Line Rules

- **≤ 72 characters and MUST stay on a single line — NEVER wrap the subject onto a second line.** Aim for ≤ 50; hard cap at 72. A wrapped subject produces ugly multi-space gaps in `git log --oneline`.
- Body lines wrapped at 72 characters
- Imperative present tense: "Add feature" not "Added" / "Adds"
- Capitalised, no trailing period

---

## Commit Message Discipline

### Partitioning Changesets

Group uncommitted changes into logical partitions before writing messages — one atomic unit per commit. Cross-cutting refactors get their own commit, separate from feature work.

### Message Content: Why, Not What

The diff shows *what* changed; the message explains *why*:

```
feat(auth): require email verification on signup

Unverified accounts were abused to spam downstream services.
Adding a verification gate at registration prevents abuse
without breaking existing verified users.

Closes #42
```

Body bullets: `    * reason` / `    * intent` / `    * context`

---

## Branch Strategy

- `main` / `trunk` — protected; merge here frequently
- `feature/<description>` or `<username>/<feature-name>`
- `bugfix/<description>`, `hotfix/<description>`
- No long-lived or environment branches (`dev`, `staging` are deployment targets, not branches)

### Rebase vs Merge

- **Rebase** feature branches onto trunk to maintain linear history before opening a PR
- **Merge** trunk into a long-running branch only when you need upstream changes and a rebase would be disruptive (many collaborators, published branch)
- **Squash merge** PRs into trunk — one logical commit per PR keeps `git log` clean
- Never rebase a branch that others have checked out

---

## Committer Delegation

Most agents are **denied** `git commit` and `git push` permissions. Only the `@committer` agent may commit and push. When your changes are ready:

1. **Stage and verify** — run tests, lint, and self-review the diff
2. **Delegate to `@committer`** with a message containing:
   - **Scope of changes** — which files/modules were touched and why
   - **Commit type/scope/subject** — the conventional commit headline (e.g. `feat(auth): add email verification`)
   - **The "why"** — context for the commit body explaining intent, not mechanics

### Delegation template

```
@committer — please commit the staged changes:

Type/scope/subject: feat(parser): support nested TOML arrays
Why: The config loader silently dropped nested arrays, causing
     default values to override user settings. This adds recursive
     array parsing so nested structures round-trip correctly.
Files: src/parser.py, tests/test_parser.py
```

Do **not** attempt `git commit` or `git push` yourself — the command will be denied.

---

## Git Worktrees

Use `git worktree` when you need multiple checkouts of the same repo simultaneously (e.g. reviewing one branch while developing on another, or GasTown agent isolation).

```bash
# Create a worktree for a new feature branch
git worktree add ../feature-work -b feature/new-thing

# Create a worktree tracking an existing remote branch
git worktree add ../hotfix-work origin/hotfix/urgent

# List all worktrees
git worktree list

# Clean up after merging
git worktree remove ../feature-work
```

**Key details:**
- Worktree checkouts contain a `.git` **file** (not a directory) pointing back to the main repo's `.git/worktrees/` entry
- Each worktree must be on a **unique branch** — two worktrees cannot check out the same branch
- Run `git worktree prune` to clean up stale entries after manually deleting worktree directories

---

## Pull Request Practices

- Aim for <400 lines changed per PR; split larger work into a stack
- One concern per PR; link all related issues

### PR Checklist

- [ ] Self-review done; no secrets committed
- [ ] Tests added/updated and passing
- [ ] Documentation and CHANGELOG updated
- [ ] Type labelled: bug fix / new feature / breaking change / docs

**Authors:** respond to all comments.  
**Reviewers:** review within 24 h; be constructive; use "Request Changes" sparingly.

---

## CHANGELOG (Keep a Changelog)

Update before merging any user-visible change. Follow [keepachangelog.com](https://keepachangelog.com/).

```markdown
## [Unreleased]
## [1.2.3] - YYYY-MM-DD
### Added / Changed / Fixed / Security / Deprecated / Removed
- One-line description per entry
```

---

## Versioning with setuptools_scm

Drive versions from git tags — no manual version files.

```toml
# pyproject.toml
[tool.setuptools_scm]
tag_regex = "^v(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+)$"
local_scheme = "node-and-date"
version_scheme = "post-release"
```

```bash
# MAJOR.MINOR.PATCH — breaking / feature / fix
git tag v1.2.3 && git push --tags
```

---

## Pre-commit Hook Stack

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.7
    hooks:
      - id: ruff-format
      - id: ruff
        args: [--fix]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
  - repo: https://github.com/pypa/pip-audit
    rev: v2.10.0
    hooks:
      - id: pip-audit
```

```bash
pre-commit install          # install
pre-commit run --all-files  # run manually
pre-commit autoupdate       # bump versions
```

---

## CI/CD Patterns

### Workflow Triggers

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

### Dependency Caching

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('**/uv.lock') }}
    restore-keys: ${{ runner.os }}-uv-
```

### Matrix Testing

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12', '3.13']
```

### Deployment Triggers

- **Lower environments** — auto-deploy on merge to `main`
- **Production** — manual approval gate (`environment: production`)
- `workflow_dispatch` for ad-hoc manual deploys

### CI Discipline

- Total CI time under 10 minutes; lint/type-check before tests (fail fast)
- Run independent jobs in parallel
- Never hard-code credentials; use secrets and OIDC role assumption
- Run `pip-audit` (or equivalent) in CI to catch vulnerable dependencies
