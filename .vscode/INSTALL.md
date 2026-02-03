# Installing Superpowers for VS Code

VS Code doesn't have a built-in plugin system for AI coding agents, but you can use Superpowers with popular AI assistant extensions like **Continue.dev** or **GitHub Copilot**.

## Prerequisites

- [Visual Studio Code](https://code.visualstudio.com) installed
- One of these AI assistant extensions:
  - [Continue](https://marketplace.visualstudio.com/items?itemName=Continue.continue) (recommended - open source, customizable)
  - [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) with Chat enabled

## Option 1: Continue.dev Integration (Recommended)

Continue.dev supports custom context providers and instructions, making it ideal for Superpowers integration.

### Installation Steps

#### 1. Install Continue Extension

Install from VS Code marketplace or via command line:
```bash
code --install-extension Continue.continue
```

#### 2. Clone Superpowers

Clone to your home directory or preferred location:

```bash
# macOS / Linux
git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers

# Windows (PowerShell)
git clone https://github.com/obra/superpowers.git "$env:USERPROFILE\.vscode\superpowers"

# Windows (Command Prompt)
git clone https://github.com/obra/superpowers.git "%USERPROFILE%\.vscode\superpowers"
```

#### 3. Configure Continue

Create or edit Continue's configuration file:

**Location:**
- macOS / Linux: `~/.continue/config.json`
- Windows: `%USERPROFILE%\.continue\config.json`

**Add Superpowers context provider:**

```json
{
  "models": [
    {
      "title": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "apiKey": "YOUR_API_KEY"
    }
  ],
  "customCommands": [
    {
      "name": "superpowers",
      "description": "Load Superpowers skills framework",
      "prompt": "Read the file {{{ ~/.vscode/superpowers/skills/using-superpowers/SKILL.md }}} and follow its instructions. This is the Superpowers framework for AI coding agents.\n\n**IMPORTANT:** You are now following the using-superpowers skill. It is ALREADY LOADED - do NOT try to load it again.\n\n**Tool Mapping for VS Code/Continue:**\n- `Skill` tool → Use Continue's custom commands to load skills from ~/.vscode/superpowers/skills/\n- `TodoWrite` → Use Continue's `update_plan` or create TODO comments\n- `Task` with subagents → Break into sequential steps (Continue doesn't support parallel agents)\n- File operations → Use Continue's native file operations\n\n**Skills location:**\nAll skills are in `~/.vscode/superpowers/skills/` - reference them by reading the SKILL.md file in each skill directory."
    }
  ],
  "slashCommands": [
    {
      "name": "skill",
      "description": "Load a Superpowers skill",
      "prompt": "Read and follow the instructions in ~/.vscode/superpowers/skills/{{{input}}}/SKILL.md"
    },
    {
      "name": "brainstorm",
      "description": "Interactive design refinement",
      "prompt": "Read and follow ~/.vscode/superpowers/skills/brainstorming/SKILL.md"
    },
    {
      "name": "plan",
      "description": "Create implementation plan",
      "prompt": "Read and follow ~/.vscode/superpowers/skills/writing-plans/SKILL.md"
    },
    {
      "name": "tdd",
      "description": "Test-driven development workflow",
      "prompt": "Read and follow ~/.vscode/superpowers/skills/test-driven-development/SKILL.md"
    },
    {
      "name": "debug",
      "description": "Systematic debugging process",
      "prompt": "Read and follow ~/.vscode/superpowers/skills/systematic-debugging/SKILL.md"
    }
  ],
  "contextProviders": [
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

**Adjust the configuration:**
- Replace `YOUR_API_KEY` with your Anthropic API key
- Update file paths if you cloned to a different location
- You can add other models (OpenAI, local models, etc.) as needed

#### 4. Verify Installation

1. Restart VS Code
2. Open Continue sidebar (Ctrl+Shift+L / Cmd+Shift+L)
3. Type `/superpowers` to load the framework
4. Type `/skill brainstorming` to test loading a specific skill

### Usage with Continue

#### Loading the Framework

At the start of any new chat, type:
```
/superpowers
```

This loads the base Superpowers framework and context.

#### Loading Specific Skills

Use the `/skill` command:
```
/skill brainstorming
/skill writing-plans
/skill test-driven-development
/skill systematic-debugging
```

Or use convenient shortcuts:
```
/brainstorm
/plan
/tdd
/debug
```

#### Project-Specific Configuration

You can also add Superpowers to a specific project by creating `.continue/config.json` in your project root with the same configuration.

### Personal Skills

Create your own skills in `~/.vscode/superpowers-personal/`:

```bash
mkdir -p ~/.vscode/superpowers-personal/my-skill
```

Create `~/.vscode/superpowers-personal/my-skill/SKILL.md`:

```markdown
---
name: my-skill
description: Use when [condition] - [what it does]
---

# My Skill

[Your skill content here]
```

Add to Continue config:
```json
{
  "slashCommands": [
    {
      "name": "my-skill",
      "description": "My custom skill",
      "prompt": "Read and follow ~/.vscode/superpowers-personal/my-skill/SKILL.md"
    }
  ]
}
```

## Option 2: GitHub Copilot Integration

GitHub Copilot Chat can also work with Superpowers, though it requires manual context loading.

### Installation Steps

#### 1. Install GitHub Copilot

Install both extensions from VS Code marketplace:
```bash
code --install-extension GitHub.copilot
code --install-extension GitHub.copilot-chat
```

#### 2. Clone Superpowers

```bash
# macOS / Linux
git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers

# Windows (PowerShell)
git clone https://github.com/obra/superpowers.git "$env:USERPROFILE\.vscode\superpowers"
```

#### 3. Create Workspace Snippets (Optional)

To make loading skills easier, create VS Code snippets:

**File:** `.vscode/superpowers.code-snippets` (in your project)

```json
{
  "Load Superpowers": {
    "prefix": "!superpowers",
    "body": [
      "Read and follow the instructions in ~/.vscode/superpowers/skills/using-superpowers/SKILL.md",
      "",
      "Tool Mapping for VS Code:",
      "- Skill tool → Ask me to read skill files from ~/.vscode/superpowers/skills/",
      "- TodoWrite → Use TODO comments or task tracking",
      "- Task with subagents → Break into sequential steps",
      "- File operations → Use my native file operations"
    ],
    "description": "Load Superpowers framework"
  },
  "Load Skill": {
    "prefix": "!skill",
    "body": [
      "Read and follow the instructions in ~/.vscode/superpowers/skills/${1:skill-name}/SKILL.md"
    ],
    "description": "Load a specific Superpowers skill"
  }
}
```

### Usage with GitHub Copilot

1. Open Copilot Chat (Ctrl+Shift+I / Cmd+Shift+I)
2. Paste or use snippet to load framework:
   ```
   Read and follow the instructions in ~/.vscode/superpowers/skills/using-superpowers/SKILL.md
   ```
3. Load specific skills as needed:
   ```
   Read and follow ~/.vscode/superpowers/skills/brainstorming/SKILL.md
   ```

**Note:** GitHub Copilot doesn't support custom slash commands, so you'll need to manually reference skill files each session.

## Skill Locations

Skills are organized in the `skills/` directory:

```
~/.vscode/superpowers/skills/
├── using-superpowers/      # Core framework
├── brainstorming/           # Design refinement
├── writing-plans/           # Implementation planning
├── executing-plans/         # Batch execution
├── test-driven-development/ # TDD workflow
├── systematic-debugging/    # Debugging process
├── requesting-code-review/  # Pre-review checklist
├── receiving-code-review/   # Responding to feedback
├── using-git-worktrees/     # Parallel branches
├── finishing-a-development-branch/ # Merge/PR workflow
├── subagent-driven-development/    # Fast iteration
├── dispatching-parallel-agents/    # Concurrent workflows
├── verification-before-completion/ # Verification checks
└── writing-skills/          # Creating new skills
```

## Tool Mapping Reference

When skills reference Claude Code tools, map to VS Code equivalents:

| Claude Code Tool | VS Code / Continue Equivalent |
|------------------|-------------------------------|
| `Skill` | Continue slash commands or file reading |
| `TodoWrite` | `update_plan` or TODO comments |
| `Task` with subagents | Sequential steps (no parallel support) |
| `Read`, `Write`, `Edit` | Native Continue file operations |
| `Bash` | VS Code terminal integration |

## Updating

```bash
cd ~/.vscode/superpowers
git pull
```

Restart VS Code to load updates.

## Troubleshooting

### Skills not loading

1. Verify clone location: `ls ~/.vscode/superpowers/skills`
2. Check file paths in your Continue config match your installation
3. On Windows, use backslashes or forward slashes consistently
4. Restart VS Code after configuration changes

### Continue custom commands not working

1. Check Continue config syntax: `~/.continue/config.json`
2. Ensure JSON is valid (no trailing commas)
3. Check Continue extension logs: View → Output → Continue

### File path issues on Windows

If using Windows, you may need to adjust paths in the config:
- Use forward slashes: `C:/Users/YourName/.vscode/superpowers/...`
- Or escape backslashes: `C:\\Users\\YourName\\.vscode\\superpowers\\...`
- Or use PowerShell-style variables: `$env:USERPROFILE\.vscode\superpowers\...`

### Skills reference outdated

Skills evolve. Always load the current version from files, don't rely on memory.

## Getting Help

- Report issues: https://github.com/obra/superpowers/issues
- Main documentation: https://github.com/obra/superpowers
- Continue docs: https://docs.continue.dev
- Copilot docs: https://docs.github.com/copilot

## Limitations

**VS Code Integration Limitations:**

1. **No automatic context injection** - Unlike Claude Code's native plugin system, you must manually load skills each session
2. **No parallel agent support** - Continue and Copilot run sequentially, so skills that use parallel agents need adaptation
3. **File reading overhead** - Skills are loaded by reading markdown files rather than native tool invocation
4. **No native TodoWrite** - Use Continue's `update_plan` or create TODO comments instead

**Despite these limitations**, Superpowers provides valuable workflows and discipline for AI-assisted development in VS Code.

## Alternative: Use Claude Code

For the best Superpowers experience, consider using [Claude Code](https://claude.ai/code) which has native plugin support and all features working out of the box.
