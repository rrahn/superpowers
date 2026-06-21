---
name: requirements-elicitation
description: >
  Requirements elicitation methodology — uncover root needs behind vague requests, transform
  abstract asks into testable acceptance criteria, map stakeholders, validate specs for
  completeness. This is the *upstream*
  methodology for @spec-writer and @goal-developer, not a replacement — it produces the
  inputs they consume. Load when: (1) a request is vague ("make it faster", "improve UX")
  and needs drill-down, (2) stakeholders disagree, (3) you're about to write a spec or PRD,
  (4) you need to convert abstract quality attributes into measurable NFRs, (5) auditing an
  existing spec for testability. Trigger phrases: "gather requirements", "user story",
  "acceptance criteria", "5 whys", "spec is vague", "stakeholder", "PRD", "out of scope",
  "what should this do".
alwaysApply: false
tier: 5
user-invocable: true
metadata:
  version: "1.1"
  sources: "https://github.com/rsmdt/the-startup/tree/main/plugins/team/skills/cross-cutting/requirements-elicitation, https://github.com/Yeachan-Heo/oh-my-codex/blob/main/skills/deep-interview/SKILL.md"
---

# Requirements Elicitation

Transform vague asks into clear, testable, prioritized specifications — drill past surface
requests to root needs, resolve stakeholder conflicts, and produce documentation that
aligns teams and survives review.

---

## When to Use

- Initial discovery: user describes a feature in one sentence and you need a real spec
- Vague quality attributes ("fast", "scalable", "intuitive") need concretization into NFRs
- Conflicting stakeholders: ops wants A, support wants B, exec sponsor wants C
- Documenting an existing process before changing it
- Validating a draft spec for completeness/testability before handing off to implementation

The output of this skill is the *input* to `@spec-writer` (which produces requirements.md +
design.md) or `@goal-developer` (which produces a structured goal file). If you have a clean
elicitation result, those agents have less to invent.

---

## Core Principles

**Always:**
- Drill past surface requests to root needs (5 Whys or equivalent) — solutions hide problems
- Transform every abstract requirement into at least one concrete, testable scenario
- Define explicit scope boundaries — what is in, out, deferred, and *pre-authorized* (decisions the implementer may make without checking back)
- Document all assumptions and open questions visibly — silence becomes assumed common ground
- Every requirement needs: ID, description, source, priority (MoSCoW), acceptance criteria
- Group requirements by feature area, not by stakeholder
- Include an explicit out-of-scope section to prevent scope creep

**Never:**
- Accept a solution-shaped request without uncovering the underlying need
- Leave "common sense" assumptions undocumented — "obvious" varies by stakeholder
- Add unrequested features beyond documented scope (gold plating)
- Use technical jargon when domain language is clearer
- Present requirements without acceptance criteria

---

## Workflow

### 1. Assess the situation

Identify:

- **What** is being specified (feature, system, integration, change)
- **Who** the stakeholders are — map them on interest × influence
- **What information exists** already vs. what is missing
- **Conflicts** — are stakeholder needs misaligned or just unclear?

**Order matters.** Elicit in this sequence even if the user volunteers later-stage detail first:

1. **Intent** (why) → **Outcome** (what end state) → **Scope + Non-goals** (boundaries) → **Decision Boundaries** (what may be decided unilaterally)
2. **Constraints** (must-hold limits) → **Success Criteria** (how completion is judged)
3. **Brownfield context** (existing codebase grounding — only when modifying an existing system; gather facts from source/docs *before* asking the user)

Skipping ahead to constraints before intent is the most common failure mode: you build a precise spec for the wrong problem.

### 2. Pick a technique

| Situation | Technique | Why |
|---|---|---|
| Unclear root need | 5 Whys | Drill from symptom to underlying problem |
| Abstract requirements ("fast", "intuitive") | Concrete Examples | Make testable with measurable thresholds |
| Scope ambiguity | Boundary Identification | Decide in / out / deferred explicitly |
| New domain or stakeholder | Stakeholder Interview | Structured extraction from a single source |
| Workflow optimization | Observation | Watch real usage — what people *do* ≠ what they *say* |
| Conflicting priorities | Conflict Resolution | Find shared goal beneath competing solutions |
| Documented but unvalidated | Validation Review | Run the checklist in step 5 |
| Interview converging too smoothly | Challenge Modes (Contrarian / Simplifier / Ontologist) | Stress-test untested assumptions before crystallizing |

For full technique mechanics (steps, scripts, examples), read `references/techniques.md`.

### 3. Elicit

Apply the chosen technique. For each requirement that surfaces:

1. Identify the root *need*, not the proposed solution
2. Make it concrete and testable (measurable threshold, observable behavior)
3. Write acceptance criteria in Given-When-Then form
4. Identify edge cases and exceptions
5. Classify priority — MUST / SHOULD / COULD / WONT (MoSCoW; apostrophe-free for enum consistency with the Output Shape below)
6. Note source and confidence level

**When an answer feels vague, apply the pressure ladder in order:**

1. **Evidence** — ask for a concrete example, counterexample, or recent occurrence behind the claim
2. **Hidden assumption** — surface the belief that has to be true for the claim to hold
3. **Boundary** — force a tradeoff: what would you explicitly *not* do, defer, or reject?
4. **Root cause** — if the answer still describes a symptom, reframe toward essence (analogous to 5 Whys)

Stay on the same thread until one layer deeper, one assumption clearer, or one boundary tighter. Breadth without pressure is not progress.

Accumulate open questions for anything unresolved. Do not silently invent answers — flagged
gaps are cheap; wrong assumptions in a spec are expensive.

When interviewing a stakeholder, the question banks in `references/interview-questions.md`
cover discovery, current-state, future-state, NFR, and conflict-resolution phases.

### 4. Document

Use templates from `references/templates.md`:

- **User story** template for functional requirements
- **NFR** template for quality attributes (performance, security, availability, usability)
- **Edge case table** for exception handling
- **Feature request** and **requirements document** templates for full deliverables
- **Traceability matrix** linking each requirement to its source/goal

For worked examples — well-formed stories, common mistakes, INVEST checks, acceptance
criteria patterns — read `references/user-stories.md`.

### 5. Validate

Run each requirement through the review checklist (detail in `references/techniques.md`):

- **Complete** — everything needed is documented
- **Consistent** — no contradictions between requirements
- **Correct** — matches stakeholder intent (re-confirm if uncertain)
- **Unambiguous** — only one reasonable interpretation
- **Testable** — observable, measurable, verifiable
- **Traceable** — links back to a business goal or source
- **Feasible** — implementable within known constraints
- **Prioritized** — relative importance is explicit

Flag any failing criterion. Suggest a resolution path (re-interview, concretize, defer,
drop) before declaring the spec ready.

Before sign-off, run two additional disciplines:

- **Pressure pass** — pick one earlier answer and re-probe it with an evidence, assumption, or tradeoff follow-up. If it still holds, the spec is more durable; if it cracks, you found a hidden assumption worth resolving.
- **Closure audit** — ask: "Would another round of questions change the implementation materially, or just polish wording?" If the answer is *polish*, stop. Low residual ambiguity is permission to crystallize, not permission to keep drilling.

---

## Output Shape

Useful when emitting structured output for downstream consumers (`@spec-writer`,
`@goal-developer`, `bd create`):

```yaml
Requirement:
  id: REQ-001                          # stable, monotonically assigned
  description: <human-readable>
  source: <stakeholder | observation | analysis>
  priority: MUST | SHOULD | COULD | WONT
  status: DRAFT | REVIEWED | APPROVED | REJECTED | IMPLEMENTED | VERIFIED
  acceptanceCriteria: [<Given-When-Then>, ...]
  testCases: [<id>, ...]               # optional, populated post-implementation

StakeholderProfile:
  name: <person>
  role: <role>
  interest: HIGH | MEDIUM | LOW        # how much they care about the outcome
  influence: HIGH | MEDIUM | LOW       # how much weight their input carries
  communication: <frequency + channel> # e.g. "weekly, Slack #project-x"

ElicitationResult:
  requirements: [Requirement, ...]
  stakeholders: [StakeholderProfile, ...]
  openQuestions: [<unresolved question>, ...]
  outOfScope: [<explicitly deferred item>, ...]
  decisionBoundaries: [<choice the implementer may make unilaterally>, ...]
```

---

## Anti-Patterns

| Anti-pattern | Description | Correct approach |
|---|---|---|
| **Solution First** | Accepting "add a button to X" without asking why | Ask "What problem would that button solve?" — validate the underlying need first |
| **Assumed Obvious** | "Of course it should handle empty input — that's common sense" | Document it explicitly; common sense varies by stakeholder |
| **Gold Plating** | Adding unrequested features while you're in there | Stay inside documented scope; file separate items for nice-to-haves |
| **Moving Baseline** | Expanding scope without formal change control | Lock the spec; route new asks through an explicit change log |
| **Single Stakeholder** | Treating one voice as the whole user base | Map interest × influence; sample across roles before finalizing |
| **Untestable Quality** | "Must be fast" with no threshold | Concretize: "p95 latency under 200 ms for endpoint X under load Y" |
| **Jargon Drift** | Using engineering terms with domain users | Mirror the user's vocabulary; reserve technical terms for the design doc |

---

## See Also

- `surgical-changes` — once requirements are locked, keep implementation scope locked to them
- `debugging-methodology` — when a reported "bug" turns out to be a missing requirement
- `@spec-writer` — consumes elicitation output to produce requirements.md + design.md + bd epic
- `@goal-developer` — refines a raw idea into a structured goal file (lighter than full spec)
- `beads-workflow` — turn validated requirements into a beads epic with blocking dependencies
