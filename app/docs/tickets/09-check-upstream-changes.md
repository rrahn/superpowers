# 09: Check for upstream changes

**What to build:** `skillctl upstream check [COLLECTION]` compares every skill with GitHub provenance to its upstream and shows a dry-run change set: new upstream skills, and per skill added / modified / deleted files; orphaned and unavailable upstreams are shown, never fatal.

**Blocked by:** 07

**Status:** ready-for-agent

- [ ] Pure change-set planner tested with literal file trees
- [ ] Orphaned skills flagged, not scheduled for deletion
- [ ] One unreachable source does not abort the check
- [ ] Summary table + per-skill detail snapshot
