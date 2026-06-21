---
name: typescript-bun
description: >
  TypeScript project tooling with Bun runtime, turbo monorepo, tsgo/tsc type checking,
  biome/eslint linting, and bun:test — project discovery, validation commands, coding
  standards, and Bun-specific patterns. Use when: working in a TypeScript/Bun project,
  writing TypeScript code, running tests, type checking, or managing a turbo monorepo.
  Covers strict TypeScript, Zod schemas, Hono handlers, and plugin development.
markers:
  - bun.lockb
  - bunfig.toml
globs:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/bun.lockb"
alwaysApply: false
tier: 1
metadata:
  version: "1.0"
  sources: "https://bun.sh/docs, https://turbo.build/repo/docs"
user-invocable: true
---

# TypeScript + Bun Development

Guide for TypeScript projects using the Bun runtime, turbo monorepo orchestration,
and modern tooling (biome, tsgo, drizzle, Hono, Zod).

---

## 1. Project Discovery

Before writing or modifying code, detect the project shape.

### Marker files

| File / Dir               | Signals                                      |
| ------------------------ | -------------------------------------------- |
| `package.json`           | Node/Bun project root                        |
| `bun.lockb` / `bun.lock` | Bun is the package manager                  |
| `tsconfig.json`          | TypeScript project                           |
| `turbo.json`             | Turborepo monorepo orchestration             |
| `biome.json` / `biome.jsonc` | Biome for lint + format                 |
| `.eslintrc*` / `eslint.config.*` | ESLint for linting                   |
| `drizzle.config.ts`      | Drizzle ORM for persistence                  |
| `bunfig.toml`            | Bun configuration                            |

### Monorepo detection

When `package.json` has `"workspaces"`, you are in a monorepo. Typical layout:

    project-root/
    ├── turbo.json              ← turbo orchestration
    ├── package.json            ← root workspace config
    ├── packages/
    │   ├── opencode/
    │   │   ├── package.json
    │   │   ├── tsconfig.json
    │   │   └── src/            ← main app source
    │   ├── plugin-sdk/
    │   └── shared/
    └── apps/
        └── web/

Use `turbo` to orchestrate tasks across packages — never run tasks in
individual packages unless explicitly debugging a single package.

### Discovery checklist

1. Read `package.json` → identify `scripts`, `dependencies`, `workspaces`.
2. Read `tsconfig.json` → identify `strict`, `paths`, `compilerOptions`.
3. Read `turbo.json` → identify task pipeline and caching.
4. Read `biome.json` or eslint config → identify lint/format rules.
5. Check for `bunfig.toml` → Bun-specific settings.

---

## 2. Validation Commands

Run these in order. Fix errors before moving to the next step. All commands
assume you are at the **monorepo root** unless stated otherwise.

### 2.1 Install dependencies

```sh
bun install
```

Never use `npm install` or `yarn install` in a Bun project.

### 2.2 Type checking

```sh
# Preferred: tsgo (faster, used in most packages)
bunx tsgo --noEmit

# Fallback: tsc
bunx tsc --noEmit

# Via turbo (runs across all packages)
bun turbo typecheck
```

Always run with `--noEmit` — we type-check, we don't emit JS from tsc.

### 2.3 Linting

```sh
# Biome (preferred)
bunx biome check .

# ESLint (fallback)
bunx eslint .

# Via turbo
bun turbo lint
```

### 2.4 Formatting

```sh
# Biome (preferred)
bunx biome format --write .

# Check only (CI)
bunx biome format .

# Prettier (fallback)
bunx prettier --check .
```

### 2.5 Tests

```sh
# Single package
bun test

# Specific file
bun test src/handlers/auth.test.ts

# With filter
bun test --filter "should create user"

# Via turbo (all packages)
bun turbo test
```

### 2.6 Build

```sh
bun turbo build
```

### 2.7 Full validation pipeline

```sh
bun turbo typecheck lint test build
```

---

## 3. Errand Runner Delegation

When asked to validate, fix, or ship code, run tasks in this order:

| Step | Command                     | Gate                                    |
| ---- | --------------------------- | --------------------------------------- |
| 1    | `bun install`               | Exit 0                                  |
| 2    | `bunx tsgo --noEmit`        | 0 errors                                |
| 3    | `bunx biome check .`        | 0 errors, warnings acceptable           |
| 4    | `bun test`                  | All pass                                |
| 5    | `bun turbo build`           | Exit 0                                  |

If a step fails, fix it before continuing. Do not skip gates.

For monorepo-wide validation, prefer `bun turbo typecheck lint test build`
which respects dependency order and caching.

---

## 4. Report Template Labels

When reporting results, use these labels:

| Label           | Meaning                                           |
| --------------- | ------------------------------------------------- |
| `TYPE_OK`       | `tsgo --noEmit` exited 0                          |
| `TYPE_FAIL`     | Type errors found                                 |
| `LINT_OK`       | `biome check` / `eslint` passed                   |
| `LINT_FAIL`     | Lint errors found                                 |
| `FORMAT_OK`     | `biome format` / `prettier` check passed          |
| `FORMAT_DRIFT`  | Files need formatting                             |
| `TEST_OK`       | All tests passed                                  |
| `TEST_FAIL`     | Test failures — include names + assertion details  |
| `BUILD_OK`      | `turbo build` exited 0                            |
| `BUILD_FAIL`    | Build errors found                                |
| `DEPS_OK`       | `bun install` succeeded, lockfile clean            |
| `DEPS_DRIFT`    | Lockfile out of sync or install failed             |

---

## 5. Coding Standards

### 5.1 Strict TypeScript

The project enforces strict TypeScript. Key compiler options:

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "verbatimModuleSyntax": true
  }
}
```

**Rules:**

- **No `any`** without a justifying comment explaining why it's necessary.
- **No non-null assertions (`!`)** without a justifying comment.
- **No `@ts-ignore`** — use `@ts-expect-error` with a description if truly needed.
- **No CommonJS** — no `require()`, no `module.exports`. ESM only.
- **`import type`** for type-only imports:

  ```ts
  import type { User } from "./types";
  import { createUser } from "./users";
  ```

- **Discriminated unions** over class hierarchies:

  ```ts
  // Good
  type Result<T> =
    | { ok: true; value: T }
    | { ok: false; error: Error };

  // Bad — class hierarchies for variants
  class SuccessResult<T> extends BaseResult { ... }
  ```

- **Type-first design** — define interfaces/types before implementations.
- **Exhaustive switches** with `never` checks:

  ```ts
  function handle(action: Action) {
    switch (action.type) {
      case "create": return handleCreate(action);
      case "delete": return handleDelete(action);
      default: {
        const _exhaustive: never = action;
        throw new Error("Unhandled action");
      }
    }
  }
  ```

### 5.2 Bun-Specific Patterns

**Shell operations** — use `Bun.$`, not `child_process`:

```ts
// Good
const result = await Bun.$`ls -la ${dir}`.text();

// Bad
import { exec } from "child_process";
```

**File I/O** — use Bun APIs:

```ts
// Good
const content = await Bun.file("config.json").json();
await Bun.write("output.txt", data);

// Bad
import { readFileSync } from "fs";
```

**SQLite** — use `bun:sqlite`:

```ts
import { Database } from "bun:sqlite";
const db = new Database("app.db");
```

**Testing** — use `bun:test`:

```ts
import { describe, it, expect, beforeEach, mock } from "bun:test";

describe("UserService", () => {
  it("should create a user", async () => {
    const user = await createUser({ name: "Alice" });
    expect(user.id).toBeDefined();
    expect(user.name).toBe("Alice");
  });
});
```

**Async/Await** — always prefer `async`/`await` over callbacks or raw promises:

```ts
// Good
const data = await fetchUser(id);

// Bad
fetchUser(id).then((data) => { ... });
```

### 5.3 Hono HTTP Framework

```ts
import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";

const app = new Hono();

const CreateUserSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});

app.post("/users", zValidator("json", CreateUserSchema), async (c) => {
  const body = c.req.valid("json");
  const user = await createUser(body);
  return c.json(user, 201);
});
```

**Patterns:**

- Validate request bodies with `zValidator` + Zod schemas.
- Return typed JSON responses with `c.json()`.
- Use middleware for auth, logging, error handling.
- Group routes with `app.route("/api", apiRoutes)`.

### 5.4 Zod Schemas

Use Zod for **runtime validation** and derive TypeScript types from schemas:

```ts
import { z } from "zod";

// Schema is the source of truth
export const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  email: z.string().email(),
  role: z.enum(["admin", "user", "viewer"]),
  createdAt: z.coerce.date(),
});

// Type derived from schema
export type User = z.infer<typeof UserSchema>;

// Partial schema for updates
export const UpdateUserSchema = UserSchema.partial().omit({ id: true });
export type UpdateUser = z.infer<typeof UpdateUserSchema>;
```

**Rules:**

- Zod schemas for **runtime** boundaries (API input, config, external data).
- TypeScript types for **compile-time** internal contracts.
- Derive types from schemas with `z.infer<>`, not the other way around.
- Keep schemas in a dedicated `schemas/` or co-located with the domain.

### 5.5 Drizzle ORM + bun:sqlite

```ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { drizzle } from "drizzle-orm/bun-sqlite";
import { Database } from "bun:sqlite";

// Schema definition
export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
});

// Database instance
const sqlite = new Database("app.db");
export const db = drizzle(sqlite);

// Queries
const allUsers = await db.select().from(users);
const user = await db.select().from(users).where(eq(users.id, id));
await db.insert(users).values({ id, name, email, createdAt: new Date() });
```

### 5.6 Plugin System

Plugins use the `@opencode-ai/plugin` SDK with async hooks:

```ts
import { definePlugin } from "@opencode-ai/plugin";

export default definePlugin({
  name: "my-plugin",
  version: "1.0.0",

  hooks: {
    "before:run": async (context) => {
      // Runs before each command execution
    },
    "after:run": async (context, result) => {
      // Runs after each command execution
      if (result.exitCode !== 0) {
        await notifyFailure(context, result);
      }
    },
  },
});
```

**Rules:**

- Hooks are always `async` functions.
- Plugins must not throw — wrap risky code in try/catch.
- Plugins must not mutate shared state outside their scope.
- Use the SDK types for hook signatures; don't hand-roll them.

### 5.7 Turbo Orchestration

```jsonc
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**"]
    },
    "typecheck": {
      "dependsOn": ["^build"]
    },
    "lint": {},
    "test": {
      "dependsOn": ["build"]
    }
  }
}
```

**Rules:**

- `^build` means "build dependencies first".
- Use `bun turbo <task>` from the monorepo root.
- Turbo caches results — `bun turbo build --force` to skip cache.
- Filter to a package: `bun turbo build --filter=opencode`.
- Never bypass turbo for cross-package tasks.

---

## 6. Prohibitions

These patterns are **banned**. Do not use them.

| Prohibition                       | Reason                                           |
| --------------------------------- | ------------------------------------------------ |
| `any` without comment             | Defeats type safety                              |
| `!` (non-null) without comment    | Hides potential null/undefined bugs               |
| `@ts-ignore`                      | Use `@ts-expect-error` with description           |
| `require()` / `module.exports`    | CommonJS; use ESM `import`/`export`               |
| `npm` / `yarn` / `pnpm`          | Use `bun` as the package manager                  |
| `node` CLI                        | Use `bun` to run scripts                          |
| `child_process`                   | Use `Bun.$` for shell operations                  |
| `fs.readFileSync` / `writeFileSync` | Use `Bun.file()` / `Bun.write()`              |
| Callbacks for async               | Use `async`/`await`                               |
| Class hierarchies for variants    | Use discriminated unions                          |
| `console.log` in production code  | Use a structured logger                           |
| Barrel `index.ts` re-exports      | Direct imports for tree-shaking and clarity       |
| `enum` (TypeScript)               | Use `as const` objects or union types              |
| Mutation of function parameters   | Return new values; treat params as readonly        |
| Default exports (prefer named)    | Named exports for refactorability                  |

---

## 7. Output Truncation Rules

When reporting command output:

1. **Type errors**: Show the first 5 errors in full, then `... and N more errors`.
2. **Test failures**: Show each failing test name + first assertion failure.
   Truncate stack traces to 5 frames.
3. **Lint errors**: Show first 10 errors with file:line, then summarize.
4. **Build output**: Show only errors/warnings. Suppress success logs.
5. **Install output**: Show only if there are warnings or errors.
6. **Turbo output**: Show the task summary table, suppress per-task stdout
   unless there are failures.

**Max output per command**: ~100 lines. If exceeded, truncate the middle
and keep the first 30 + last 30 lines with a `[... N lines truncated ...]`
marker.

---

## Quick Reference

```sh
# Install
bun install

# Type check
bunx tsgo --noEmit          # preferred
bunx tsc --noEmit           # fallback

# Lint
bunx biome check .          # preferred
bunx eslint .               # fallback

# Format
bunx biome format --write . # preferred
bunx prettier --write .     # fallback

# Test
bun test                    # all tests
bun test path/to/file.test.ts

# Build
bun turbo build

# Full pipeline
bun turbo typecheck lint test build

# Single package
bun turbo build --filter=opencode
```
