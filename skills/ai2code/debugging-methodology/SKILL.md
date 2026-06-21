---
name: debugging-methodology
description: >
  Scientific debugging methodology — hypothesis-driven root cause analysis, isolation
  techniques, diagnostic logging patterns, git bisect, and async/concurrency debugging.
  Prevents the #1 AI agent failure mode: shotgun-fixing symptoms instead of diagnosing
  root causes. Load when: (1) a bug fix attempt has already failed and you are about to
  try again, (2) a test is failing and the cause is not obvious from the error message,
  (3) you have made 2+ changes trying to fix something and it is still broken, (4) you
  see a regression and need git bisect, (5) you are debugging race conditions, stale
  closures, or async timing issues, (6) you are about to add a try/catch or null-check
  to silence an error — STOP and load this skill first. Trigger phrases: "debug",
  "investigate", "figure out why", "root cause", "bisect", "it used to work".
alwaysApply: false
tier: 5
user-invocable: true
---
# Debugging Methodology

A systematic, repeatable approach to diagnosing and fixing bugs in any codebase.

---

## 1. Scientific Debugging Method

### Observe
- What is the exact symptom? (error message, wrong output, crash)
- When does it occur? (always, intermittently, under specific conditions)
- What changed recently? (`git log --oneline -20`)

### Hypothesize
- Form 2–3 possible explanations ranked by likelihood
- Ask: "What would have to be true for this hypothesis to be correct?"

### Predict
- "If hypothesis X is correct, then Y should happen when I do Z"
- Design a test that would *disprove* your hypothesis (falsification is stronger than confirmation)

### Test
- Change **one variable at a time**
- Create isolated, reproducible test cases
- Document all results, including negative ones

### Conclude
- Which hypothesis survived testing?
- What new questions emerged?
- Is further investigation needed or is the root cause confirmed?

---

## Debugging Log Template

Copy-paste and fill in as you work. Every hypothesis and test result goes here.

```
### Debugging Log: [brief description]
**Symptom:** [exact error message or wrong behavior]
**Hypothesis 1:** [description] — Likelihood: HIGH/MEDIUM/LOW
  - Prediction: [if this is true, then...]
  - Test: [what I did]
  - Result: [what happened] → CONFIRMED / DISPROVED
**Hypothesis 2:** [description] — Likelihood: HIGH/MEDIUM/LOW
  - Prediction: [if this is true, then...]
  - Test: [what I did]
  - Result: [what happened] → CONFIRMED / DISPROVED
**Root Cause:** [final diagnosis]
**Fix:** [what was changed and why]
```

---

## 2. Isolation Strategies

### Binary Search (Bisection)
1. Identify the full code path that produces the bug
2. Add a probe at the midpoint
3. Determine which half contains the bug
4. Repeat until isolated to a single function or line

### Elimination
- List all plausible causes
- Rule each one out with a targeted test
- Document the evidence used to eliminate each candidate

### Minimal Reproduction
1. Start with the full failing case
2. Remove dependencies, inputs, and components one by one
3. Stop when removal makes the bug disappear — that removed piece is the key

### Working Backwards
- Start at the error or wrong output
- Trace data flow in reverse through the call chain
- Stop when you find the last point where state was correct

### Test Runner Isolation Flags

Run a single test in isolation to rule out ordering/pollution issues:

```bash
# Python (pytest)
pytest -x --tb=short -k "test_name"          # stop on first fail, short traceback

# Go
go test -run TestName -v -count=1             # -count=1 defeats test caching

# TypeScript / Bun
bun test --bail --grep "pattern"              # stop on first fail, filter by name
```

---

## 3. Diagnostic Logging Patterns

### Entry/Exit Logging
```js
function suspectFunction(args) {
  console.log('[ENTER] suspectFunction', { args });
  try {
    const result = /* ... */;
    console.log('[EXIT] suspectFunction', { result });
    return result;
  } catch (e) {
    console.log('[ERROR] suspectFunction', { error: e });
    throw e;
  }
}
```

### State Snapshot Logging
```js
console.log('[STATE BEFORE]', JSON.stringify(state, null, 2));
await operation();
console.log('[STATE AFTER]', JSON.stringify(state, null, 2));
```

### Async Operation Tracing
```js
const traced = async (name, fn) => {
  console.log(`[${name}] START`, Date.now());
  try {
    const result = await fn();
    console.log(`[${name}] END`, Date.now(), result);
    return result;
  } catch (e) {
    console.log(`[${name}] ERROR`, Date.now(), e);
    throw e;
  }
};
```

### Call Stack Capture
```js
console.log('[STACK]', new Error().stack);
```

### Python Equivalents
```python
import logging, traceback
log = logging.getLogger(__name__)

def suspect_function(args):
    log.debug("[ENTER] suspect_function args=%s", args)
    try:
        result = ...
        log.debug("[EXIT] suspect_function result=%s", result)
        return result
    except Exception:
        log.error("[ERROR] suspect_function\n%s", traceback.format_exc())
        raise
```

### Go Equivalents
```go
import "log/slog"

func suspectFunction(args string) (string, error) {
    slog.Debug("[ENTER] suspectFunction", "args", args)
    result, err := doWork(args)
    if err != nil {
        slog.Error("[ERROR] suspectFunction", "err", err)
        return "", err
    }
    slog.Debug("[EXIT] suspectFunction", "result", result)
    return result, nil
}
```
---

## 4. Git Bisect Workflow

Use when a regression exists but the introducing commit is unknown.

```bash
git bisect start
git bisect bad HEAD                  # current commit is broken
git bisect good <last-known-good>    # last commit known to work

# Git checks out a midpoint commit; run your reproducer, then:
git bisect good   # if this commit works
git bisect bad    # if this commit is broken

# Repeat until Git reports the first bad commit
git bisect reset  # return to HEAD when done
```

**Automate with a script:**
```bash
git bisect run ./reproduce.sh   # exits 0 = good, non-zero = bad
```
---

## 5. Async & Concurrent Debugging Patterns

### Race Condition Detection
```js
// Log timestamps to reveal ordering issues
console.log('[OP A] started', Date.now());
console.log('[OP B] started', Date.now());
// If B completes before A but A's result overwrites B, you have a race
```

### Stale Closure Detection
```js
// Compare closure-captured value vs current value
const valueRef = { current: value };
// Update ref on every change; compare in callbacks
console.log('[CLOSURE CHECK]', {
  closureValue: value,      // potentially stale
  currentValue: valueRef.current  // always fresh
});
```

### Cleanup Race (async effect cancellation)
```js
// Universal cancellation pattern for async operations
let cancelled = false;

asyncOperation().then(result => {
  if (cancelled) return;   // guard every state update
  applyResult(result);
});

return () => { cancelled = true; };   // cleanup / unmount
```

---

## 6. Memory Leak Detection Patterns

### Repeated-Operation Heap Test
```js
const before = process.memoryUsage().heapUsed;

for (let i = 0; i < 1000; i++) {
  suspectOperation();
  if (i % 100 === 0) console.log('heap', process.memoryUsage().heapUsed);
}

const after = process.memoryUsage().heapUsed;
console.log('delta bytes', after - before, 'per-op', (after - before) / 1000);
```
A flat profile means no leak; a steadily climbing profile confirms one.

### Browser Heap Snapshot Workflow
1. DevTools → Memory → Take snapshot (baseline)
2. Perform the suspect operation N times
3. Take a second snapshot
4. Use the "Comparison" view — objects with growing retained size are the leak

### Common Leak Sources Checklist
- Event listeners added but never removed
- Subscriptions / timers never cancelled
- Resources (file handles, native objects) missing `.dispose()` / `.delete()` in a `finally` block
- Closures retaining large objects longer than needed

---

## When to Escalate

Stop and ask the user when any of these are true:

1. **3 hypotheses disproved** with no new leads emerging from the evidence
2. **All isolation strategies exhausted** (bisect, elimination, minimal repro, working backwards) — the bug survives every cut
3. **Root cause found but fix is unclear** — you know *what* but not *how* without risking collateral damage

Use this template to summarize before escalating:

```
I've investigated [symptom] and narrowed it down but need your input:
- Tried: [list hypotheses and outcomes]
- Ruled out: [eliminated causes]
- Current best theory: [what remains]
- Stuck because: [why you can't proceed]
```

---

## 7. Anti-Patterns Catalogue

| Anti-pattern | Description | Correct approach |
|---|---|---|
| **Shotgun debugging** | Changing random things hoping something works | Form a hypothesis; change one thing at a time |
| **Confirmation bias** | Only looking for evidence that supports your theory | Actively try to *disprove* each hypothesis |
| **Assumption without testing** | "It can't be X because…" without verifying | Test every assumption, even obvious ones |
| **Fixing symptoms** | Silencing the error message instead of the root cause | Trace to the origin; fix there |
| **Scope creep** | Investigating unrelated issues during the bug hunt | Log unrelated findings, stay focused on the current bug |
| **Undocumented experiments** | Making changes without recording what was tried | Keep a running log of tests and their outcomes |
| **Big-bang changes** | Applying multiple fixes simultaneously | One change per test cycle so causation is clear |
