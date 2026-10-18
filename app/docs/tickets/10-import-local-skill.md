# 10: Import internally maintained skills from a local path

**What to build:** `skillctl upstream import PATH --collection C` copies a skill from a local path into the collection and records local provenance; `upstream check` then compares it with that path and reports "unavailable" when the path is missing.

**Blocked by:** 09

**Status:** ready-for-agent

- [ ] Validates `SKILL.md` name matches directory
- [ ] Refuses to overwrite an existing catalog skill without `--force`
- [ ] Local provenance participates in `upstream check`
