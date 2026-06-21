---
name: skill-extraction
description: >
  Copilotception methodology for extracting reusable knowledge into SKILL.md files after
  completing non-obvious tasks. Use when: (1) you solved something that required significant
  investigation, (2) a fix was non-obvious from documentation alone, (3) you discovered a
  project-specific pattern worth preserving for future sessions. Also covers skill improvement,
  description trigger testing, and workflow-to-skill conversion. Skills saved mid-session
  are NOT available until the next opencode session due to Instance.state caching.
alwaysApply: false
tier: 5
user-invocable: true
---

# Skill Extraction — Copilotception for opencode

Continuous learning system: extract hard-won knowledge into skill files so future sessions
start with it already available.

---

## When to Extract

1. **Non-obvious solutions** — Debugging, workarounds, or fixes requiring significant investigation.
2. **Project-specific patterns** — Conventions, configs, or architectural decisions not documented elsewhere.
3. **Tool integration knowledge** — Using a tool, library, or API in ways docs don't cover well.
4. **Error resolution** — Specific errors and their actual root causes, especially when the message is misleading.
5. **Workflow optimizations** — Multi-step processes that can be streamlined.
6. **Blockades** — You needed several cycles to figure out why the codebase or tools were blocking you in executing your task.

## Quality Gates (All Must Pass)

- **Reusable**: Will this help future tasks, not just this one instance?
- **Non-trivial**: Did this require actual discovery, not just a docs lookup?
- **Specific**: Can you describe exact trigger conditions (error messages, symptoms)?
- **Verified**: Has this solution actually worked, not just theoretically?

If any gate fails, do not extract.

---

## Skill Placement

| Location | Path | Use for |
|----------|------|---------|
| Project | `.opencode/skills/<name>/SKILL.md` | Project-specific knowledge; version-controlled with the repo |
| Global | `~/.opencode/skills/<name>/SKILL.md` | Cross-project patterns; personal tooling knowledge |

**Rule of thumb**: If the knowledge depends on this codebase's conventions, use project-level.
If it would help in any project (e.g., a Docker networking fix, a shell pattern), use global.

---

## Writing Principles

Follow these when drafting any SKILL.md:

1. **Explain the why, not just the what.** Help agents understand the reasoning behind each step so they can adapt when conditions vary. "Run `--frozen` because CI has no lock file write access" is better than "Run `--frozen`."
2. **Use imperative form.** "Run X", "Check Y" — not "You should run X" or "X can be run."
3. **Include concrete examples.** Show actual commands with actual parameter values. Abstract instructions produce abstract results.
4. **Avoid ALWAYS/NEVER/MUST in all caps.** Explain the reasoning instead — agents follow principles better than rigid rules.
5. **Front-load the common case.** Put the 80% workflow first. Edge cases, caveats, and rare scenarios go later or in `references/`.

---

## Size Guidelines & Progressive Disclosure

### Core SKILL.md: aim for under 500 lines

Everything in SKILL.md is injected into context on every invocation. Every line costs tokens. If a section is only relevant ~20% of the time, move it out of the core file.

~500 lines of markdown ≈ 2,000–3,000 tokens, roughly 2–5% of a typical context window — noticeable but not devastating. Beyond 500 lines, signal-to-noise drops sharply.

### The `references/` overflow pattern

When a skill needs detailed lookup tables, edge-case documentation, or domain reference material, place it in a `references/` subdirectory:

```
skills/<name>/
├── SKILL.md              # ≤500 lines: core workflow, always loaded
└── references/
    ├── error-codes.md    # Detailed error lookup table
    └── edge-cases.md     # Rare scenarios and workarounds
```

**How OpenCode handles this**: When a skill is loaded, OpenCode lists up to 10 non-SKILL.md files in the skill directory (recursing into subdirectories) and surfaces them in a `<skill_files>` block. File contents are NOT auto-loaded — the agent must explicitly `read` them.

**The SKILL.md must instruct the agent** when and why to read each reference file:

```markdown
## Detailed Error Codes
For the full error code lookup table, read `references/error-codes.md`.

## Edge Cases
If the standard workflow fails with an unexpected state, read `references/edge-cases.md`.
```

Without explicit pointers, the agent sees the file listing but has no reason to open them.

### Guidelines

- Keep total files per skill directory under 10 (the listing is capped and sampled).
- Put the 80% workflow in SKILL.md. Put the 20% reference material in `references/`.
- For reference files over 300 lines, include a table of contents at the top.

---

## Description Writing Rules

The `description` frontmatter field is the primary trigger for skill activation. If it is vague, the skill will never be used. If it is too broad, it will fire on irrelevant tasks.

**Rules:**

- **Be pushy.** Slightly over-trigger rather than under-trigger. Instead of "Fix Docker networking issues", write "Fix Docker networking issues including bridge conflicts, port binding failures, and container DNS resolution. Use when: containers can't reach each other, `docker-compose up` fails with port-in-use errors, or DNS lookups inside containers return NXDOMAIN."
- **Include trigger phrases.** List the user phrases, error messages, and data types that should activate the skill.
- **Keep under ~100 words.** The description is always in context for every agent — bloated descriptions waste tokens across every session.
- **Use `>` YAML folding** for multi-line descriptions.

---

## Extraction Process

### Step 1: Check for Existing Skills

```sh
find .opencode/skills/ ~/.opencode/skills/ -name 'SKILL.md' -exec head -5 {} + 2>/dev/null
grep -rl "keyword" .opencode/skills/ ~/.opencode/skills/ 2>/dev/null
```

| Found | Action |
|-------|--------|
| Nothing related | Create new skill |
| Same trigger + same fix | Update existing (bump version) |
| Same trigger, different cause | Create new, add "See also" cross-links |
| Partial overlap | Add variant subsection to existing skill |

### Step 2: Identify the Knowledge

- What was the problem or task?
- What was non-obvious about the solution?
- What would someone need to know to solve this faster next time?
- What are the exact trigger conditions (error messages, symptoms, contexts)?

### Step 3: Research Best Practices

Search the web for current information when the topic involves external technologies or tools.
Skip for purely project-internal patterns.

### Step 4: Write the Skill File

```markdown
---
name: descriptive-kebab-case-name
description: >
  Precise, pushy description of what problem this solves and when to use it.
  Use when: (1) specific trigger scenario, (2) exact error message seen,
  (3) observable symptom. Include key technologies and frameworks.
  Keep under 100 words.
metadata:
  version: "1.0"
  sources: "https://relevant-docs-url"
---

# Skill Name — Human Readable Title

## Problem

Clear description of the problem. What pain point does this solve? Why is it non-obvious?

## Trigger Conditions

- Exact error message: `ErrorType: specific message text`
- Observable symptom or behavior
- Environmental condition (framework version, tool, platform)

## Solution

1. First action — with rationale for why this step matters
2. Second action — with code example if applicable
3. Third action — verification command

## Verification

1. Expected output or behavior
2. Commands to run for validation

## Notes

- Edge cases or limitations
- When NOT to use this approach
- See also: `related-skill-name`

## References

- [Source](https://url) — Brief description
```

**Frontmatter rules:**

- `name`: Lowercase alphanumeric with hyphens only. Descriptive: `nextjs-ssr-errors`, `docker-compose-port-conflict`. Never generic: `fix-errors`.
- `description`: Pushy, trigger-ready, under 100 words, with `>` YAML folding. Must include exact trigger conditions and error messages — this is what the skill-loader scans to determine relevance.
- `metadata.version`: SemVer — patch=typos, minor=new scenario, major=breaking change.
- `metadata.sources`: Comma-separated authoritative reference URLs.

### Step 5: Save the Skill

```sh
# Project-level (codebase-specific):
mkdir -p .opencode/skills/skill-name

# Global (cross-project):
mkdir -p ~/.opencode/skills/skill-name

# Then write SKILL.md into that directory
# If needed, create references/ with supplementary files
```

### Step 6: Validate

**Structural checklist:**

- [ ] `name` is lowercase alphanumeric with hyphens
- [ ] `description` includes specific error messages or trigger phrases
- [ ] `description` is under 100 words and uses pushy language
- [ ] Problem statement is clear and concise
- [ ] Trigger conditions are exact and searchable
- [ ] Solution uses imperative voice with rationale for each step
- [ ] Concrete examples with actual commands and parameter values
- [ ] No sensitive information (credentials, internal URLs, hostnames)
- [ ] Does not duplicate existing skills or official documentation
- [ ] Core SKILL.md is under 500 lines
- [ ] Any `references/` files are explicitly pointed to from the body
- [ ] Total files in skill directory are under 10

**Description trigger testing:**

Generate 5 queries that SHOULD trigger and 5 that SHOULD NOT:

> **Should trigger:**
> 1. "[exact user phrasing]" — matches because [reason]
> 2. "[different phrasing, same intent]" — matches because [reason]
> 3. "[includes a specific error message]" — matches because [reason]
> 4. "[casual/abbreviated version]" — matches because [reason]
> 5. "[related but different angle]" — matches because [reason]
>
> **Should NOT trigger:**
> 1. "[near-miss, shares keywords]" — doesn't match because [reason]
> 2. "[same domain, different problem]" — doesn't match because [reason]
> 3. "[superficially similar]" — doesn't match because [reason]
> 4. "[different tool, same symptom]" — doesn't match because [reason]
> 5. "[too broad/generic]" — doesn't match because [reason]

Review the description against these. Adjust if any should-trigger queries wouldn't match or any should-not queries would false-positive.

> ⚠️ **Session boundary**: Skills written mid-session are NOT loaded until the next opencode
> session. Inform the user: "Skill saved — will be active from your next session."

---

## Improving an Existing Skill

Not every problem requires a new skill. Sometimes an existing skill underperforms and needs iteration.

### Diagnostic Table

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Skill doesn't trigger | Description is too vague or narrow | Expand with more trigger phrases, error messages, and contexts |
| Agent skips steps | Workflow lacks explicit sequencing | Add numbered step-by-step with checkpoints |
| Agent uses wrong approach | Missing "why" explanations | Add rationale for each decision point |
| Skill is too long / context-heavy | Everything crammed in one file | Extract reference material to `references/` |
| Outdated information | Version or tool drift | Verify current state, update content, bump version |
| Too narrow / overfitted | Written for one specific case | Generalize the principle, add variant examples |
| Wrong tool referenced | Tool renamed or deprecated | Verify tool still exists, update name and parameters |
| Missing error handling | Only covers the happy path | Add common failure modes and recovery steps |

### Iteration Loop

1. Diagnose the problem using the table above
2. Apply the fix to the SKILL.md
3. Re-run the structural checklist and description trigger testing
4. Get user feedback (or test with realistic prompts)
5. Repeat until no meaningful improvements remain

### Principle: Generalize, Don't Overfit

When improving based on a specific failure:
- Understand **why** the failure happened, not just **what** failed
- Write instructions that address the root cause, not the symptom
- Avoid adding rigid rules for one-off edge cases — explain the principle instead
- Remove instructions that aren't pulling their weight (if an instruction doesn't change agent behavior, cut it)

---

## Workflow → Skill Conversion

When converting a completed workflow (from a session or conversation) into a skill, capture:

- [ ] **The sequence** — what steps were performed and in what order
- [ ] **The tools** — which commands, APIs, or tool calls were used (exact names)
- [ ] **The domain knowledge** — what the agent needed to know that wasn't in documentation
- [ ] **The errors** — what went wrong and how it was fixed (these become Trigger Conditions)
- [ ] **The rationale** — why each step was done, not just what
- [ ] **The corrections** — any mid-course adjustments or retries (these reveal edge cases)
- [ ] **The output** — what the final deliverable looked like (format, location, structure)

The `skill-builder` agent can read session history directly from the OpenCode database
(`opencode export <sessionID>`) to extract this information without the calling agent
needing to summarize.

---

## Anti-Patterns

- **Over-extraction**: Not every task deserves a skill. Mundane solutions don't need preservation.
- **Vague triggers**: "Helps with Python problems" won't surface when needed. Use exact error messages.
- **Unverified solutions**: Only extract what actually worked.
- **Documentation duplication**: Link to official docs; add only what's missing from them.
- **Stale knowledge**: Include version/date context so skills can be deprecated when tools change.
- **All-caps rigid rules**: "NEVER do X" is less effective than explaining why X causes problems.
- **Bloated skills**: If the SKILL.md is over 500 lines, split into core + `references/`.

---

## Self-Check (After Every Significant Task)

1. "Did I spend meaningful time investigating something?"
2. "Would future-me benefit from having this documented?"
3. "Was the solution non-obvious from documentation alone?"

If yes to any, run this extraction process now.
