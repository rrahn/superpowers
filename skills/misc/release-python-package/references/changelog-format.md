# Keep a Changelog — cheat sheet

Reference: https://keepachangelog.com/en/1.0.0/

The project `CHANGELOG.md` follows Keep a Changelog + Semantic Versioning.

## Structure

- Do **not** add an `## [Unreleased]` placeholder section. Keep the changelog
  clean — only concrete, released versions appear. (This rule lives in the skill;
  the changelog itself carries no placeholder.)
- Insert the new release section directly below the intro paragraph, above the
  previous release:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features.

### Changed
- Changes in existing functionality.

### Deprecated
- Soon-to-be removed features.

### Removed
- Now removed features.

### Fixed
- Bug fixes.

### Security
- Vulnerability fixes.
```

Only include subsections that have entries.

## Categorising commits

Map commit subjects to sections:

| Commit prefix / intent                     | Section    |
|--------------------------------------------|------------|
| `feat`, "Add", "Implement", new adapter    | Added      |
| `refactor`, "Rename", "Restructure", schema updates | Changed |
| `fix`, "Fix", dtype/bug corrections        | Fixed      |
| removals                                   | Removed    |
| security patches                           | Security   |

Reword terse commit subjects into user-facing bullets. Reference issue numbers
(e.g. `(#22)`) when the commit subject mentions them.

## Link references (bottom of file)

Update/append the tag link for the new version:

```markdown
[X.Y.Z]: https://github.com/<owner>/<repo>/releases/tag/vX.Y.Z
```

Do not add an `[Unreleased]` compare link. For a subsequent release, the new tag
compares against the previous tag:

```markdown
[X.Y.Z]: https://github.com/<owner>/<repo>/compare/vPREV...vX.Y.Z
```

## Choosing the version number

`setuptools_scm` computes a *dev/post* version from the last tag — it does **not**
decide the release number. You (with the user) pick the next Semantic Version:

- No prior tags → this is the first release. Propose `0.1.0` (or `0.0.1` / `1.0.0`)
  and confirm with the user.
- Prior tag exists → bump per SemVer based on the commit set:
  - breaking changes → major
  - new features → minor
  - fixes only → patch

## After the PR merges

Versioning is driven by `setuptools_scm`, so the package only builds as `X.Y.Z`
once a matching tag exists. Tag the merge commit and push the tag:

```bash
git checkout main && git pull
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```
