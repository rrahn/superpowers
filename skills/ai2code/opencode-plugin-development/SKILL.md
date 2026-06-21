---
name: opencode-plugin-development
description: >
  Writing OpenCode plugins using the @opencode-ai/plugin SDK — hook system, event bus,
  tool interception, system prompt modification, and session lifecycle management. Use when:
  creating OpenCode plugins, implementing hook handlers, intercepting tool execution,
  injecting context into sessions, or integrating external systems (like GasTown) via
  the plugin API. Covers all 17 plugin hooks, deployment options, and important caveats
  about blocking, error handling, and experimental API stability.
dependencies:
  - "@opencode-ai/plugin"
alwaysApply: false
tier: 2
metadata:
  version: "1.0"
  sources: "packages/opencode/src/plugin/src/index.ts, packages/opencode/src/session/prompt.ts"
user-invocable: true
---

# OpenCode Plugin Development

Write plugins for OpenCode using the `@opencode-ai/plugin` SDK. Plugins are async
TypeScript modules that register hook handlers to intercept, modify, and extend every
phase of the OpenCode lifecycle — from session creation to tool execution to LLM
request shaping.

---

## 1. Plugin Entry Point

Every plugin exports a default async function that receives a context object and
returns a map of hook handlers:

```ts
import type { Plugin } from "@opencode-ai/plugin"

const plugin: Plugin = async (ctx) => {
  // ctx provides plugin identity and config access
  return {
    // Hook handlers go here -- all 17 hooks documented below
    "event": async (input) => { /* ... */ },
    "tool.execute.before": async (input, output) => { /* ... */ },
  }
}
export default plugin
```

**Key rule:** Hook handlers mutate `output` properties in-place. Never reassign `output`
itself — mutate its fields. For example: `output.args.foo = "bar"` YES,
`output.args = {...}` NO.

---

## 2. All 17 Plugin Hooks

### 2.1 Core Hooks

#### `event` — Global Event Listener
Receives ALL bus events. Use for logging, analytics, session lifecycle tracking.
Fired by every event on the bus (session.created, session.idle, tool.start, etc.)

```ts
"event": async (input: { event: { type: string; properties: any } }) => {
  if (input.event.type === "session.created") {
    console.log("New session:", input.event.properties.sessionID)
  }
}
```

#### `config` — Configuration Modification

```ts
"config": async (input, output: { config: Record<string, any> }) => {
  output.config.someKey = "value"
}
```

#### `tool` — Custom Tool Registration

```ts
"tool": async (input, output: { tools: ToolDefinition[] }) => {
  output.tools.push({
    name: "my_tool",
    description: "Does something useful",
    parameters: { /* JSON Schema */ },
    execute: async (args) => { /* ... */ }
  })
}
```

#### `auth` — Authentication Providers

```ts
"auth": async (input, output) => {
  // Inject auth credentials
}
```

---

### 2.2 Message Hooks

#### `chat.message` — User Message Mutation
Fires per message creation (prompt.ts L1361). Modify user message content and parts.

```ts
"chat.message": async (
  input: {
    sessionID: string;
    agent?: string;
    model?: { id: string; provider: string };
    messageID?: string
  },
  output: { message: UserMessage; parts: Part[] }
) => {
  output.parts.push({ type: "text", text: "Additional context here" })
}
```

Use cases: Context injection, message augmentation, mail drain patterns.

#### `chat.params` — LLM Request Parameter Control

```ts
"chat.params": async (input, output: { params: Record<string, any> }) => {
  output.params.temperature = 0.2
  output.params.max_tokens = 8192
}
```

#### `chat.headers` — LLM Request Header Injection

```ts
"chat.headers": async (input, output: { headers: Record<string, string> }) => {
  output.headers["X-Custom-Header"] = "value"
  output.headers["Authorization"] = "Bearer " + myToken
}
```

---

### 2.3 Permission Hooks

#### `permission.ask` — Permission Gating
Set `output.status = "deny"` to block — this throws `RejectedError` internally.

```ts
"permission.ask": async (
  input: { permission: string; /* additional context fields */ },
  output: { status?: "allow" | "deny" }
) => {
  if (input.permission === "file.write" && isSensitivePath(input)) {
    output.status = "deny" // Throws RejectedError, tool is blocked
  }
}
```

**Caveat:** `"deny"` triggers `RejectedError` — the tool sees a rejection, not silent skip.

---

### 2.4 Tool Hooks

#### `tool.execute.before` — Pre-Tool Execution
Fires before any tool runs (prompt.ts L414/L818/L884). Inspect or modify tool args.

```ts
"tool.execute.before": async (
  input: { tool: string; sessionID: string; callID: string },
  output: { args: any }
) => {
  if (input.tool === "file_write") {
    // Mutate args PROPERTIES -- don't reassign output.args
    output.args.path = sanitize(output.args.path)
  }
}
```

**Caveat:** No native `{ block: true }` mechanism. To block execution, **throw an error**
or mutate args to a no-op. Throwing propagates (Plugin.trigger has no try-catch,
lines 105-121).

#### `tool.execute.after` — Post-Tool Execution

```ts
"tool.execute.after": async (input, output) => {
  recordToolUsage(input.tool, output)
}
```

#### `shell.env` — Shell Environment Variable Injection

```ts
"shell.env": async (
  input: { tool: string },
  output: { env: Record<string, string> }
) => {
  output.env["MY_API_KEY"] = process.env.MY_API_KEY ?? ""
  output.env["PROJECT_ROOT"] = "/path/to/project"
}
```

---

### 2.5 Transform Hooks

#### `tool.definition` — Tool Schema Modification

```ts
"tool.definition": async (input, output) => {
  // Modify tool schemas visible to the model
}
```

#### `experimental.chat.messages.transform` — Full Message History Rewrite

```ts
"experimental.chat.messages.transform": async (input, output) => {
  // output.messages is the full message history -- mutate in place
}
```

#### `experimental.chat.system.transform` — System Prompt Modification
(llm.ts L106, agent.ts L290)

```ts
"experimental.chat.system.transform": async (
  input: { sessionID: string },
  output: { system: string[] }
) => {
  output.system.push("You are operating under budget constraints.")
}
```

Primary use: Context injection, persona modification, constraint enforcement.

#### `experimental.session.compacting` — Compaction Customization
(compaction.ts L169)

```ts
"experimental.session.compacting": async (
  input: { sessionID: string },
  output: { prompt?: string; context: string[] }
) => {
  output.prompt = "Summarize the session focusing on decisions made"
  output.context.push("Key constraint: always preserve file paths mentioned")
}
```

#### `experimental.text.complete` — Post-Process Assistant Text

```ts
"experimental.text.complete": async (input, output) => {
  // Modify completed text output
}
```

**Warning:** All `experimental.*` hooks may change between OpenCode versions.

---

## 3. Hook Execution Model

| Aspect           | Behavior                                                                   |
|------------------|----------------------------------------------------------------------------|
| Invocation       | All registered handlers for a hook fire sequentially                       |
| Error handling   | Plugin.trigger has NO try-catch (lines 105-121) — thrown errors propagate |
| Output mutation  | Mutate output properties in-place; never reassign output or output.args    |
| Async            | All hooks are async — you can await external calls                        |
| Multiple plugins | Handlers run in registration order; output mutations accumulate            |

---

## 4. Reference Implementation: GasTown Plugin

Complete example showing session lifecycle management, budget enforcement, and
context injection — the canonical pattern for external system integration.

```ts
import type { Plugin } from "@opencode-ai/plugin"

interface SessionState {
  budget: number
  spent: number
  turnCount: number
}

const sessions = new Map<string, SessionState>()

const gastown: Plugin = async (ctx) => {
  return {
    // 1. Session detection -- track new sessions
    "event": async (input) => {
      const { type, properties } = input.event

      if (type === "session.created") {
        const budget = await fetchBudget(properties.userID)
        sessions.set(properties.sessionID, {
          budget, spent: 0, turnCount: 0
        })
      }

      // session.idle fires per-turn, NOT per-session-end
      // Need state tracking for dedup
      if (type === "session.idle") {
        const state = sessions.get(properties.sessionID)
        if (state) {
          state.turnCount++
          const turnCost = await recordTurnCost(
            properties.sessionID, state.turnCount
          )
          state.spent += turnCost
        }
      }
    },

    // 2. System prompt injection -- budget awareness
    "experimental.chat.system.transform": async (input, output) => {
      const state = sessions.get(input.sessionID)
      if (state) {
        const remaining = state.budget - state.spent
        output.system.push(
          "[GasTown] Budget: $" + remaining.toFixed(2) +
            " remaining of $" + state.budget.toFixed(2) + "."
        )
        if (remaining < 5) {
          output.system.push(
            "CAUTION: Budget running low. Prefer efficient solutions."
          )
        }
      }
    },

    // 3. Mail drain -- inject metadata into every user message
    "chat.message": async (input, output) => {
      const state = sessions.get(input.sessionID)
      if (state) {
        output.parts.push({
          type: "text",
          text: "[GasTown] Turn " + state.turnCount +
            ", spent: $" + state.spent.toFixed(2)
        })
      }
    },

    // 4. Guard enforcement -- block tools when over budget
    "tool.execute.before": async (input, output) => {
      const state = sessions.get(input.sessionID)
      if (state && state.spent >= state.budget) {
        // No native {block: true} -- throw to prevent execution
        throw new Error(
          "[GasTown] Budget exceeded. Tool blocked: " + input.tool
        )
      }
    },

    // 5. Environment propagation -- pass info to shell commands
    "shell.env": async (input, output) => {
      output.env["GASTOWN_ACTIVE"] = "true"
      output.env["GASTOWN_ENDPOINT"] =
        process.env.GASTOWN_ENDPOINT ?? ""
    },
  }
}

export default gastown

// Stub externals
async function fetchBudget(userID: string): Promise<number> {
  return 50.0
}
async function recordTurnCost(
  sessionID: string, turn: number
): Promise<number> {
  return 0.12
}
```

### Pattern Summary

| Concern              | Hook                                 | Technique                                    |
|----------------------|--------------------------------------|----------------------------------------------|
| Session lifecycle    | `event`                              | Listen for session.created, session.idle     |
| Context injection    | `experimental.chat.system.transform` | Push to `output.system[]`                    |
| Message augmentation | `chat.message`                       | Push to `output.parts[]`                     |
| Tool blocking        | `tool.execute.before`                | Throw error (no native block flag)           |
| Cost tracking        | `event`                              | session.idle fires per-turn — dedup w/state |
| Env propagation      | `shell.env`                          | Set `output.env` properties                  |

---

## 5. Deployment Options

### Auto-discovery (recommended for project-local plugins)
Place TypeScript files in `.opencode/plugins/`:

```
.opencode/
  plugins/
    gastown.ts        # Auto-loaded
    my-logger.ts      # Auto-loaded
```

### Explicit configuration in opencode.json

```json
{
  "plugin": [
    ".opencode/plugins/gastown.ts",
    "./lib/my-plugin.ts",
    "file:///absolute/path/to/plugin.ts"
  ]
}
```

### npm package

```json
{
  "plugin": [
    "@myorg/opencode-plugin-gastown"
  ]
}
```

The plugin must have a default export matching the `Plugin` type.

---

## 6. Critical Caveats

### Error Propagation
`Plugin.trigger` (lines 105-121) has **no try-catch**. If your hook throws, the error
propagates to the calling code. This is useful for blocking (`tool.execute.before`
throw-to-block pattern) but dangerous if unintentional.

### Output Mutation Rules

```ts
// CORRECT -- mutate properties
output.args.path = "/safe/path"
output.system.push("new instruction")
output.env["KEY"] = "value"

// WRONG -- reassigning output fields
output.args = { path: "/safe/path" }  // Breaks reference
output = { args: { ... } }            // Does nothing
```

### session.idle Is Per-Turn
`session.idle` fires after every assistant turn, NOT once when the session ends.
You must track state to avoid duplicate processing:

```ts
const processedTurns = new Set<string>()
// ...
if (type === "session.idle") {
  const key = properties.sessionID + "-" + turnCount
  if (processedTurns.has(key)) return
  processedTurns.add(key)
  // Process once
}
```

### permission.ask Denial Mechanism
Setting `output.status = "deny"` doesn't silently skip — it throws `RejectedError`.
The tool caller receives an error message. Plan your UX accordingly.

### Experimental Hook Stability
All `experimental.*` hooks may change signatures or be removed between versions:
- `experimental.chat.system.transform`
- `experimental.chat.messages.transform`
- `experimental.session.compacting`
- `experimental.text.complete`

Pin your OpenCode version in production if you depend on these.

### Plugin Load Order
Plugins fire hooks in registration order. When multiple plugins modify the same
`output`, later plugins see mutations from earlier ones. Design defensively --
check before you push, don't assume the array is empty.

---

## 7. Quick-Start Template

Minimal plugin skeleton:

```ts
import type { Plugin } from "@opencode-ai/plugin"

const plugin: Plugin = async (ctx) => {
  console.log("[my-plugin] loaded")

  return {
    "event": async (input) => {
      console.log("[my-plugin] event: " + input.event.type)
    },

    "experimental.chat.system.transform": async (input, output) => {
      output.system.push("Custom system instruction from my-plugin.")
    },

    "tool.execute.before": async (input, output) => {
      console.log("[my-plugin] tool: " + input.tool)
    },
  }
}

export default plugin
```

Save as `.opencode/plugins/my-plugin.ts` and it auto-loads on next OpenCode start.

---

## 8. Critical Runtime Behaviors

Undocumented behaviors discovered empirically. Each will cause subtle or catastrophic
failures if unknown.

### ⚠️ Plugin.trigger has no try-catch — wrap every hook body

`src/plugin/index.ts` lines 106–121: hooks iterate with `await` and no surrounding
`try-catch`. An unhandled throw inside any hook:

- blocks all subsequent hooks for that trigger (sequential iteration stops)
- can crash the active session entirely

**Rule:** every hook body must catch its own errors unless the throw is intentional
(e.g., the `tool.execute.before` block pattern).

```ts
"experimental.chat.system.transform": async (input, output) => {
  try {
    output.system.push(await fetchContext(input.sessionID))
  } catch (err) {
    console.error("[my-plugin] context fetch failed:", err)
    // fall through — don't crash the session
  }
}
```

### ⚠️ output.system is a fresh array every LLM turn — always push, never cache

`experimental.chat.system.transform` receives a **new empty array** on every turn
(`llm.ts` L106). Plugins that push on first call only will lose their content after
turn 1.

**Rule:** always push unconditionally on every invocation.

**Caching note:** content pushed should be *identical* across turns so Anthropic's
prompt caching can deduplicate the system prefix. Vary-per-turn strings (timestamps,
counters) defeat caching.

```ts
// WRONG — only runs once, missing from turn 2+
let injected = false
"experimental.chat.system.transform": async (input, output) => {
  if (!injected) { output.system.push("..."); injected = true }
}

// CORRECT — push every call, stable content for cache hits
"experimental.chat.system.transform": async (input, output) => {
  output.system.push("You are operating under budget constraints.")
}
```

### ⚠️ Never reassign output.system — use push only

After your hook returns, `llm.ts` lines 104–115 splits `output.system` into two
segments for Anthropic prompt caching. If you reassign the array reference
(`output.system = [...]`), the downstream split operates on the original empty array
and all injected content is silently dropped.

```ts
// WRONG — reassignment; downstream split sees the original ref
output.system = ["My instruction"]

// CORRECT
output.system.push("My instruction")
```

### ⚠️ Skill frontmatter fields beyond name/description are stripped

`src/skill/skill.ts` uses Zod `.pick({ name: true, description: true })` when
loading SKILL.md files. All other frontmatter keys (`tier`, `dependencies`,
`metadata`, `alwaysApply`, custom fields) are **invisible to OpenCode**.

Plugins that need extended metadata (e.g., `tier`, `version`, activation conditions)
must re-parse the SKILL.md file themselves — for example with `gray-matter`:

```ts
import matter from "gray-matter"
import { readFileSync } from "fs"

const { data } = matter(readFileSync(skillPath, "utf8"))
const tier = data.tier ?? 2   // OpenCode never sees this
```

### ⚠️ tool.definition uses input.toolID — not input.name or input.id

The `tool.definition` hook receives `input.toolID` as the tool identifier. Using
`input.name` or `input.id` returns `undefined`. The `output` shape is:

```ts
output: {
  description: string   // plain text; may contain XML-like tags embedded by OpenCode
  parameters: any       // JSON Schema object
}
```

Mutate `output.description` or `output.parameters` to alter what the model sees for
that tool.

### ⚠️ Use fs.existsSync for file checks — never spawn git subprocesses

`fs.existsSync` is ~1000× faster than `git ls-files` or any subprocess spawn for
marker-based file presence checks (e.g., detecting `.opencode/`, `SKILL.md`,
`.beads/`). Subprocess overhead (fork + exec + IPC) is ~50–100ms; `existsSync` is
~0.05ms.

```ts
import { existsSync } from "fs"

// CORRECT — ~0.05ms
if (existsSync(path.join(dir, ".beads"))) { /* ... */ }

// WRONG — ~50-100ms, blocks the hook, forks a process per check
const { stdout } = await exec("git ls-files .beads")
if (stdout.trim()) { /* ... */ }
```
