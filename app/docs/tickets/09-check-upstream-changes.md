# 09: Check for upstream changes

**What to build:** `skillctl upstream check [COLLECTION]` compares every skill with GitHub provenance to its upstream and shows a dry-run change set: new upstream skills, and per skill added / modified / deleted files; orphaned and unavailable upstreams are shown, never fatal.

**Blocked by:** 07

**Status:** done

- [x] Pure change-set planner tested with literal file trees
- [x] Orphaned skills flagged, not scheduled for deletion
- [x] One unreachable source does not abort the check
- [x] Summary table + per-skill detail snapshot
