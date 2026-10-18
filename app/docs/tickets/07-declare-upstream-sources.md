# 07: Declare upstream sources

**What to build:** a pydantic-validated `skills/sources.toml` declaring upstream sources per collection (GitHub `owner/repo` + ref + path, or local path) and per-skill provenance; `skillctl sources list` renders it as a table. Seed the file for this repository.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Invalid files fail with a message naming the bad key
- [ ] Seeded with ai2code, mattpocock, superpowers, misc, nextflow (private/local ones marked as such)
- [ ] Snapshot of the table
