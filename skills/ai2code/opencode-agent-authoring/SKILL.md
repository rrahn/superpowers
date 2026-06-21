---
name: opencode-agent-authoring
description: >
  Writing and improving OpenCode agent definitions — YAML frontmatter, permission models,
  agent modes, task delegation, skill loading, and design patterns. Use when: creating new
  agents, modifying agent permissions, designing orchestrator/worker/judge agent hierarchies,
  or debugging agent behavior. Covers markdown format, tool permissions, model selection,
  and the checklist for well-designed agents.
markers:
  - .opencode/
  - AGENTS.md
globs:
  - "**/agent/**/*.md"
  - "**/agents/**/*.md"
  - "**/.opencode/**"
alwaysApply: false
tier: 4
metadata:
  version: "1.0"
  sources: "packages/opencode/src/config/config.ts, packages/opencode/src/permission/next.ts, packages/opencode/src/agent/agent.ts"
user-invocable: true
---

# OpenCode Agent Authoring Reference

An OpenCode agent is a single Markdown file with YAML frontmatter. The filename (kebab-case, without extension) becomes the agent name.

Agents live in:
- `.opencode/agents/` — project-scoped
- `~/.opencode/agents/` — global

---

## 1. File Structure

```yaml
---
model: provider/model-name
description: When to use this agent — shown in @ menu and task tool
mode: primary
variant: high
temperature: 0
permission:
  bash:
    "*": allow
    "git commit*": deny
    "git push*": deny
  edit:
    "*": allow
  read: allow
  task:
    "*": deny
---

# Agent Display Name

System prompt goes here. Markdown body is the agent’s instructions.
```

---

## 2. YAML Frontmatter Fields

### Required

| Field         | Type   | Description                                                      |
|---------------|--------|------------------------------------------------------------------|
| `description` | string | When to use this agent. Shown in @ autocomplete and task tool.   |

### Model & Reasoning

| Field         | Type    | Description                                                     |
|---------------|---------|-----------------------------------------------------------------|
| `model`       | string  | Model ID as `provider/model` (e.g. `anthropic/claude-sonnet-4-20250514`) |
| `variant`     | string  | Reasoning effort: `"low"`, `"medium"`, `"high"`, `"max"`        |
| `temperature` | number  | 0 = deterministic, 1 = creative                                 |
| `top_p`       | number  | Nucleus sampling parameter                                      |
| `steps`       | integer | Max agentic loop iterations before forcing a text response      |

> **Note:** `reasoningEffort` (used in some existing agents) is a legacy alias. It ends up in `options` as an unknown key. The canonical schema field is `variant`. Both work in practice — use `variant` for new agents.

### Visibility & Lifecycle

| Field      | Type    | Description                                              |
|------------|---------|----------------------------------------------------------|
| `mode`     | string  | `"primary"` / `"subagent"` / `"all"` (default: `"all"`) |
| `hidden`   | boolean | Hide from @ autocomplete menu                            |
| `disable`  | boolean | Disable a built-in agent without deleting it             |
| `color`    | string  | Hex color or theme name for UI display                   |

### Advanced

| Field        | Type   | Description                            |
|--------------|--------|----------------------------------------|
| `permission` | object | Tool permission rules (see §3)         |
| `options`    | object | Arbitrary key-value pairs for extensions |

---

## 3. Permission Model

Permissions control which tools an agent can use and how. Three actions:

| Action  | Behavior                          |
|---------|-----------------------------------|
| `allow` | Tool executes without prompting   |
| `ask`   | User is prompted before execution |
| `deny`  | Tool call is blocked silently     |

### Syntax

**Shorthand** — applies to all arguments:

```yaml
permission:
  read: allow
  todowrite: deny
```

**Pattern matching** — glob patterns on tool arguments:

```yaml
permission:
  bash:
    "*": allow
    "git commit*": deny
    "git push*": deny
    "rm -rf *": deny
  edit:
    "*": allow
    "*.env": deny
    "*.pem": deny
  task:
    "*": deny
    "developer": allow
    "codebase-analyzer": allow
```

### Resolution Rules

1. Most-specific pattern wins (longer/more-literal match).
2. Equal specificity: last-defined pattern wins.
3. No match: defaults to `ask`.

### Recommended Baseline Permissions

```yaml
permission:
  bash:
    "*": allow
    "git commit*": deny
    "git push*": deny
    "rm -rf /": deny
  edit:
    "*": allow
  read: allow
  glob: allow
  grep: allow
  fetch: allow
  task:
    "*": deny
```

Start from this baseline and add/remove per agent purpose.

---

## 4. Agent Modes

| Mode       | Selectable in @ menu | Callable via `task` tool | Default for    |
|------------|----------------------|--------------------------|----------------|
| `primary`  | Yes                  | No                       | —              |
| `subagent` | No                   | Yes                      | —              |
| `all`      | Yes                  | Yes                      | custom agents  |

- Use `primary` for user-facing agents (e.g. `developer`, `architect`).
- Use `subagent` for agents only invoked by other agents (e.g. `test-runner`, `linter`).
- Use `all` when an agent should be both user-selectable and delegatable.

---

## 5. Task Delegation

Agents invoke subagents via the `task` tool. Control delegation with `task` permissions:

```yaml
permission:
  task:
    "*": deny                # deny by default
    "developer": allow       # allow calling the developer agent
    "test-runner": allow     # allow calling the test-runner agent
```

When writing delegation instructions in the markdown body, include a table:

```markdown
## Delegation Guidelines

| Task Type          | Delegate To        | When                              |
|--------------------|--------------------|-----------------------------------|
| Write code         | @developer         | Any file creation/modification    |
| Run tests          | @test-runner       | After code changes                |
| Research codebase  | @codebase-analyzer | Before architectural decisions    |
```

---

## 6. Skill Loading

Agents load skills in their markdown body via:

```
skill({ name: "skill-name" })
```

Skills are discovered from (in order):
1. `.opencode/skills/` — project-level
2. `~/.opencode/skills/` — global
3. `.claude/skills/` — Claude Code compatibility

Include a **Project Discovery** section in the agent prompt:

```markdown
## Project Discovery

Before starting work, load relevant skills:

skill({ name: "project-conventions" })
skill({ name: "testing-patterns" })
```

---

## 7. Markdown Body Features

### File Injection

Reference a file to inject its contents into context:

```
@path/to/file.ts
```

### Command Output Injection

Inject shell command output with the bang-backtick syntax:

```
!`git log --oneline -10`
!`cat package.json | jq '.dependencies'`
```

### System Prompt Best Practices

- Use imperative form ("Analyze the codebase", not "You should analyze").
- Front-load the common case — put the most frequent instructions first.
- Include concrete examples of expected behavior.
- Add context protection directives for context-heavy agents:

```markdown
## Context Management

CRITICAL: Do not dump entire file contents into context unless necessary.
Use grep/glob to find relevant sections first, then read specific line ranges.
Summarize findings — do not echo raw file contents back.
```

---

## 8. Design Patterns

### Pattern 1: Orchestrator (No Direct I/O)

Routes tasks to specialized subagents. Does not read/write files directly.

```yaml
model: anthropic/claude-sonnet-4-20250514
variant: low
mode: primary
description: >
  Routes development tasks to specialized agents.
  Use for multi-step projects requiring coordination.
permission:
  read: allow
  glob: allow
  grep: allow
  bash: deny
  edit: deny
  task:
    "*": deny
    "developer": allow
    "test-runner": allow
    "codebase-analyzer": allow
```

**When:** Complex workflows needing coordination. Cheap model + low reasoning since it only routes.

### Pattern 2: Delegating Worker (I/O + Delegation)

Has direct tool access and can delegate subtasks.

```yaml
model: anthropic/claude-sonnet-4-20250514
variant: high
mode: primary
description: >
  Implements features end-to-end. Delegates testing
  and code review to subagents.
permission:
  bash:
    "*": allow
    "git commit*": deny
    "git push*": deny
  edit:
    "*": allow
  read: allow
  task:
    "*": deny
    "test-runner": allow
    "reviewer": allow
```

**When:** Primary development agent. High reasoning for architectural decisions.

### Pattern 3: Leaf Node (No Delegation)

Does one thing well. No `task` permission.

```yaml
model: anthropic/claude-haiku-3.5-20241022
variant: low
mode: subagent
description: >
  Runs the test suite and reports results.
  Called after code changes to verify correctness.
permission:
  bash:
    "*": allow
    "git *": deny
  read: allow
  edit: deny
  task: deny
```

**When:** Single-purpose agents. Use cheapest model that handles the task.

### Pattern 4: Multi-Model Judge Panel

A head judge delegates to variant judges using different models, then merges verdicts.

```yaml
# head-judge.md
model: anthropic/claude-opus-4-20250514
variant: high
mode: primary
description: >
  Code review via multi-model consensus. Delegates to
  three judges with different models, merges verdicts.
permission:
  read: allow
  task:
    "*": deny
    "judge-sonnet": allow
    "judge-opus": allow
    "judge-gpt": allow
  edit: deny
  bash: deny
```

Each judge is a `subagent` with a different model. The head merges their verdicts for consensus. Prevents single-model blind spots.

---

## 9. Model Selection Guide

| Task Complexity       | Model Tier   | Example Models                        | `variant` |
|-----------------------|--------------|---------------------------------------|-----------|
| Simple/mechanical     | Haiku-class  | `anthropic/claude-haiku-3.5-20241022` | `low`     |
| Routine development   | Sonnet-class | `anthropic/claude-sonnet-4-20250514`  | `medium`  |
| Complex/architectural | Opus-class   | `anthropic/claude-opus-4-20250514`    | `high`    |
| Extreme reasoning     | Opus-class   | `anthropic/claude-opus-4-20250514`    | `max`     |

Match model cost to task difficulty. Orchestrators and leaf nodes can use cheaper models. Workers doing complex reasoning need stronger models.

---

## 10. Checklist for New Agents

Before shipping a new agent, verify:

- [ ] **Filename** is kebab-case (becomes the agent name)
- [ ] **`description`** is specific about when to use (<100 words, include trigger phrases)
- [ ] **`mode`** is appropriate (`primary` vs `subagent` vs `all`)
- [ ] **`model`** matches task complexity (Opus for hard, Sonnet for routine, Haiku for simple)
- [ ] **`variant`** matches reasoning depth needed
- [ ] **`permission`** follows least-privilege principle
- [ ] **`task` permissions** explicitly whitelist allowed subagents (default deny)
- [ ] **`bash`**: `git commit*` and `git push*` are denied (delegate to a committer agent)
- [ ] **Context protection** directives included if agent does context-heavy work
- [ ] **Delegation table** included if agent has subagents
- [ ] **Skill loading** instructions in a Project Discovery section
- [ ] **Tested** the agent interactively before committing

---

## 11. Complete Example: Feature Developer Agent

```yaml
---
model: anthropic/claude-sonnet-4-20250514
description: >
  Implements features and fixes bugs in the codebase. Use when: writing new code,
  modifying existing files, fixing errors, or refactoring. Delegates testing to
  @test-runner after changes.
mode: primary
variant: high
temperature: 0
color: "#4A9EFF"
permission:
  bash:
    "*": allow
    "git commit*": deny
    "git push*": deny
    "rm -rf /": deny
  edit:
    "*": allow
    "*.env": deny
    "*.pem": deny
  read: allow
  glob: allow
  grep: allow
  fetch: allow
  task:
    "*": deny
    "test-runner": allow
    "codebase-analyzer": allow
---

# Feature Developer

You are a senior software engineer. Implement features and fix bugs precisely.

## Project Discovery

skill({ name: "project-conventions" })

## Workflow

1. Understand the request — ask clarifying questions if ambiguous.
2. Research the codebase with grep/glob/read before writing code.
3. Implement changes in small, testable increments.
4. Delegate testing to @test-runner after each logical change.
5. Summarize what you changed and why.

## Delegation Guidelines

| Task Type        | Delegate To          | When                            |
|------------------|----------------------|---------------------------------|
| Run tests        | @test-runner         | After every code change         |
| Analyze codebase | @codebase-analyzer   | Before large refactors          |

## Context Management

Do not dump entire files into context. Use grep to find relevant sections,
then read specific line ranges. Summarize findings concisely.
```

---

## 12. Quick Reference: Frontmatter Template

Copy-paste starter for new agents:

```yaml
---
model: anthropic/claude-sonnet-4-20250514
description: >
  [What this agent does]. Use when: [trigger conditions].
mode: primary          # or: subagent, all
variant: medium        # low, medium, high, max
temperature: 0
permission:
  bash:
    "*": allow
    "git commit*": deny
    "git push*": deny
  edit:
    "*": allow
  read: allow
  glob: allow
  grep: allow
  task:
    "*": deny
---
```
