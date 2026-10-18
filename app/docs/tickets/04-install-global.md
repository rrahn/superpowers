# 04: Install a skill globally

**What to build:** `skillctl install NAME` copies every file of the catalog skill into `~/.copilot/skills/NAME/` atomically and records it in the lockfile; `skillctl installed` then shows it as managed.

**Blocked by:** 03

**Status:** done

- [x] All files of the skill directory copied (nested files included)
- [x] Refuses to overwrite an existing installation without `--force`
- [x] Unknown name fails with close-match suggestions
- [x] A failed download leaves no partial directory and no lockfile entry
