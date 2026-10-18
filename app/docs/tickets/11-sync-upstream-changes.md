# 11: Sync upstream changes

**What to build:** `skillctl upstream sync [COLLECTION] [SKILL...]` applies the change set from `upstream check` to the working tree — adds new skills, writes modified/added files, deletes files removed upstream — after confirmation; `--dry-run` and `--yes` supported. Orphaned and unavailable skills are kept.

**Blocked by:** 09, 10

**Status:** ready-for-agent

- [ ] Dry-run and apply share one plan (identical output)
- [ ] GitHub changes are read at the commit the check resolved, never a re-resolved ref
- [ ] Imported skills sync from their recorded local origin, byte for byte
- [ ] Each skill is replaced atomically (`fsops.replacing`); a failure leaves it untouched
- [ ] Nothing committed; summary tells the user to review the diff

Notes from ticket 10's review: give each `SkillChange` its origin (GitHub repo@commit:path, or the local path) so sync doesn't re-read `skills/sources.toml` to tell mixed collections apart.
