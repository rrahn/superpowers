# 11: Sync upstream changes

**What to build:** `skillctl upstream sync [SKILL...]` applies the change set from `upstream check` to the working tree — adds new skills, writes modified/added files, deletes files removed upstream — after confirmation; `--dry-run` and `--yes` supported. Orphaned skills are kept.

**Blocked by:** 09

**Status:** ready-for-agent

- [ ] Dry-run and apply share one plan (identical output)
- [ ] Provenance commit updated after a successful sync
- [ ] Nothing committed; summary tells the user to review the diff
