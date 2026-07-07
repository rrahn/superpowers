#!/usr/bin/env bash
# release-state.sh — Gather all git + versioning state needed to start a release.
#
# Prints a machine-readable report so the agent does NOT need to re-derive these
# commands. Safe to run repeatedly (read-only, no mutations).
#
# Usage: ./release-state.sh
set -euo pipefail

export GIT_PAGER=cat

section() { printf '\n=== %s ===\n' "$1"; }

section "REPO"
repo_root=$(git rev-parse --show-toplevel)
echo "root=$repo_root"
cd "$repo_root"

section "CURRENT_BRANCH"
git branch --show-current

section "DEFAULT_BRANCH"
# Prefer gh; fall back to origin/HEAD symref; default to 'main'.
default_branch=""
if command -v gh >/dev/null 2>&1; then
  default_branch=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || true)
fi
if [ -z "$default_branch" ]; then
  default_branch=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || true)
fi
[ -z "$default_branch" ] && default_branch="main"
echo "$default_branch"

section "WORKING_TREE"
if [ -z "$(git status --porcelain)" ]; then
  echo "clean"
else
  echo "dirty"
  git status --porcelain
fi

section "TAGS"
git fetch --tags --quiet 2>/dev/null || true
last_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [ -z "$last_tag" ]; then
  echo "last_tag=NONE"
else
  echo "last_tag=$last_tag"
fi

section "SCM_VERSION"
# Computed setuptools_scm version (dev/post version, NOT the release number).
scm_ver=""
scm_tmp=$(mktemp)
trap 'rm -f "$scm_tmp"' EXIT
if python -m setuptools_scm >"$scm_tmp" 2>/dev/null; then
  scm_ver=$(cat "$scm_tmp")
elif uv run python -m setuptools_scm >"$scm_tmp" 2>/dev/null; then
  scm_ver=$(cat "$scm_tmp")
elif command -v uv >/dev/null 2>&1 && uv run --with setuptools-scm python -m setuptools_scm >"$scm_tmp" 2>/dev/null; then
  scm_ver=$(cat "$scm_tmp")
elif command -v uvx >/dev/null 2>&1 && uvx --from setuptools-scm python -m setuptools_scm >"$scm_tmp" 2>/dev/null; then
  scm_ver=$(cat "$scm_tmp")
fi
[ -z "$scm_ver" ] && scm_ver="UNKNOWN (setuptools_scm unavailable)"
echo "$scm_ver"

section "COMMITS_SINCE_LAST_RELEASE"
# Feed these to the changelog. No merge commits.
if [ -n "$last_tag" ]; then
  git log "${last_tag}..HEAD" --no-merges --pretty=format:'%h%x09%s'
else
  git log --no-merges --pretty=format:'%h%x09%s'
fi
echo
