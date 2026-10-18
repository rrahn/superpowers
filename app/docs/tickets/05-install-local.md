# 05: Install a skill into the local scope

**What to build:** `skillctl install NAME --scope local` installs into `<repo root>/.github/skills/NAME/` with its own lockfile; fails clearly outside a git repository.

**Blocked by:** 04

**Status:** done

- [x] Works from any subdirectory of the repository
- [x] Clear error outside a git repository, nothing written
- [x] `installed` shows the skill as managed in the local scope
