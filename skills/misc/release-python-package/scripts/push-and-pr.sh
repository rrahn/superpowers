#!/usr/bin/env bash
# push-and-pr.sh — Push the release branch and open a PR against the default branch.
#
# Usage: ./push-and-pr.sh <X.Y.Z> <path-to-pr-body.md>
set -euo pipefail
export GIT_PAGER=cat

version="${1:?Usage: push-and-pr.sh <X.Y.Z> <pr-body.md>}"
body_file="${2:?Usage: push-and-pr.sh <X.Y.Z> <pr-body.md>}"
branch="release/v${version}"

cd "$(git rev-parse --show-toplevel)"

if [ ! -f "$body_file" ]; then
  echo "ERROR: PR body file not found: $body_file" >&2
  exit 1
fi

current=$(git branch --show-current)
if [ "$current" != "$branch" ]; then
  echo "ERROR: current branch is '$current', expected '$branch'." >&2
  exit 1
fi

# Resolve default branch.
default_branch=""
if command -v gh >/dev/null 2>&1; then
  default_branch=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || true)
fi
[ -z "$default_branch" ] && default_branch=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || true)
[ -z "$default_branch" ] && default_branch="main"

git push -u origin "$branch"

gh pr create \
  --base "$default_branch" \
  --head "$branch" \
  --title "Release v${version}" \
  --body-file "$body_file"
