#!/usr/bin/env bash
# create-release-branch.sh — Create the release/vX.Y.Z branch off the default branch.
#
# Refuses to run on a dirty working tree. Starts the branch from an up-to-date
# copy of the default branch.
#
# Usage: ./create-release-branch.sh <X.Y.Z>
set -euo pipefail
export GIT_PAGER=cat

version="${1:?Usage: create-release-branch.sh <X.Y.Z>}"
branch="release/v${version}"

cd "$(git rev-parse --show-toplevel)"

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: working tree is dirty. Commit or stash changes first." >&2
  exit 1
fi

# Resolve default branch.
default_branch=""
if command -v gh >/dev/null 2>&1; then
  default_branch=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || true)
fi
[ -z "$default_branch" ] && default_branch=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || true)
[ -z "$default_branch" ] && default_branch="main"

git fetch origin "$default_branch" --quiet
git checkout -b "$branch" "origin/${default_branch}"
echo "Created and switched to $branch (from origin/${default_branch})"
