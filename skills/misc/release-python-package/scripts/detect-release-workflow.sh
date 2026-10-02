#!/usr/bin/env bash
# detect-release-workflow.sh — Check whether this repository has a GitHub Actions
# workflow that automatically creates a tag and/or GitHub release when a
# release/vX.Y.Z branch is merged into the default branch.
#
# Prints machine-readable output:
#   AUTO_RELEASE=true|false
#   WORKFLOW_FILE=<filename>     (only when AUTO_RELEASE=true)
#   REASON=<text>                (only when AUTO_RELEASE=false)
#
# Exit codes: 0 in both cases (the caller reads AUTO_RELEASE=).
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
workflows_dir="$repo_root/.github/workflows"

if [ ! -d "$workflows_dir" ]; then
  echo "AUTO_RELEASE=false"
  echo "REASON=No .github/workflows directory found"
  exit 0
fi

# A workflow is considered an auto-release workflow if it:
#   1. References a "release/" branch/head-ref pattern  AND
#   2. Creates a tag or GitHub release
found_file=""
for f in "$workflows_dir"/*.yml "$workflows_dir"/*.yaml; do
  [ -f "$f" ] || continue
  grep -qE 'release/' "$f" || continue
  if grep -qE \
    "(gh release create|git tag|actions/create-release|softprops/action-gh-release)" \
    "$f"; then
    found_file="$f"
    break
  fi
done

if [ -n "$found_file" ]; then
  echo "AUTO_RELEASE=true"
  echo "WORKFLOW_FILE=$(basename "$found_file")"
else
  echo "AUTO_RELEASE=false"
  echo "REASON=No workflow found that auto-creates a release on release/* merge"
fi
