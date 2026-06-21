---
name: context-protection
description: >
  Context window protection protocol — prevents auto-compaction infinite loops (OpenCode
  bug #15533). Covers orchestrators, delegating workers, and leaf nodes. Load when:
  spawning child agents via task(), starting a new task after compaction, you see a summary
  message as your first context, or context usage is approaching 70%. Trigger phrases:
  "compaction loop", "context too large", "summary message", "spawning child agent".
alwaysApply: true
tier: 5
metadata:
  version: "1.0"
user-invocable: true
---

# Context Protection Protocol

OpenCode has a known bug ([#15533](https://github.com/anomalyco/opencode/issues/15533)) where auto-compaction creates an infinite loop that **permanently hangs** the agent and its entire parent chain. This skill defines the defense-in-depth protocol that prevents it.

---

## How Compaction Works (Why This Matters)

1. **Pruning** — Token-budget walk. Keeps the most recent ~40K tokens of tool outputs, erases older ones. The `"skill"` tool is exempt (`PRUNE_PROTECTED_TOOLS`) — skill reads are never pruned.
2. **LLM Summarization** — Everything that survived pruning is fed to an LLM that produces a structured summary (Goal, Instructions, Discoveries, Accomplished work, Relevant files). **No mechanism forces the summarizer to preserve any content verbatim.**
3. **System message** — The initial instruction block is **never compacted**. It survives every compaction event verbatim. This is the only compaction-proof channel.

**Failure mode**: After compaction, skill content read in earlier turns is diluted to something like _"Read project SKILL.md containing guidelines"_ — the agent knows the skill exists but has lost the actionable rules. Without a re-read trigger, it silently drifts to default behaviors.

---

## Protocol by Agent Type

### A. Pure Orchestrators

_Agents that ONLY coordinate — they have no file I/O tools enabled. Examples: `codebase-analyzer`, `spec-judge` (head), `spec-implementor-orchestrator`, `web-researcher`._

#### Core Rules

1. **You are an ORCHESTRATOR.** You do NOT read files, fetch URLs, grep, or run shell commands. Your child agents do ALL I/O. You spawn, synthesize, and report.
2. **Your ONLY tool is `task`.** Every other tool is disabled or forbidden. If you find yourself about to use a disabled tool, STOP — reformulate as a child agent task.
3. **Be concise.** Keep your own output lean — bullet points, structured tables, `file:line` references. Verbose prose fills your context.
4. **Stop early.** If you have enough information to answer, STOP. Do not spawn "one more child" for completeness.
5. **Batch children.** Never accumulate more than 3–4 child results before synthesizing. Synthesize in batches if you need more.
6. **Recite your pledge** before your first delegation and after every child returns:
   > _"I am an orchestrator. I do not perform I/O directly. I delegate to children and synthesize. I am monitoring my context usage."_

#### Hard Stop Rule

If you are about to read a file, grep for a symbol, or run a shell command:
1. **STOP IMMEDIATELY.**
2. **REFORMULATE** as a research question for the appropriate child agent.
3. **SPAWN A CHILD** instead.

#### Child Tier Selection (for codebase-analyzer orchestrator)

| Child | Model | Speed | Use When |
|-------|-------|-------|----------|
| `@codebase-analyzer-scout` | Haiku 4.5 | ⚡ Fast (~5–15s) | Simple lookups, file existence, symbol locations, config reads, imports |
| `@codebase-analyzer-standard` | Sonnet 4.6 | 🔄 Medium (~15–45s) | Module-level tracing, interface mapping, patterns (2–5 files) |
| `@codebase-analyzer-deep` | Opus 4.6 | 🐢 Slow (~45–120s) | Complex multi-file reasoning, edge cases, architectural inference (5+ files) |

**Start cheap.** Default to scout. Escalate only when the cheaper child cannot answer.

---

### B. Delegating Workers

_Agents that do their own I/O but also spawn child agents for research. Examples: `spec-implementor`, `spec-implementor-fix`, `spec-writer`, `developer`, `architect`, `documentation`, `dependencies`, `committer`, `spec-judge-opus`, `spec-judge-gemini`, `spec-judge-gpt`._

#### Core Rules

1. **Read surgically.** Read only the files you are modifying or the specific spec sections you need. Use line ranges — never read entire large files.
2. **Delegate heavy research.** If you need to understand patterns across 5+ files, explore module structure, or search the whole codebase — delegate to `@codebase-analyzer`. If you need web research — delegate to `@web-researcher`.
3. **Track your context.** After every file read and after every subagent return, mentally estimate your context usage. If you estimate you are past **65% capacity**, stop expanding scope and finalize with what you have.
4. **When invoking subagents**, prepend the Subagent Preamble (Section C below) to your task prompt so the child agent inherits context protection.
5. **Recite your pledge** before your first file read and after every subagent return:
   > _"Context check: I am monitoring my context usage. I will delegate research and finalize with available evidence."_

#### Context Budget Guidelines

| Action | Context Cost | Guidance |
|--------|-------------|----------|
| Reading a 50-line file section | Low | ✅ Do directly |
| Reading a 500-line file | High | ❌ Use line ranges or delegate |
| Running lint/test/format | Low (output only) | ✅ Do directly |
| Searching 10+ files for patterns | High | ❌ Delegate to `@codebase-analyzer` |
| Fetching a URL | High | ❌ Delegate to `@web-researcher` |
| Receiving a subagent report | Medium | ✅ But synthesize before spawning more |

---

### C. Subagent Preamble (For Delegating Workers to Prepend)

When invoking `@codebase-analyzer` or `@web-researcher`, **prepend this block** to your task prompt:

> **⚠️ CONTEXT PROTECTION — MANDATORY** (OpenCode bug [#15533](https://github.com/anomalyco/opencode/issues/15533))
>
> Auto-compaction WILL create an infinite loop. To prevent this:
> 1. **DELEGATE** all I/O to your child agents — never read/fetch/grep directly.
> 2. **Be concise** — bullet points with `file:line` references only.
> 3. **Stop early** — return as soon as you can answer.
> 4. **Batch** — never accumulate more than 3–4 child results before synthesizing.
> 5. **Pledge** before first delegation and after each child returns:
>    _"I am an orchestrator. I do not perform I/O directly. I delegate to children and synthesize. I am monitoring my context usage."_

This preamble ensures the middle-tier orchestrator agents (`codebase-analyzer`, `web-researcher`) inherit context protection when spawned by workers who do have direct I/O access.

---

### D. Leaf Nodes

_Agents that do the actual I/O — they have no children to delegate to. Examples: `codebase-analyzer-scout`, `codebase-analyzer-standard`, `codebase-analyzer-deep`, `web-search-child`._

#### Core Rules

1. **You are a worker, not an orchestrator.** You execute I/O directly. You do NOT spawn children.
2. **Read surgically.** Use `grep` to locate relevant lines first, then read only the specific line ranges you need (10–30 lines for scouts, up to 100 lines for standard/deep).
3. **Grep before read.** A targeted grep costs far less context than reading a file blind.
4. **Stop at capacity.** If you estimate you are past **60% context** (scout) or **70% context** (standard/deep), immediately proceed to documenting findings with what you have.
5. **Answer and return.** Once you have enough evidence, stop investigating. Do not explore "for completeness."
6. **Recite your pledge** before your first tool call:
   > _"I am a [scout/worker]. I read only what I need. I answer and return immediately."_

#### Step Budget

| Agent | Steps | Guidance |
|-------|-------|----------|
| Scout (Haiku) | 3 | One grep → one targeted read → report. If grep answers it, skip the read. |
| Standard (Sonnet) | 8 | Grep to orient → 2–4 targeted reads → report. Max 5 files. |
| Deep (Opus) | 8 | Grep to orient → targeted reads across 5+ files → deep reasoning → report. |

---

## Post-Compaction Recovery

**If you see a summary message as your first context** (instead of normal conversation history), you have been through a compaction event. Your earlier file reads and skill content may have been diluted.

**Immediately do the following:**

1. Re-read this skill: `skill({ name: "context-protection" })`
2. Re-read any project-specific skills referenced in your initial instructions.
3. Then resume your task with refreshed context.

This recovery step is triggered by the compaction-proof directive in your initial instruction block, which survives every compaction event.

---

## Summary: Defense-in-Depth Layers

| Layer | What | Survives Pruning? | Survives Summarization? | Purpose |
|-------|------|-------------------|------------------------|---------|
| **L0: Initial instruction block** | Compact 4-rule safety block + post-compaction re-read trigger | ✅ Always | ✅ Always (never compacted) | Immortal safety net |
| **L1: Skill tool read** | Full protocol (this file) loaded via `skill` tool | ✅ Protected (`PRUNE_PROTECTED_TOOLS`) | ❌ Diluted by summarizer | Detailed rules during normal operation |
| **L2: Post-compaction re-read** | System message triggers skill re-read after compaction | ✅ Always (system message) | ✅ Always (system message) | Restores L1 after compaction |
| **L3: Pledge recitation** | Periodic self-reminder during operation | n/a (agent output) | ❌ Summarized | Keeps rules salient between compactions |

**Worst case** (all layers except L0 fail): The 4 core rules in the initial instruction block still survive. The agent operates with reduced guidance but does not enter the infinite loop.
