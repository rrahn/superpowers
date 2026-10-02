---
name: release-python-package
description: 'Cut a release for a setuptools_scm-versioned Python package. Use when the user asks to "make a release", "cut a release", "prepare a release", "release this package", "create a release branch", or "release vX.Y.Z". Creates a release/vX.Y.Z branch, generates a Keep a Changelog entry from git commits since the last release, commits it, pushes, and opens a PR against the default branch via the gh CLI. Uses bundled scripts to evaluate git/version state so the steps do not need to be re-derived.'
argument-hint: '[optional target version X.Y.Z]'
version: 0.0.1
---

# Release a Python package (setuptools_scm)

Prepares a release branch, changelog, and PR for a Python package whose version is
managed by `setuptools_scm` (dynamic `version` in `pyproject.toml`, `[tool.setuptools_scm]`).

## When to use
- The user wants to initiate/prepare a release for a Python package.
- The package uses `setuptools_scm` (no hardcoded version; tags drive the version).
- A `CHANGELOG.md` in the Keep a Changelog format is present (or should be created).

## Prerequisites
- `gh` CLI authenticated (`gh auth status`).
- A clean working tree on an up-to-date default branch.
- `git`, and one of `python`/`uv`/`uvx` able to run `setuptools_scm`.

## Procedure

Run scripts from the skill directory. They are read-only or clearly scoped and
print machine-readable output — do not re-implement their logic inline.

### 1. Evaluate git + version state
Run [release-state.sh](./scripts/release-state.sh). It reports: repo root, current
branch, default branch, working-tree cleanliness, last tag (or `NONE`), the
`setuptools_scm` computed version, and the commit list since the last release.

- If the working tree is `dirty`, stop and ask the user to commit/stash first.

### 2. Decide the release version
`setuptools_scm` gives a dev/post version, **not** the release number. Pick the
next Semantic Version from the commit set (see
[changelog-format.md](./references/changelog-format.md) → "Choosing the version number"):
- No prior tags → propose `0.1.0` and **confirm with the user**.
- Prior tag → bump major/minor/patch based on the commits.

If the user passed a version argument, use it. Otherwise confirm before proceeding.

### 3. Create the release branch
Run [create-release-branch.sh](./scripts/create-release-branch.sh) `<X.Y.Z>`.
Creates `release/vX.Y.Z` off an up-to-date default branch (refuses a dirty tree).

### 4. Write the changelog entry
Edit `CHANGELOG.md` following [changelog-format.md](./references/changelog-format.md):
- Add a `## [X.Y.Z] - YYYY-MM-DD` section directly below the intro paragraph,
  above the previous release.
- Categorise the commits from step 1 into Added / Changed / Fixed / Removed /
  Security. Reword terse subjects into user-facing bullets; keep issue refs (`#NN`).
- Do **not** add an `## [Unreleased]` placeholder section — keep the changelog
  clean, only released versions appear.
- Append the tag link reference for the new version at the bottom of the file
  (no `[Unreleased]` compare link).

The commits are already available from step 1's `COMMITS_SINCE_LAST_RELEASE` output —
do not re-query git.

### 5. Commit the changelog
Run [commit-changelog.sh](./scripts/commit-changelog.sh) `<X.Y.Z>`. Commits
`CHANGELOG.md` as `docs(changelog): prepare vX.Y.Z release notes`.

### 6. Push and open the PR
Write the PR body to a temp file (reuse the changelog section content — do NOT use
heredocs). Then run [push-and-pr.sh](./scripts/push-and-pr.sh) `<X.Y.Z>` `<body-file>`.
Pushes the branch and opens a PR titled `Release vX.Y.Z` against the default branch.

### 7. Detect auto-release workflow, report, and WAIT for human confirmation

Run [detect-release-workflow.sh](./scripts/detect-release-workflow.sh). It scans
`.github/workflows/` for a workflow that auto-creates a tag and GitHub release when
a `release/vX.Y.Z` branch is merged.

Confirm the PR is open: `gh pr view --json url,state,baseRefName` (must be `OPEN`
against the default branch).

Report to the user:
- The PR URL.
- The auto-release finding:
  - `AUTO_RELEASE=true` → "This repo has `WORKFLOW_FILE` which will automatically
    create the `vX.Y.Z` tag and GitHub release when the PR is merged. The release
    notes will be auto-generated from PR titles; I will update them with the
    curated changelog after merge."
  - `AUTO_RELEASE=false` → "No auto-release workflow found. After merging the PR,
    confirm back and I will create the tag and GitHub release."

**STOP here.** End your turn. Do not proceed until the user responds with one of:
- **"merged"** (or equivalent) → continue to step 8.
- **"abort"** (or equivalent) → stop; remind them to delete the branch locally and
  on origin if needed.
- **Requested changes** → apply them, amend/push the branch, and wait again.

### 8. Post-merge finalization (conditional on auto-release)

Once the user confirms the PR was merged, switch to the default branch and pull:

```bash
git checkout <default_branch> && git pull
```

Then run [finalize-release.sh](./scripts/finalize-release.sh) `<X.Y.Z>`.
The script handles both cases automatically:

- **`AUTO_RELEASE=true`** (workflow-driven repo): the CI workflow will have already
  created the tag on the merge commit and a GitHub release with auto-generated notes.
  `finalize-release.sh` detects the existing release and **updates its body** with the
  curated notes extracted from `CHANGELOG.md`.
- **`AUTO_RELEASE=false`** (manual repo): `finalize-release.sh` creates the `vX.Y.Z`
  tag on `HEAD` of the default branch, pushes it, and opens a new GitHub release with
  the curated changelog notes.

Report the final release URL to the user.

## Scripts
- [release-state.sh](./scripts/release-state.sh) — evaluate git/version state (read-only).
- [create-release-branch.sh](./scripts/create-release-branch.sh) — create `release/vX.Y.Z`.
- [commit-changelog.sh](./scripts/commit-changelog.sh) — commit `CHANGELOG.md`.
- [push-and-pr.sh](./scripts/push-and-pr.sh) — push branch + open PR via `gh`.
- [detect-release-workflow.sh](./scripts/detect-release-workflow.sh) — detect auto-release CI workflows (read-only).
- [finalize-release.sh](./scripts/finalize-release.sh) — post-merge: ensure tag + create/update GitHub release.
