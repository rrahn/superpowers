#!/usr/bin/env bash
# finalize-release.sh — Post-merge: ensure the vX.Y.Z tag exists on the default
# branch and create or update the GitHub release with curated changelog notes.
#
# Handles both repo patterns:
#   • Workflow-driven: tag and a GitHub release already exist (auto-created by CI).
#     This script updates the release body with notes from CHANGELOG.md.
#   • Manual: no tag/release yet. Script creates the tag on HEAD and opens the
#     GitHub release.
#
# Precondition: caller must be on the default branch with a clean, up-to-date
# working tree (run `git pull` first).
#
# Usage: ./finalize-release.sh <X.Y.Z>
set -euo pipefail
export GIT_PAGER=cat

version="${1:?Usage: finalize-release.sh <X.Y.Z>}"
tag="v${version}"

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

# ── Ensure we have up-to-date remote tags ───────────────────────────────────
git fetch --tags --quiet 2>/dev/null || true

# ── Ensure the tag exists on origin ─────────────────────────────────────────
if git tag --list "$tag" | grep -q "^${tag}$"; then
  echo "Tag $tag exists (commit: $(git rev-list -n1 "$tag"))."
  git push origin "$tag" 2>/dev/null && echo "  Verified on origin." \
    || echo "  Already on origin."
else
  echo "Tag $tag not found — creating on HEAD ($(git rev-parse --short HEAD))."
  git tag "$tag"
  git push origin "$tag"
  echo "Pushed $tag."
fi

# ── Extract changelog section for this version ──────────────────────────────
changelog_file="$repo_root/CHANGELOG.md"
if [ ! -f "$changelog_file" ]; then
  echo "ERROR: CHANGELOG.md not found at $changelog_file" >&2
  exit 1
fi

notes_file=$(mktemp /tmp/release-notes-XXXX.md)
trap 'rm -f "$notes_file"' EXIT

# Extract everything between "## [X.Y.Z]" (exclusive) and the next "## [" (exclusive).
awk -v ver="[${version}]" \
  'found && /^## \[/{exit}
   /^## \[/{if (index($0, ver)) found=1; next}
   found{print}' \
  "$changelog_file" \
  > "$notes_file"

# Trim leading and trailing blank lines (portable awk, no sed -i).
awk 'NF{found=1} found' "$notes_file" > "${notes_file}.tmp" && mv "${notes_file}.tmp" "$notes_file"

if [ ! -s "$notes_file" ]; then
  echo "ERROR: No changelog section found for [$version] in CHANGELOG.md" >&2
  exit 1
fi

echo "Extracted changelog notes for $version."

# ── Create or update the GitHub release ─────────────────────────────────────
if gh release view "$tag" --json tagName >/dev/null 2>&1; then
  echo "GitHub release $tag already exists — updating with curated changelog notes."
  gh release edit "$tag" --title "Release ${tag}" --notes-file "$notes_file"
else
  echo "Creating GitHub release for $tag."
  gh release create "$tag" --title "Release ${tag}" --notes-file "$notes_file"
fi

echo ""
echo "=== RELEASE FINALIZED ==="
gh release view "$tag" --json url,name,tagName,publishedAt
