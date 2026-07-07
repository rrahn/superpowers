#!/usr/bin/env bash
# commit-changelog.sh — Stage and commit CHANGELOG.md with a conventional message.
#
# Run AFTER editing CHANGELOG.md for the release. No-op safe: fails clearly if
# CHANGELOG.md has no staged/unstaged changes.
#
# Usage: ./commit-changelog.sh <X.Y.Z>
set -euo pipefail
export GIT_PAGER=cat

version="${1:?Usage: commit-changelog.sh <X.Y.Z>}"
cd "$(git rev-parse --show-toplevel)"

if git diff --quiet -- CHANGELOG.md && git diff --cached --quiet -- CHANGELOG.md; then
  echo "ERROR: CHANGELOG.md has no changes to commit. Edit it first." >&2
  exit 1
fi

git add CHANGELOG.md
git commit -m "docs(changelog): prepare v${version} release notes"
git log --oneline -1
