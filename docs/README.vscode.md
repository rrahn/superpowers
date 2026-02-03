# Superpowers for VS Code

Complete guide for using Superpowers with Visual Studio Code AI coding assistants.

## Overview

Unlike Claude Code or OpenCode, VS Code doesn't have a native plugin system for AI agent skills. However, you can integrate Superpowers with popular VS Code AI extensions:

- **[Continue.dev](https://continue.dev)** - Best option, supports custom commands and context providers
- **[GitHub Copilot Chat](https://github.com/features/copilot)** - Works with manual skill loading

## Quick Install (Continue.dev)

**Step 1:** Install Continue extension
```bash
code --install-extension Continue.continue
```

**Step 2:** Clone Superpowers
```bash
git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers
```

**Step 3:** Configure Continue

Edit `~/.continue/config.json` (create if it doesn't exist):

```json
{
  "models": [
    {
      "title": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "apiKey": "YOUR_ANTHROPIC_API_KEY"
    }
  ],
  "slashCommands": [
    {
      "name": "superpowers",
      "description": "Load Superpowers framework",
      "prompt": "Read and follow {{{ ~/.vscode/superpowers/skills/using-superpowers/SKILL.md }}}\n\n**Tool Mapping:** Skill tool → Continue slash commands, TodoWrite → update_plan, Task → sequential steps"
    },
    {
      "name": "skill",
      "description": "Load a specific skill",
      "prompt": "Read and follow {{{ ~/.vscode/superpowers/skills/{{{input}}}/SKILL.md }}}"
    },
    {
      "name": "brainstorm",
      "description": "Design refinement",
      "prompt": "Read and follow {{{ ~/.vscode/superpowers/skills/brainstorming/SKILL.md }}}"
    },
    {
      "name": "plan",
      "description": "Implementation planning",
      "prompt": "Read and follow {{{ ~/.vscode/superpowers/skills/writing-plans/SKILL.md }}}"
    },
    {
      "name": "tdd",
      "description": "Test-driven development",
      "prompt": "Read and follow {{{ ~/.vscode/superpowers/skills/test-driven-development/SKILL.md }}}"
    }
  ]
}
```

**Step 4:** Use it
- Open Continue sidebar (Ctrl+Shift+L)
- Type `/superpowers` to activate
- Use `/brainstorm`, `/plan`, `/tdd`, etc.

## Full Documentation

See [.vscode/INSTALL.md](../.vscode/INSTALL.md) for:
- Detailed installation for both Continue.dev and GitHub Copilot
- Windows-specific instructions
- Personal skills setup
- Project-specific configuration
- Troubleshooting guide

## How It Works

### Architecture

Unlike platforms with native plugin support:

1. **Skills are loaded via file reading** - Continue reads markdown files from `~/.vscode/superpowers/skills/`
2. **Slash commands trigger skill loading** - `/brainstorm` loads the brainstorming skill
3. **No automatic context** - You must explicitly load skills each session
4. **Sequential execution** - No parallel agent support

### Skill Discovery

Continue.dev uses slash commands configured in `~/.continue/config.json`. Each command reads a skill file and instructs the AI to follow it.

### Tool Mapping

When skills reference Claude Code tools, use these equivalents:

| Claude Code | VS Code/Continue |
|-------------|------------------|
| `Skill` tool | Continue slash commands (`/skill name`) |
| `TodoWrite` | `update_plan` or TODO comments |
| `Task` with subagents | Break into sequential steps |
| File operations | Native Continue file operations |
| `Bash` | VS Code integrated terminal |

## Available Skills

All skills from the core Superpowers library are available:

**Development Workflows:**
- `brainstorming` - Interactive design refinement
- `writing-plans` - Detailed implementation plans
- `executing-plans` - Batch execution with checkpoints
- `subagent-driven-development` - Fast iteration workflow
- `using-git-worktrees` - Parallel branch development
- `finishing-a-development-branch` - Merge/PR workflow

**Quality & Testing:**
- `test-driven-development` - RED-GREEN-REFACTOR cycle
- `requesting-code-review` - Pre-review checklist
- `receiving-code-review` - Responding to feedback
- `verification-before-completion` - Verification checks

**Debugging:**
- `systematic-debugging` - 4-phase root cause process

**Meta:**
- `using-superpowers` - Framework introduction
- `writing-skills` - Create new skills

Load any skill with:
```
/skill <skill-name>
```

## Differences from Claude Code

### What's Missing

1. **Automatic skill activation** - Must manually load skills
2. **Native tool integration** - Skills loaded via file reading
3. **Parallel agents** - Must use sequential execution
4. **TodoWrite tool** - Use Continue's `update_plan` instead

### What Works

1. **All skill content** - Full skill library available
2. **Workflows** - TDD, brainstorming, planning all work
3. **Personal skills** - Create your own in `~/.vscode/superpowers-personal/`
4. **Project skills** - Project-specific skills via `.continue/config.json`

## Workflow Examples

### Starting a New Feature

```
1. /superpowers          # Load framework
2. /brainstorm           # Design the feature
3. /plan                 # Create implementation plan
4. /tdd                  # Switch to TDD mode
5. [implement]
6. /skill requesting-code-review  # Pre-review check
```

### Debugging an Issue

```
1. /superpowers          # Load framework
2. /debug                # Load systematic debugging
3. [follow the process]
4. /skill verification-before-completion  # Verify fix
```

### Code Review

```
1. /superpowers          # Load framework
2. /skill requesting-code-review  # Before submitting
   [or]
3. /skill receiving-code-review   # Responding to feedback
```

## Project Configuration

### Per-Project Setup

Create `.continue/config.json` in your project root to enable Superpowers automatically for that project:

```json
{
  "slashCommands": [
    {
      "name": "init",
      "description": "Initialize with Superpowers",
      "prompt": "Read {{{ ~/.vscode/superpowers/skills/using-superpowers/SKILL.md }}} and activate Superpowers framework. Use /brainstorm to start design discussions."
    }
  ]
}
```

Then developers just type `/init` when opening the project.

### Project-Specific Skills

Add project-specific workflows:

```json
{
  "slashCommands": [
    {
      "name": "api",
      "description": "Our API development workflow",
      "prompt": "Follow our API development process:\n1. Load /tdd for test-driven development\n2. Ensure OpenAPI spec is updated\n3. Add integration tests\n4. Update API documentation"
    }
  ]
}
```

## Comparison Table

| Feature | Claude Code | Continue.dev | Copilot Chat |
|---------|-------------|--------------|--------------|
| Automatic context | ✅ | ❌ | ❌ |
| Slash commands | ✅ | ✅ | ❌ |
| Parallel agents | ✅ | ❌ | ❌ |
| TodoWrite tool | ✅ | ⚠️ (update_plan) | ⚠️ (comments) |
| Skill discovery | ✅ | ⚠️ (config) | ❌ |
| Personal skills | ✅ | ✅ | ❌ |
| Project skills | ✅ | ✅ | ⚠️ (snippets) |
| Cost | Subscription | Your API | Subscription |

✅ = Full support | ⚠️ = Partial/workaround | ❌ = Not available

## Updating

```bash
cd ~/.vscode/superpowers
git pull
```

Restart VS Code to pick up changes.

## Tips & Best Practices

### 1. Load Framework First

Always start with `/superpowers` to establish context:
```
/superpowers
```

### 2. One Skill at a Time

Load skills as needed rather than all at once:
```
/brainstorm    # For design
/plan          # For planning
/tdd           # For implementation
```

### 3. Use Project Config

Set up `.continue/config.json` in your project for team-wide consistency.

### 4. Create Aliases

Add short aliases for frequently used skills:
```json
{
  "slashCommands": [
    {
      "name": "b",
      "description": "Brainstorm (short)",
      "prompt": "Read {{{ ~/.vscode/superpowers/skills/brainstorming/SKILL.md }}}"
    }
  ]
}
```

### 5. Combine with Continue Features

Use Continue's context providers alongside Superpowers:
```json
{
  "contextProviders": [
    {
      "name": "diff"
    },
    {
      "name": "terminal"
    },
    {
      "name": "superpowers",
      "params": {
        "type": "file",
        "path": "~/.vscode/superpowers/skills/using-superpowers/SKILL.md"
      }
    }
  ]
}
```

## Known Limitations

### Sequential Only

Skills that reference parallel agents (like `dispatching-parallel-agents`) need adaptation. Break into sequential steps:

```
Instead of: Launch 3 agents in parallel
Do: Task 1 → Task 2 → Task 3 sequentially
```

### Manual Loading

Unlike Claude Code's automatic skill discovery, you must explicitly load skills each chat session. Consider:

1. Start each session with `/superpowers`
2. Create a "startup" command in your config
3. Use project-specific config to auto-remind

### File Path Dependencies

Skills loaded via file reading means:
- File paths must be correct for your OS
- Skills must be kept in sync (use `git pull`)
- No dynamic skill generation

## Getting Help

- **Installation issues**: See [.vscode/INSTALL.md](../.vscode/INSTALL.md)
- **Continue.dev help**: https://docs.continue.dev
- **Report bugs**: https://github.com/obra/superpowers/issues
- **Main docs**: https://github.com/obra/superpowers

## Alternative Platforms

For the best Superpowers experience:

1. **[Claude Code](https://claude.ai/code)** - Native plugin support, automatic context, all features ✅
2. **[OpenCode.ai](https://opencode.ai)** - Plugin system, native skills ✅
3. **[Codex](https://openai.com/codex)** - CLI-based, good integration ⚠️
4. **VS Code** - Works but requires manual setup ⚠️

## Contributing

Help improve VS Code integration:

1. Test on different platforms (Windows, Mac, Linux)
2. Try different Continue configurations
3. Report what works and what doesn't
4. Share your Continue config files
5. Document workarounds for limitations

Submit improvements via [GitHub issues](https://github.com/obra/superpowers/issues).
