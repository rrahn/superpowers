# Elicitation Techniques — Detailed Reference

Comprehensive methodology for each technique. Loaded on demand when applying a specific approach.

## Contents

- [The 5 Whys](#the-5-whys)
- [Concrete Examples Technique](#concrete-examples-technique)
- [Boundary Identification](#boundary-identification)
- [Stakeholder Interviews](#stakeholder-interviews)
- [Observation and Shadowing](#observation-and-shadowing)
- [Stakeholder Analysis](#stakeholder-analysis)
- [Conflict Resolution Process](#conflict-resolution-process)
- [Challenge Modes](#challenge-modes)
- [Validation Techniques](#validation-techniques)
- [Traceability](#traceability)

---

## The 5 Whys

Drill past surface requests to discover root needs.

```
Surface Request: "We need a dashboard"

Why 1: Why do you need a dashboard?
→ "To see our metrics in one place"

Why 2: Why do you need to see metrics in one place?
→ "To identify problems quickly"

Why 3: Why do you need to identify problems quickly?
→ "Because slow response affects customer satisfaction"

Why 4: Why does customer satisfaction matter right now?
→ "We're losing customers and don't know why until it's too late"

Why 5: Why don't you know until it's too late?
→ "We only see issues in monthly reports"

Root Need: Real-time alerting for customer-impacting issues
(Not just a dashboard - the dashboard was a solution, not the need)
```

---

## Concrete Examples Technique

Transform abstract requirements into specific, testable scenarios:

| Abstract | Concrete |
|----------|----------|
| "The system should be fast" | "Page loads in under 2 seconds on 3G" |
| "Users should be able to search" | "Find orders by customer name, date range, or status" |
| "It needs to be secure" | "All PII encrypted at rest, session timeout after 15 min inactive" |
| "Good error handling" | "Network failures retry 3x with exponential backoff, then show offline mode" |

---

## Boundary Identification

Define what's explicitly in and out of scope:

```
Feature: User Registration

IN SCOPE:
✓ Email/password registration
✓ Email verification
✓ Password strength requirements
✓ Terms of service acceptance

OUT OF SCOPE:
✗ Social login (Google, Facebook)
✗ Two-factor authentication
✗ Password recovery (separate feature)

DEFERRED:
◐ SSO integration (planned for Q3)
◐ Biometric login (pending security review)
```

---

## Stakeholder Interviews

Structured conversation to extract requirements:

```
Interview Structure (45 min):

1. CONTEXT (10 min)
   - What's your role in this project?
   - What does success look like for you?
   - What's driving this initiative?

2. CURRENT STATE (10 min)
   - How do you do this today?
   - What works well?
   - What are the pain points?

3. DESIRED STATE (15 min)
   - What would the ideal solution look like?
   - Walk me through a typical scenario...
   - What would make your job easier?

4. CONSTRAINTS (5 min)
   - What absolutely must be included?
   - What's definitely out of scope?
   - Any timeline or budget constraints?

5. WRAP-UP (5 min)
   - What haven't I asked that I should?
   - Who else should I talk to?
   - Can I follow up if I have questions?
```

---

## Observation and Shadowing

Watch users perform tasks in their environment:

```
Observation Protocol:

PREPARE:
- Define what you're observing
- Get permission to observe
- Prepare note-taking template

OBSERVE:
- Note actions, not interpretations
- Record workarounds and pain points
- Note environmental factors
- Time key activities

DEBRIEF:
- "I noticed you did X, can you tell me more?"
- "What would make that easier?"
- "How often does this happen?"

Document:
┌─────────────────────────────────────────────────────────────┐
│ Observation: Order Processing                               │
├─────────────────────────────────────────────────────────────┤
│ Action: Copied customer email from order to support tool    │
│ Time: 15 seconds per order                                  │
│ Frequency: ~50 orders/day                                   │
│ Pain Point: Manual copy-paste, error-prone                  │
│ Opportunity: Direct integration between systems             │
└─────────────────────────────────────────────────────────────┘
```

---

## Stakeholder Analysis

### Stakeholder Map

```
             High Influence
                   │
    ┌──────────────┼──────────────┐
    │   Manage     │    Partner   │
    │   Closely    │    With      │
    │              │              │
Low ├──────────────┼──────────────┤ High
Interest          │              Interest
    │   Monitor    │    Keep      │
    │   Only       │    Informed  │
    │              │              │
    └──────────────┼──────────────┘
                   │
             Low Influence
```

### Stakeholder Register Template

| Name | Role | Interest | Influence | Communication |
|------|------|----------|-----------|---------------|
| VP Sales | Sponsor | High | High | Weekly update |
| Dev Team | Implementer | High | Medium | Daily standup |
| Legal | Advisor | Low | High | As needed |

### RACI Matrix

```
R = Responsible (does the work)
A = Accountable (final decision maker)
C = Consulted (provides input)
I = Informed (kept updated)

| Requirement | Product | Dev | Design | Legal |
|-------------|---------|-----|--------|-------|
| User stories | R,A | C | C | I |
| UI mockups | C | I | R,A | I |
| API contracts | C | R,A | I | I |
| Privacy policy | C | I | I | R,A |
```

---

## Conflict Resolution Process

When stakeholders disagree:

```
Resolution Process:

1. UNDERSTAND both positions
   - "Help me understand why X is important to you"
   - Identify underlying needs vs stated positions

2. FIND COMMON GROUND
   - What do both parties agree on?
   - What's the shared goal?

3. EXPLORE OPTIONS
   - Can we do both? (phased approach)
   - Is there a third option that addresses both needs?
   - What's the minimum viable for each?

4. ESCALATE if needed
   - Present options with trade-offs
   - Let decision-maker decide
   - Document the decision and rationale

Example:
Marketing wants: Launch by Q1 with all features
Engineering says: Can't do all features by Q1

Resolution: Launch Q1 with core features (MVP), Phase 2 in Q2
Documented: ADR-2024-03: MVP Scope Decision
```

---

## Challenge Modes

Assumption stress-tests to deploy when an interview is converging too smoothly — a sign that everyone is agreeing on the surface framing without testing whether the framing itself is correct. Use one mode per session unless a new untested assumption surfaces.

### Contrarian

**When**: An answer rests on an untested assumption, or every stakeholder has agreed too quickly.

**Pattern**: Argue the opposite position seriously, not as a debate trick.

> "What would have to be true for the *opposite* of this requirement to be the right answer? If we built the inverse, who would be better off?"

**Example**: Stakeholder says "users want fewer clicks to checkout." Contrarian probe: "What would have to be true for users to *want* more steps — confirmation, undo, fraud safeguards? Is the real goal fewer clicks, or fewer regrets?"

**Stops when**: The assumption is either validated (you understand *why* it holds) or replaced (a deeper need surfaces).

### Simplifier

**When**: Scope is expanding faster than outcome clarity. Requirement count is climbing but the desired end-state is still fuzzy.

**Pattern**: Force a minimum-viable framing.

> "If we had to ship the smallest version of this in two weeks, what would survive? What would you cut and still call it a success?"

**Example**: Spec has 23 acceptance criteria across 4 user roles. Simplifier probe: "If you could ship for only one role with three criteria, which role and which three?" The surviving set reveals the true priority core.

**Stops when**: The MVP shape is concrete and the rest is explicitly marked SHOULD/COULD rather than MUST.

### Ontologist

**When**: The user keeps describing symptoms, or each answer triggers another layer of "and also..." without the underlying intent stabilizing.

**Pattern**: Force essence-level reframing.

> "Is this requirement the actual goal, or a proxy for something else? If we delivered exactly this and nothing more, what would still be missing?"

**Example**: Stakeholder wants "a dashboard with 12 charts." Ontologist probe: "Is the goal to *see* 12 charts, or to *answer* specific questions? Which questions, and would 3 well-chosen charts answer them?" The reframing often replaces a feature-shaped ask with an outcome-shaped one.

**Stops when**: The intent is named at a level abstract enough to survive solution drift but concrete enough to be testable.

### Combining modes

Apply at most one mode per round; multiple in succession produces fatigue rather than insight. Track which modes you've used so you don't loop on the same lever.

---

## Validation Techniques

### Requirements Review Checklist

| Criterion | Question | Pass/Fail |
|-----------|----------|-----------|
| Complete | Is everything needed documented? | |
| Consistent | Are there contradictions? | |
| Correct | Does it match stakeholder intent? | |
| Unambiguous | Is there only one interpretation? | |
| Testable | Can we verify it's met? | |
| Traceable | Can we link to business goal? | |
| Feasible | Can it be implemented? | |
| Prioritized | Is importance clear? | |

### Prototype Validation

```
Prototype Levels:

Low Fidelity (Paper/Whiteboard):
- Quick to create (minutes)
- Good for: Overall flow, major screens
- Validate: "Is this the right approach?"

Medium Fidelity (Clickable mockups):
- Moderate effort (hours)
- Good for: Detailed interactions, UI layout
- Validate: "Does this workflow make sense?"

High Fidelity (Functional prototype):
- Significant effort (days)
- Good for: Complex interactions, performance
- Validate: "Will this actually work?"
```

### Acceptance Criteria Review

```
Review Format:

"Here's my understanding of [feature]. Please correct me if I'm wrong."

[Read each scenario aloud]

Questions:
- "Is this what you expected?"
- "What did I miss?"
- "What edge cases should we handle?"
- "Is the priority right?"

Document changes and get sign-off.
```

---

## Traceability

### Traceability Matrix

```
| Req ID | Description | Source | Priority | Status | Test Cases |
|--------|-------------|--------|----------|--------|------------|
| REQ-001 | User login | Stakeholder interview | MUST | Approved | TC-001, TC-002 |
| REQ-002 | Order history | User observation | SHOULD | Draft | TC-015 |
| REQ-003 | Export CSV | Sales team request | COULD | Approved | TC-020 |
```

### Requirement States

```
States:
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│ Draft   │────►│ Reviewed │────►│ Approved │────►│ Implemented│
└─────────┘     └──────────┘     └──────────┘     └────────────┘
                     │                                   │
                     ▼                                   ▼
                ┌──────────┐                      ┌──────────┐
                │ Rejected │                      │ Verified │
                └──────────┘                      └──────────┘
```
