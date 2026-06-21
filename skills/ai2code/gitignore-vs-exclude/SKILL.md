---
name: gitignore-vs-exclude
description: >
  Git ignore scope hygiene — distinguishes .gitignore (shared, committed, for all
  contributors) from .git/info/exclude (personal, per-clone, untracked) and the global
  gitignore. Load when: working in any git repo and touching .gitignore, adding files to
  ignore, reviewing PRs with .gitignore changes, or when any file that looks
  developer-local (scratch dirs, AI assistant configs like .claude/ or CLAUDE.md, local
  logs, .direnv/, editor configs) appears in .gitignore. Teaches the decision rule
  "would every contributor benefit from ignoring this?" and flags developer-local entries
  that should go in .git/info/exclude instead. Marker files: .git/
markers:
  - .git/
globs:
  - "**/.gitignore"
  - ".git/info/exclude"
alwaysApply: false
tier: 4
metadata:
  version: "1.0"
  sources: "https://git-scm.com/docs/gitignore"
user-invocable: true
---

# Git Ignore Scope Hygiene

## The Decision Rule

> **"Would every contributor to this repository benefit from ignoring this file?"**
>
> **YES** → `.gitignore`
> **NO** → `.git/info/exclude` (or global gitignore)

A harder version of NO: "Does this file exist because of _my specific local setup_, not
because of the project itself?" If yes, it is developer-local — keep it out of `.gitignore`.

## The Three Mechanisms

| Mechanism           | Location                                                                | Committed? | Scope                                  |
| ------------------- | ----------------------------------------------------------------------- | ---------- | -------------------------------------- |
| `.gitignore`        | Repo root (or subdirs)                                                  | Yes        | All contributors to this repo          |
| `.git/info/exclude` | `.git/info/exclude`                                                     | No         | This clone only (you, on this machine) |
| Global gitignore    | `~/.config/git/ignore` (default) or custom path via `core.excludesFile` | No         | All repos on this machine              |

## What Belongs Where

### `.git/info/exclude` — developer-local patterns

These are produced by one developer's personal tooling, not by the project:

- **AI assistant configs**: `.claude/`, `CLAUDE.md`, `.cursor/`, `.aider`, `.aider.chat.history.md`, `.copilot/`
- **Local dev environment**: `.direnv/`, `.envrc` (when not part of the project's standard tooling)
- **Personal scratch/notes**: `scratch/`, `notes/`, `*.local.md`, `TODO.personal.md`
- **Local run artifacts**: `logs/`, `*.log` (unless the project standardises logging here)
- **Local build outputs**: personally-named binaries (e.g. `opencode-dev`), debug builds
- **Editor configs** (when the team does not standardise on one editor): `.vscode/`, `.idea/`, `*.swp`, `*.swo`, `.DS_Store`
- **Machine-local tooling state**: any directory produced by developer-machine tools, not by the project's build system

### `.gitignore` — shared, project-wide patterns

These are produced by the project itself, for every contributor:

- **Build outputs all developers produce**: `dist/`, `build/`, `__pycache__/`, `*.pyc`, `node_modules/`, `.venv/`, `*.egg-info/`
- **Language-native artifacts**: `*.o`, `*.a`, `*.class`, `*.wasm`
- **Secrets that must never be committed**: `.env`, `*.key`, `credentials.json` (pair with a `.env.example`)
- **Project-specific tooling artifacts**: `.dolt/` in a Dolt project, `*.bun-build` in a Bun project, `tsconfig.tsbuildinfo` in TypeScript
- **Generated files** the project's build system produces

### Global gitignore — OS/editor noise across all repos

Move patterns here when they apply to every repo on your machine, not just one:

- `.DS_Store`, `Thumbs.db`
- `*.swp`, `*.swo`, `*~`
- `.idea/`, `.vscode/` (if you always use the same editor)

Git uses `~/.config/git/ignore` by default. To use a custom path (common convention:
`~/.gitignore_global`): `git config --global core.excludesFile ~/.gitignore_global`

## Real-World Example

From a fork maintenance review — entries found in the committed `.gitignore`:

```gitignore
# WRONG — developer-local, belongs in .git/info/exclude
.direnv/          # one dev's direnv setup
logs/             # one dev's personal run logs
scratch/          # one dev's investigation notes
.claude/          # one dev's AI assistant config
CLAUDE.md         # one dev's AI assistant instructions

# CORRECT — all fork contributors produce these
.dolt/                 # fork-specific tooling
.beads-credential-key  # fork-specific credential file
*.bun-build            # build artifact (Bun stack)
tsconfig.tsbuildinfo   # TypeScript build artifact
```

## Editing `.git/info/exclude`

The file already exists in every git repo (`git init` creates it). It uses identical
syntax to `.gitignore` — one pattern per line. Add patterns below the existing comment
header:

```bash
# View current personal excludes
cat .git/info/exclude
```

Use the Edit tool to modify `.git/info/exclude` directly — not shell redirection.

After adding patterns, verify with `git status` — matched files should no longer appear
as untracked. If a file was already tracked before adding the exclude pattern, the pattern
has no effect — untrack it first with `git rm --cached <file>`.

## Active Duties

When this skill is loaded:

1. **Reviewing `.gitignore` changes**: Check each new entry against the decision rule.
   Flag any developer-local entry and explain why it belongs in `.git/info/exclude`.

2. **Discovering developer-local entries already in `.gitignore`**: Surface the finding
   and suggest moving them to `.git/info/exclude` as a separate cleanup step. Do not
   silently move them without being asked.

3. **Creating personal/local files during a task** (scratch notes, debug outputs, local
   experiment files): Add them to `.git/info/exclude` proactively — never to `.gitignore`.

4. **Editing `.git/info/exclude`**: Use the Edit tool to modify the file at
   `.git/info/exclude`. Do not use `echo >>` or shell redirection.

## References

- [gitignore documentation](https://git-scm.com/docs/gitignore) — covers all three mechanisms and pattern syntax
- See also: `git-workflow` skill for commit conventions and PR hygiene
