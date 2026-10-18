# 03: See installed skills

**What to build:** `skillctl installed` shows installations in the global scope and, inside a git repository, the local scope: name, scope, managed/unmanaged, symlink target, and whether the name exists in the catalog. `--scope` and `--json` supported.

**Blocked by:** 02

**Status:** done

- [x] Managed iff recorded in the scope lockfile (ADR-0002)
- [x] Symlinked installations show their target
- [x] Outside a git repository only the global scope is shown, with a hint
- [x] Catalog unreachable degrades to an "unknown" in-catalog column, not a failure
- [x] Text and SVG snapshot
