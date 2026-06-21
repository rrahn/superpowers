---
name: surgical-changes
description: >
  Minimal-intervention discipline for making focused, scope-locked code changes. Prevents
  the most common AI agent anti-patterns: scope creep (refactoring untouched code), pattern
  modernization (introducing newer framework idioms into an older codebase), dependency
  version bumps inside feature/fix PRs, variable renaming "for clarity", import
  reorganization, and gratuitous method extraction. Includes a pre-change checklist, rules
  for handling unrelated bugs discovered mid-task, and testing boundaries. Load when:
  implementing a bug fix, adding a feature to an existing codebase, making a PR-scoped
  change, touching code you did not write, working in a mature or unfamiliar codebase, or
  any time you catch yourself wanting to "clean up" code adjacent to your actual goal.
alwaysApply: false
tier: 5
user-invocable: true
---
# Surgical Changes Policy

Minimal-intervention guidelines for working in any active codebase.
These principles govern *planning and scope* — not the fix-cycle mechanics
(see `implementor-fix-cycle` agent for that).

---

## Core Rules

### 1. Change Only the Exact Lines Required

Before writing a single line, identify the precise scope:

- Touch only the functions/files required by the stated goal
- Do not fix unrelated bugs noticed "while you're there"
- Do not improve code style in untouched sections
- Do not rename existing variables, methods, or classes unless the goal demands it
- Do not reorganize imports, extract methods, or restructure files
- Do not add type annotations to existing function signatures unless the goal specifically requires it

> If a change wasn't on the plan before you started, it shouldn't appear in the diff.

**Comment & docstring rule:** Don't touch comments on code you didn't change.
*Do* update docstrings and comments on code you *did* change — if you alter a function's
behavior, its docstring MUST reflect the new behavior. Stale docs are worse than no docs.

### 2. Never Update Dependency Versions in a Feature/Fix PR

Version bumps are their own separate task requiring full regression testing:

- Do not update package versions (`requirements.txt`, `pyproject.toml`, `package.json`, `Gemfile`)
- Do not upgrade base Docker images
- Do not change language/runtime versions
- If the current version has a limitation, work within it and document it — do not "fix" it by upgrading

### 3. Write Code Idiomatic to the Existing Framework Version

New code must look like it belonged in the codebase when it was first written:

- Match the patterns, idioms, and library usage of the surrounding code
- Do not introduce patterns or APIs from newer framework versions, even if you know better ones
- If existing views use `APIView` + manual serializer validation, your new view should too
- When in doubt: copy the structure of the nearest similar thing in the codebase

### 4. Comprehensive Tests for All New Code

Tests must go beyond smoke tests — cover the full surface of what you added:

| Must test | Must NOT test |
|---|---|
| All new functions/methods | Existing unchanged code |
| All new branches and conditions | |
| Success path AND all failure paths | |
| Edge cases: empty/null/zero inputs | |
| Boundary conditions: min/max values | |
| Integration with existing code | |

Follow the existing test patterns in the project (class-based, parametrized, etc.).
Aim for full coverage of lines you wrote; untested new code is unfinished code.

---

## Pre-Change Checklist

Work through this before touching any file.

**Planning**
- [ ] Can I describe the exact minimal scope in one sentence?
- [ ] Have I identified every file that must change (and confirmed no others need to)?
- [ ] Is there an existing pattern in the codebase I should follow?

**Implementation**
- [ ] Am I using idioms appropriate for this framework version?
- [ ] Am I preserving all existing functionality and comments on untouched code?
- [ ] Have I updated docstrings/comments on code I *did* change? (see Rule 1 comment rule)
- [ ] Am I leaving dependency versions untouched?

**Testing**
- [ ] Do my tests cover all new branches, including error paths?
- [ ] Do my tests cover edge cases and boundary conditions?
- [ ] Do my tests follow the existing test patterns in this project?

**Review**
- [ ] Can I justify every single changed line against the stated goal?
- [ ] Would the code owners immediately understand why these specific lines changed?

---

## Diff Hygiene

Every line in the diff must relate to the stated goal. Nothing else.

- Never mix whitespace-only changes with functional changes in the same commit
- Never include formatting changes on lines you didn't functionally modify
- If a formatter or linter auto-fixes untouched lines, undo those changes before committing
- Run formatters only on files you modified: `ruff format <your-files>`, not `ruff format .`
- Use `--check` / `--diff` mode first to preview what a formatter will touch
- The diff should be reviewable at a glance — if a reviewer has to ask "why did this line change?", you over-reached

---

## When You Discover Unrelated Issues

- **Unrelated bug**: Document it separately; do not fix it in this PR
- **Scope creep required**: Stop, reassess, get explicit approval before expanding
- **Critical blocker bug**: Only fix it if it directly prevents your goal; document why

---

## The Golden Rule

> **Change only what you must. Test what you change. Respect what exists.**
