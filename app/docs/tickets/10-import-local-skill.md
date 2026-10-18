# 10: Import internally maintained skills from a local path

**What to build:** `skillctl upstream import PATH --collection C` copies a skill from a local path into the collection and records local provenance; `upstream check` then compares it with that path and reports "unavailable" when the path is missing.

**Blocked by:** 09

**Status:** done

- [x] Validates `SKILL.md` name matches directory
- [x] Provenance per skill in `skills/sources.toml` (`[collections.<c>.skills.<skill>] local = "…"`). Local origins are compared live by content, so no commit/hash is stored; GitHub provenance keeps the commit in the check report for ticket 11.
- [x] `~` in local paths is expanded when read, kept as written in the file
- [x] Refuses to overwrite an existing catalog skill without `--force`
- [x] Local provenance participates in `upstream check`

Also in this ticket: collections whose `upstream` is `local` are now compared too (the `skipped` status from ticket 09 is gone), and collection names are validated.
