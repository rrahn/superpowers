---
name: ts-experiments
description: >
  TypeScript/Bun experiment patterns for the experiment-runner agent — exit code
  discipline, dependency resolution, assertion helpers, evidence serialization, and
  common Bun runtime gotchas for standalone experiment scripts. Load when: the
  experiment-runner agent is writing TypeScript (.ts) experiments, using Bun to execute
  experiment scripts, or testing behavior of TypeScript/JavaScript libraries (Zod,
  minimatch, etc.). Trigger phrases: "bun experiment", "ts experiment", "typescript
  experiment", "zod behavior", "bun run /tmp".
alwaysApply: false
tier: 4
metadata:
  version: "1.0"
  sources: "https://bun.sh/docs, https://zod.dev, verified on Bun 1.2.15 + zod@4.1.8"
user-invocable: true
---

# TypeScript/Bun Experiment Patterns

Patterns and gotchas specific to writing TypeScript experiment scripts executed by Bun.

---

## 1. Exit Code Discipline

### Use `process.exitCode`, not `process.exit()`

`process.exit(1)` terminates immediately — remaining assertions never run, and you lose
evidence. `process.exitCode = 1` marks the process as failed but lets execution continue
through all assertions:

```typescript
// GOOD — all assertions run, final exit code reflects worst result
function assert(ok: boolean, label: string, evidence: string) {
  if (ok) {
    console.log(`  ✅ PASS: ${label}`);
  } else {
    console.log(`  ❌ FAIL: ${label}`);
    console.log(`    Evidence: ${evidence}`);
    process.exitCode = 1; // marks failure, does NOT stop execution
  }
}

// BAD — stops at first failure, skips remaining assertions
if (!condition) {
  console.log("FAIL");
  process.exit(1); // everything below is lost
}
```

### Exit code semantics

| Code             | Meaning                                                         |
| ---------------- | --------------------------------------------------------------- |
| `0`              | All assertions passed                                           |
| `1`              | One or more assertions failed (set by `process.exitCode = 1`)   |
| Non-zero (other) | Script crashed — syntax error, unhandled exception, missing dep |

---

## 2. Dependency Resolution

### Bun's module resolution order

Bun resolves bare imports (e.g., `import { z } from "zod"`) in this order:

1. **Local `node_modules/`** in the script's directory
2. **Parent `node_modules/`** — walks up the directory tree toward `/`
3. **Global install cache** (`~/.bun/install/cache/`) — packages previously installed by Bun

Because of step 3, `cd /tmp && bun run exp1.ts` may silently resolve a package from the
global cache even when no `node_modules/` exists nearby. This is dangerous for experiments
because the cached version may differ from the project's pinned version.

### Run from the project root for reproducibility

Always run experiments from the project root to ensure the project's `node_modules` is
resolved first, giving you the exact version the project uses:

```bash
# GOOD — resolves zod from ~/Code/opencode/node_modules/ (pinned version)
cd ~/Code/opencode && bun run /tmp/experiments/exp1-zod-defaults.ts

# RISKY — may resolve zod from Bun's global cache (unknown version)
cd /tmp && bun run /tmp/experiments/exp1-zod-defaults.ts
```

### Standalone experiments (pinned version, no project dependency)

For experiments that must test a specific version in isolation, install into a temp directory:

```bash
cd /tmp/experiments && bun init -y && bun add zod@4.1.8
bun run exp1-zod-defaults.ts
```

### Version pinning — verify at runtime

When testing version-specific behavior, always verify the resolved version in the script.
Use the `zod` module's own version export or read `package.json` from the local
`node_modules` — do not use a bare `import` of `"zod/package.json"` as Bun's resolution
may fail to locate it depending on how the package was resolved:

```typescript
import { z } from "zod";

// Preferred: read version from the resolved package's package.json on disk
import { readFileSync } from "fs";
import { dirname, join } from "path";

const zodEntry = import.meta.resolve("zod");
const zodDir = dirname(zodEntry.replace("file://", ""));
const pkg = JSON.parse(readFileSync(join(zodDir, "package.json"), "utf8"));

console.log(`Library: zod@${pkg.version}`);
assert(
  pkg.version === "4.1.8",
  "zod version is 4.1.8",
  `got ${pkg.version} — results may not apply to target version`,
);
```

---

## 3. Evidence Serialization

### Always `JSON.stringify` data structures

The difference between diagnosing a bug in 5 seconds vs 5 minutes:

```typescript
// GOOD — parent can see exactly what was produced
const result = schema.parse({});
assert(
  result.sources !== undefined,
  "parse applies nested defaults",
  `JSON.stringify(result) = ${JSON.stringify(result)}`,
);
// Output: Evidence: JSON.stringify(result) = {}

// BAD — parent sees "[object Object]" and learns nothing
assert(
  result.sources !== undefined,
  "parse applies nested defaults",
  `result = ${result}`,
);
```

### Use `JSON.stringify(x, null, 2)` for large structures

When the data is more than ~3 fields deep, pretty-print:

```typescript
console.log("Actual output:");
console.log(JSON.stringify(result, null, 2));
```

### Stringify Zod errors

Zod error objects are deeply nested. Always serialize them:

```typescript
const parsed = schema.safeParse(input);
if (!parsed.success) {
  console.log(`Zod errors: ${JSON.stringify(parsed.error.issues, null, 2)}`);
}
```

---

## 4. Common Bun Gotchas

### 4.1 · Top-level await

Bun supports top-level await in `.ts` files. No need for async IIFE wrappers:

```typescript
// GOOD
const result = await fetch("https://example.com");

// UNNECESSARY
(async () => {
  const result = await fetch("https://example.com");
})();
```

### 4.2 · File system paths

Use `import.meta.dir` for the script's directory, not `__dirname` (which Bun supports but
is a CJS-ism):

```typescript
import { join } from "path";
const fixture = join(import.meta.dir, "fixtures", "input.json");
```

### 4.3 · Other Bun conventions

For ESM imports, Bun shell (`$`), and general TypeScript/Bun patterns, follow the
`typescript-bun` skill (loaded at tier 1). This skill does not duplicate those conventions.

---

## 5. Experiment Script Template

Complete template for a TypeScript/Bun experiment:

```typescript
// exp1-hypothesis-slug.ts
// HYPOTHESIS: [One sentence]
// BACKGROUND: [Why this matters]

// --- Assertion helper ---
let failures = 0;
function assert(ok: boolean, label: string, evidence: string) {
  if (ok) {
    console.log(`  ✅ PASS: ${label}`);
  } else {
    console.log(`  ❌ FAIL: ${label}`);
    console.log(`    Evidence: ${evidence}`);
    process.exitCode = 1;
    failures++;
  }
}

// --- Version info ---
console.log("--- Experiment: hypothesis-slug ---");
console.log(`Runtime: Bun ${Bun.version}`);
// import pkg from "zod/package.json"  // if testing a library
// console.log(`Library: zod@${pkg.version}`)

console.log();
console.log("HYPOTHESIS: [restate hypothesis here]");
console.log();

// --- Setup ---
// [imports, test data]

// --- Experiment ---
// [the operation under test]

// --- Assertions ---
// assert(condition, "label", `expected X, got ${JSON.stringify(actual)}`)

// --- Summary ---
console.log();
if (failures === 0) {
  console.log("VERDICT: ✅ ALL PASSED — hypothesis confirmed");
} else {
  console.log(`VERDICT: ❌ ${failures} FAILED — hypothesis refuted`);
}
```

---

## 6. Discovered Gotchas (from real experiments)

### Zod v4 `.default({})` does NOT apply nested defaults

**Verified on**: zod@4.1.8 (April 2026). This behavior may change in future Zod releases —
always verify with a version-printing experiment before relying on this finding.

```typescript
const Inner = z.object({ sources: z.array(z.string()).default([]) });
const Outer = z.object({ meta: Inner.default({}) });

// You might expect:
// Outer.parse({}) → { meta: { sources: [] } }

// Actual (Zod 4.1.8):
// Outer.parse({}) → { meta: {} }

// Fix: provide a fully-formed default:
const Fixed = z.object({ meta: Inner.default({ sources: [] }) });
```

This was verified across `parse()`, `safeParse()`, and schema introspection. The outer
`.default({})` bypasses the inner field's `.default([])` because the default value `{}`
is treated as a complete replacement, not a partial that gets merged with field defaults.

---

## 7. Verification

To confirm this skill's core patterns work, run the template from §5 with a deliberate
failing assertion:

```bash
cat > /tmp/verify-skill.ts << 'EOF'
let failures = 0
function assert(ok: boolean, label: string, evidence: string) {
  if (ok) {
    console.log(`  ✅ PASS: ${label}`)
  } else {
    console.log(`  ❌ FAIL: ${label}`)
    console.log(`    Evidence: ${evidence}`)
    process.exitCode = 1
    failures++
  }
}

console.log(`Runtime: Bun ${Bun.version}`)
assert(true, "passing assertion runs", "n/a")
assert(false, "failing assertion runs too", "this should be visible")
assert(true, "third assertion still runs", "n/a")
console.log(`\nTotal failures: ${failures}`)
EOF
bun run /tmp/verify-skill.ts
echo "Exit code: $?"
```

Expected output:

- All 3 assertions printed (not just the first)
- Exit code: `1`
- `Total failures: 1`

If any of these differ, the Bun runtime behavior has changed — re-verify §1.

---

## See Also

- **`typescript-bun`** skill (tier 1) — general TypeScript/Bun conventions, ESM imports,
  Bun shell `$`, `bun:test` patterns. Loaded before this skill; do not duplicate.
- **`experiment-runner.md`** agent definition — language-agnostic experiment methodology,
  experiment chains, evidence quality, output format. This skill adds TS/Bun specifics on top.
