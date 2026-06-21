---
name: beads-workflow
description: >
  Managing issues with bd (beads) — epics, child issues, dependencies, swarm coordination,
  agent workflows, research-backed bead writing, and multi-project Dolt server isolation.
  Use when: creating epics, grouping issues, managing blocking deps, coordinating parallel
  work, writing beads after investigation/research, diagnosing stale/missing issues after
  Dolt port collisions, or setting up per-project beads infrastructure. Covers `bd`, `bdui`,
  and `dolt sql-server` lifecycle. Trigger on: "bd list shows wrong issues", "beads data loss",
  "Dolt port conflict", "issues missing from bd", "stale beads database", "write beads from
  research", "create beads after investigation", "research-backed issues".
markers:
  - .beads/
globs:
  - "**/.beads/**"
alwaysApply: false
tier: 4
metadata:
  version: "3.0.0"
  sources: "https://docs.dolthub.com/sql-reference/server/configuration"
user-invocable: true
---

# Beads (bd) Complete Workflow Reference

bd is a dependency-aware issue tracker backed by Dolt (a version-controlled MySQL-compatible database).
Issues are linked via typed dependencies forming a DAG.

---

## Issue Types

| Type      | Purpose                                                       |
| --------- | ------------------------------------------------------------- |
| `bug`     | Something broken                                              |
| `feature` | New functionality                                             |
| `task`    | Work item (tests, docs, refactoring)                          |
| `epic`    | A goal/theme decomposed into child issues (NOT a single task) |
| `chore`   | Maintenance (dependencies, tooling)                           |

## Issue Statuses

`open`, `in_progress`, `blocked`, `deferred`, `closed`

## Priorities

`0` Critical, `1` High, `2` Medium (default), `3` Low, `4` Backlog

---

## Creating Issues

```bash
# Simple issue
bd create "Fix the bug" -d "Details" -t bug -p 1 --json

# With labels
bd create "Add feature" -d "Details" -t feature -p 2 -l "permissions,subagent" --json

# Discovered while working on another issue (provenance link, non-blocking)
bd create "Found related bug" -d "Details" -p 1 --deps discovered-from:<source-id> --json
```

---

## Epics and Child Issues

An epic represents a goal decomposed into concrete child issues. Children are linked via the `parent-child` dependency type.

### Creating an epic with children

```bash
# Create the epic
bd create "Auth system overhaul" -t epic -p 1 --json
# Returns ID like opencode-abc

# Create children (auto-numbered: opencode-abc.1, opencode-abc.2, ...)
bd create "Design login UI" -t task -p 1 --parent opencode-abc --json
bd create "Backend validation" -t bug -p 0 --parent opencode-abc --json
bd create "Integration tests" -t task -p 2 --parent opencode-abc --json
```

### Adding existing issues to an epic retroactively

```bash
bd dep add <issue-id> <epic-id> --type parent-child
```

### Viewing epic state

```bash
bd children <epic-id> --json          # List children of one epic
bd epic status --json                 # Completion status of all epics
bd epic close-eligible                # Auto-close epics where all children are done
bd epic close-eligible --dry-run      # Preview without closing
```

### Epic rules

- Children are **parallel by default** — add `blocks` deps between them for ordering
- `bd ready` respects `parent-child` blocking: children of a blocked epic don't surface
- `discovered-from` is **NOT** epic membership — it's a provenance annotation
- Use `--parent` at creation or `bd dep add --type parent-child` for epic grouping

---

## Dependencies

bd has 10 dependency types. Choose the right one.

### Blocking types (affect `bd ready`)

| Type           | Semantics                               | Usage                              |
| -------------- | --------------------------------------- | ---------------------------------- |
| `blocks`       | B cannot start until A closes           | `bd dep add B A` (default type)    |
| `parent-child` | Children blocked when parent is blocked | `bd create ... --parent <epic-id>` |
| `until`        | B waits for a time/condition on A       | Deferred work                      |

### Non-blocking types (graph annotations only)

| Type              | Semantics                          |
| ----------------- | ---------------------------------- |
| `discovered-from` | Found during work on another issue |
| `caused-by`       | Root cause link                    |
| `related`         | Informational link                 |
| `tracks`          | Tracks progress of another issue   |
| `validates`       | Test/verification link             |
| `supersedes`      | Replaces another issue             |
| `relates-to`      | Bidirectional relation             |

### Dependency commands

```bash
# Add blocking dep (A blocks B — B depends on A)
bd dep add <blocked-id> <blocker-id>
bd dep add <blocked-id> <blocker-id> --type blocks  # explicit, same thing

# Add non-blocking link
bd dep add <issue-id> <source-id> --type discovered-from
bd dep add <issue-id> <cause-id> --type caused-by

# List deps
bd dep list <issue-id> --json                    # what blocks this issue
bd dep list <issue-id> --direction=up --json     # what this issue blocks

# Visualize
bd dep tree <issue-id>                           # dependency tree (down)
bd dep tree <epic-id> --direction=up             # dependent tree (up)
bd dep tree <id> --direction=both                # full graph

# Safety
bd dep cycles                                    # detect cycles
```

---

## Swarm (Parallel Agent Work on Epics)

`bd swarm` coordinates parallel work on an epic's child DAG. It computes which children are unblocked (the "ready front") for agent parallelism.

```bash
# Validate epic structure before swarming
bd swarm validate <epic-id> --json

# Create a swarm from an epic
bd swarm create <epic-id> --json

# Check swarm status (completed/active/ready/blocked)
bd swarm status <epic-id> --json

# List all swarms
bd swarm list --json
```

---

## Multi-Project Dolt Isolation

If `bd list` shows wrong or missing issues, you likely have a Dolt port collision between
projects. Read `references/dolt-isolation.md` for diagnosis, prevention, and recovery.

---

## Reading Issues

```bash
bd ready --json                      # Unblocked work — check BEFORE asking "what should I work on?"
bd list --json                       # All open issues regardless of blockers — full inventory
bd show <id> --json                  # Full details including description, deps, and history
bd search "keyword" --json           # Text search across titles and descriptions
bd children <epic-id> --json         # Children of a specific epic — check epic progress
bd dep tree <id>                     # Dependency graph — use to understand blockers
```

---

## Updating and Closing

```bash
bd update <id> --claim --json        # Assign to yourself — do this before starting work
bd update <id> --priority 0 --json   # Escalate priority (0=Critical) when impact discovered
bd close <id> --reason "Done" --json # Close with reason — stored for audit trail
bd reopen <id> --json                # Reopen if the fix was incomplete
```

---

## Agent Workflow

1. **Check ready work**: `bd ready --json`
2. **Claim**: `bd update <id> --claim --json`
3. **Work on it**: implement, test, document
4. **Discover new work?**
   - Child of current epic: `bd create "Sub-task" -d "..." -p 1 --parent <epic-id> --json`
   - Found during work: `bd create "Found bug" -d "..." -p 1 --deps discovered-from:<source-id> --json`
5. **Order work**: `bd dep add <blocked> <blocker>` if one issue must finish before another
6. **Complete**: `bd close <id> --reason "Done" --json`
7. **Check epic**: `bd epic status --json`

---

## Writing Research-Backed Beads

After a deep investigation or research session, beads should embed the findings directly —
not just reference them. An implementing agent should be able to start work immediately
without re-doing the research.

### The Pipeline

1. **Survey** the codebase broadly (grep, directory listings, key files)
2. **Deep-dive** on specific areas (verify assumptions against actual source code)
3. **Gap analysis** — compare research findings against existing beads:
   - Build a coverage table: finding → bead ID or "NOT COVERED"
   - Check for redundancy (beads requesting features that already exist)
   - Check for staleness (bead descriptions that contradict findings)
4. **Write beads** only for confirmed gaps, with research embedded

### What a Good Bead Contains

| Section | Purpose |
|---------|---------|
| **What to implement** | Concrete code or pseudocode — copy-pasteable when possible |
| **Why this approach** | Design decision with alternatives considered |
| **Exact signatures/types** | From verified source — symbol names, not just line numbers |
| **Where in the codebase** | Symbol names first (survive refactoring), line numbers second |
| **Testing instructions** | Specific scenarios, not just "write tests" |
| **Verification checklist** | Assertions to confirm before starting (codebase drifts) |
| **Research references** | Pointers to scratch/ artifacts with section numbers |
| **Key files** | List of files to read before starting |

### Key Principles

- **Verify before you write.** Every assumption in a bead should be confirmed against source code. Beads based on unverified assumptions waste agent time.
- **Embed snippets, don't just reference.** Every implementation bead MUST include a `## What To Implement` snippet — concrete starter code, a function skeleton with type hints, or the actual diff (additions/deletions). Prose-only descriptions ("consider adding X") fail this rule. If the snippet cannot be written because the design itself is ambiguous, resolve the ambiguity in design.md before creating the bead.
- **Anchor by symbol, then by line.** `## Exact Signatures / Types` and `## Where In The Codebase` cite the symbol name first (survives refactoring) and `file:line` second (rots quickly).
- **Wire dependencies.** Think about what must complete before each task can start. Use `bd dep add`. A flat epic with no edges looks parallel when it isn't.
- **Skip speculative phases.** If a phase depends on unproven assumptions, don't decompose it into beads yet. Keep it as an epic description and plan it later.
- **Verification checklists are mandatory.** Every bead that references specific code must have `- [ ] Confirm [symbol] still exists at [file]` lines. Codebases drift between research and implementation. When a checklist item depends on runtime behavior the codebase can't reveal (library API semantics, race conditions, environment-specific results), the bead should explicitly direct the implementor to delegate to `@experiment-runner` rather than guess.

For the full bead anatomy template, the implementor's compact, before/after examples,
gap analysis workflow, and detailed anti-patterns, read `references/research-backed-beads.md`.

---

## Dolt Backup / Remote Push

Beads databases are backed up via Dolt's native push to AWS S3. Auto-push is enabled by default
(`dolt.auto-push = true`, debounced 5 min). Legacy JSONL git backup is disabled.

For S3 remote setup, AWS credential configuration, auto-push mechanics, and troubleshooting,
read `references/dolt-backup.md`.

---

## References

- [Dolt SQL Server Configuration](https://docs.dolthub.com/sql-reference/server/configuration) — listener port, host, TLS settings
- `bd --help` — full command reference; `bd <command> --help` for subcommand details
- `bdui --help` — beads UI server options (host, port)
- `bd dolt --help` — Dolt server lifecycle, configuration, and version control commands

---

## Common Mistakes

| Mistake                                               | Correction                                                  |
| ----------------------------------------------------- | ----------------------------------------------------------- |
| Using `discovered-from` to group issues under an epic | Use `--parent` or `bd dep add --type parent-child`          |
| Creating an epic with no children                     | An epic must be decomposed; create children with `--parent` |
| Not using `--json` flag                               | Always use `--json` for agent/programmatic use              |
| Forgetting to check `bd ready`                        | Always check before asking "what should I work on?"         |
| Creating markdown TODO lists                          | Use bd for all task tracking                                |
| Running multiple projects on the same Dolt port       | Assign unique ports per project via justfile + `bd dolt set port` |
| Not verifying `bd list` count after server restart    | Compare `bd list` count against on-disk Dolt query          |
| Writing beads without verifying assumptions           | Confirm every code reference against actual source first    |
| Flat epics with no dependency edges                   | Use `bd dep add` to express ordering between children       |
| Beads with file references but no verification checklist | Add `- [ ] Confirm [symbol] still exists at [file]` lines |
