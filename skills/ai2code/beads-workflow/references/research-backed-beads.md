# Writing Research-Backed Beads — Detailed Guide

Read this when writing beads after a deep research/investigation session. This reference
provides the full bead anatomy template, a real before/after comparison, the gap analysis
workflow, and anti-patterns to avoid.

---

## Table of Contents

1. [The Research-to-Bead Pipeline](#the-research-to-bead-pipeline)
2. [Bead Anatomy Template](#bead-anatomy-template)
3. [Before & After: Bad Bead vs Good Bead](#before--after-bad-bead-vs-good-bead)
4. [Gap Analysis Workflow](#gap-analysis-workflow)
5. [Cross-Repo Coordination](#cross-repo-coordination)
6. [Anti-Patterns in Detail](#anti-patterns-in-detail)

---

## The Research-to-Bead Pipeline

Research and bead creation are distinct phases. Do not skip steps.

### Phase 1: Survey (broad)
- Explore both codebases (grep, directory listings, README files)
- Identify the key files, interfaces, and abstractions
- Persist findings in a scratch directory (e.g., `scratch/survey.md`)

### Phase 2: Deep-Dive (targeted)
- Use tools like `edith explore` or `edith ask` for focused analysis
- Verify assumptions against actual source code (exact file, line, symbol)
- Produce detailed technical artifacts (hook mappings, type signatures, etc.)
- Persist findings (e.g., `scratch/deep-dive-hooks.md`)

### Phase 3: Gap Analysis (compare)
- Dump all existing beads: `bd children <epic> --json`, `bd show <id>`
- Create a coverage table: research finding → existing bead or "NOT COVERED"
- Identify redundant beads (features that already exist but beads assume are missing)
- Identify missing beads (research findings with no bead)
- Identify stale beads (descriptions that contradict research findings)
- Persist the gap analysis (e.g., `scratch/beads-vs-research.md`)

### Phase 4: Write Beads (informed)
- Create beads only for confirmed gaps
- Embed research findings directly into bead descriptions
- Add verification checklists for codebase drift
- Wire dependency edges between children
- Skip phases that are too speculative to decompose

---

## Bead Anatomy Template

A well-written research-backed bead has these sections:

```
TITLE: [Verb] [specific thing] [where/for what]
  Good:  "Add shell.env hook for GasTown environment variable injection"
  Bad:   "Fix environment variables"

DESCRIPTION:

## What To Implement
[Concrete starter code — copy-pasteable. Show one of: (a) the actual diff
 (additions/deletions in unified format), (b) a function skeleton with type
 hints and a docstring stub, or (c) the new module shape with public symbols.
 Prose-only descriptions ("consider implementing X") FAIL this section —
 the implementor should be able to paste this as the starting draft.
 If you cannot write the snippet because the design is ambiguous, the design
 needs to be tightened before the bead is created.]

## Why This Approach
[Design decision with alternatives considered. Why option A over option B.]

## Exact Signatures / Types
[From verified source — function signatures, type definitions, hook interfaces.
 Include the source file and symbol name, not just line numbers.]

## Where In the Codebase
[Symbol names first (survive refactoring), line numbers second (rot quickly).
 Example: "DiscoverTargets() in internal/hooks/config.go (~L386)"]

## Testing
[Specific test scenarios, not just "write tests".
 Example: "Start OpenCode session, have AI run 'env | grep GT_',
 verify all GT_ variables appear."]

## VERIFICATION CHECKLIST (codebase may have drifted — verify before starting)
- [ ] Confirm [symbol] still exists at [file] with [expected behavior]
- [ ] Check if [assumption from research] is still true
- [ ] Verify [dependency] has been completed
- [ ] Search for [pattern] to confirm no one else has fixed this
- [ ] If any item above cannot be resolved by reading the codebase alone
      (runtime semantics, library API behavior, environment-specific results),
      delegate to @experiment-runner before coding

## Research References
[Pointers to scratch/ artifacts with section numbers.
 Example: "scratch/README.md Section 7 — complete plugin example"]

KEY FILES: [list of files to read before starting]
```

### The Implementor's Compact

The bead anatomy above is a contract with the *consumer* of the bead (typically
the spec-implementor agent). When a bead carries the full anatomy, the consumer
agrees to:

1. **Walk the Verification Checklist first.** Confirm every cited symbol, signature,
   and assumption is still true *before* writing code. Codebases drift; the snippet
   may be based on a stale read.
2. **Treat `## What To Implement` as a starter draft, not a verbatim contract.**
   If verification proves the snippet is stale, diverge — but record the divergence
   in the implementation report so a reviewer can adjudicate it. Silent divergence
   looks like spec drift to the next reader.
3. **Escalate to `@experiment-runner`** when a checklist item depends on runtime
   behavior that reading alone cannot answer. Do not guess and do not silently
   skip the item.
4. **If the snippet is wrong, say so.** When implementation reveals the bead's
   snippet was based on a faulty assumption, flag it in the report so the spec
   can be corrected post-hoc.

This compact is what makes the anatomy useful: an anchor strong enough to guide
the implementor, loose enough to absorb legitimate codebase drift.

---

## Before & After: Bad Bead vs Good Bead

### Bad Bead (written without research)

```
TITLE: "Accept OPENCODE_SESSION_ID in session ID resolution"

DESCRIPTION:
Add OPENCODE_SESSION_ID as a fallback env var for session ID resolution.
Consider a generic GT_RUNTIME_SESSION_ID.

FILE: internal/runtime/runtime.go
```

Problems:
- No code snippet showing what to change
- No mention of WHERE in the file the change goes
- No mention of the 3 other locations that also need changes
- No verification checklist — agent doesn't know if this was already fixed
- No dependency on the preset update that must happen first
- "Consider" is vague — who decides? The implementing agent has no context

### Good Bead (written after research)

```
TITLE: "Accept OPENCODE_SESSION_ID in session ID resolution"

DESCRIPTION:
## What To Implement

CURRENT: SessionIDFromEnv() in internal/runtime/runtime.go falls back to
CLAUDE_SESSION_ID unconditionally for all agents. Prime session resolution
in internal/cmd/prime_session.go also checks CLAUDE_SESSION_ID.

DELIVERABLES:
1. Add OPENCODE_SESSION_ID to the session ID env var resolution chain
2. Gate CLAUDE_SESSION_ID fallback behind GT_AGENT == "claude"
3. Use the preset's SessionIDEnv field for agent-specific resolution
4. Depends on OpenCode preset update bead for SessionIDEnv population

## Why This Approach
Each agent runtime exports its session ID in its own env var (Claude uses
CLAUDE_SESSION_ID, OpenCode uses OPENCODE_SESSION_ID). The resolution chain
should check the agent-specific var first, then fall back to a generic
GT_RUNTIME_SESSION_ID, then finally check CLAUDE_SESSION_ID only if the
agent is Claude.

## VERIFICATION CHECKLIST (codebase may have drifted — verify before starting)
- [ ] Confirm SessionIDFromEnv() in runtime.go still has CLAUDE_SESSION_ID
- [ ] Confirm prime_session.go ~L33-55 still checks CLAUDE_SESSION_ID
- [ ] Check if preset SessionIDEnv field is used in the resolution chain
- [ ] Verify OpenCode preset now has SessionIDEnv: "OPENCODE_SESSION_ID"

KEY FILES: internal/runtime/runtime.go, internal/cmd/prime_session.go,
           internal/cmd/prime.go, internal/config/agents.go
```

The good bead gives an implementing agent everything it needs to start
immediately without re-doing the research.

---

## Gap Analysis Workflow

When comparing research against existing beads:

### Step 1: Dump existing beads
```bash
bd children <epic-id> --json | python3 -c "
import sys,json
for d in json.load(sys.stdin):
    print(f'{d[\"id\"]} [{d[\"status\"]}] p{d[\"priority\"]}: {d[\"title\"]}')
"
bd dep tree <epic-id> --direction=both
```

### Step 2: Build coverage table

| Research Finding | Severity | Covered By | Gap? |
|-----------------|----------|-----------|------|
| DiscoverTargets() hardcodes .claude/ | Critical | NOT COVERED | Yes |
| Session ID env var fallback | Important | qnp.2 (partial) | Partial |
| ... | ... | ... | ... |

### Step 3: Check for redundancy

Ask for each existing bead: "Does our research show this is already solved?"

Example from real work: An epic claimed OpenCode was "MISSING" two plugin events
(PreToolUse and UserPromptSubmit). Research proved both already existed as
`tool.execute.before` and `chat.message` hooks. 3 of 4 children were closed
as redundant — avoiding ~3-4 weeks of wasted development.

### Step 4: Produce recommendations
- New beads to create (with full anatomy)
- Existing beads to update (quote specific discrepancies)
- Beads to close as redundant (with evidence)
- Dependency edges to add

---

## Cross-Repo Coordination

When work spans multiple repos with separate beads databases:

1. **Each repo owns its own beads.** Don't create beads in repo A for work in repo B.
2. **`bd dep add` cannot cross Dolt databases.** Use `--type related` links with the
   external bead ID in the description, but accept that cross-repo deps are informal.
3. **Create a coordination document** (e.g., `scratch/coordination.md`) that maps
   cross-repo dependencies in human-readable form:
   ```
   gastown-qnp.2 (session ID) ←→ opencode-krh.3 (OPENCODE_SESSION_ID env var)
   gastown-i2y.3 (guards)     ←→ opencode tool.execute.before hook (already exists)
   ```
4. **The human is the coordination layer.** Agents in each repo work independently;
   the human reconvenes, checks progress, and decides what's next.

---

## Anti-Patterns in Detail

### 1. Assumption-Based Beads
Writing beads based on what you THINK the codebase looks like, not what you VERIFIED.
The opencode-krh epic assumed hooks were missing that actually existed.
**Fix**: Verify every assumption against source code before writing beads.

### 2. Flat Epic (No Dependency Edges)
All children are siblings with no `blocks` relationships. Looks parallel but actually
has implicit ordering. An agent picks up a downstream task before its prerequisite.
**Fix**: Think about what must complete before each task can start. Use `bd dep add`.

### 3. Premature Decomposition
Writing detailed beads for work that depends on unproven assumptions. If Phase 2
hasn't proven the plugin works, detailed Phase 4 beads are fiction.
**Fix**: Plan in detail only 1-2 phases ahead. Keep future phases as epic descriptions.

### 4. Investigation Beads at Low Priority
Framing concrete work as "investigation" at P3 when research already identified
specific deliverables.
**Fix**: If research produced code snippets or specific changes, it's a task, not an
investigation. Set priority based on impact, not uncertainty.

### 5. Missing Verification Checklists
Beads with file references but no checklist to confirm those references are still valid.
By the time an agent picks up the bead, the codebase may have drifted.
**Fix**: Every bead that references specific code must have a verification checklist.

### 6. Vague Descriptions
"Consider implementing X" or "Investigate Y approach" — who decides? When?
**Fix**: Make a decision in the bead. State what to do, not what to consider.
If you genuinely can't decide, state the options and the criteria for choosing.
