# 05: Install a skill into the local scope

**What to build:** `skillctl install NAME --scope local` installs into `<repo root>/.github/skills/NAME/` with its own lockfile; fails clearly outside a git repository.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] Works from any subdirectory of the repository
- [ ] Clear error outside a git repository, nothing written
- [ ] `installed` shows the skill as managed in the local scope
