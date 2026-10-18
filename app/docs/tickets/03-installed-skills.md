# 03: See installed skills

**What to build:** `skillctl installed` shows installations in the global scope and, inside a git repository, the local scope: name, scope, managed/unmanaged, symlink target, and whether the name exists in the catalog. `--scope` and `--json` supported.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Managed iff recorded in the scope lockfile (ADR-0002)
- [ ] Symlinked installations show their target
- [ ] Outside a git repository only the global scope is shown, with a hint
- [ ] Catalog unreachable degrades to an "unknown" in-catalog column, not a failure
- [ ] Text and SVG snapshot
