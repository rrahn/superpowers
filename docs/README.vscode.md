# Superpowers for VS Code with GitHub Copilot Chat

Complete guide for using Superpowers with Visual Studio Code and GitHub Copilot Chat.

## Overview

VS Code doesn't have a native plugin system for AI agent skills like Claude Code or OpenCode. To use Superpowers with VS Code, we leverage **GitHub Copilot Chat** through VS Code code snippets.

This provides a functional integration that brings Superpowers workflows to the world's most popular code editor.

## Quick Install

**Requirements:**
- VS Code
- GitHub Copilot subscription
- Git

**Setup (5 minutes):**
```bash
# 1. Install Copilot extensions
code --install-extension GitHub.copilot
code --install-extension GitHub.copilot-chat

# 2. Clone Superpowers
git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers

# 3. Copy snippets (macOS example)
mkdir -p ~/Library/Application\ Support/Code/User/snippets/
cp ~/.vscode/superpowers/.vscode/superpowers.code-snippets ~/Library/Application\ Support/Code/User/snippets/

# 4. Restart VS Code and use: !superpowers in Copilot Chat
```

See [.vscode/QUICKSTART.md](../.vscode/QUICKSTART.md) for platform-specific instructions.

## Full Documentation

- **[.vscode/INSTALL.md](../.vscode/INSTALL.md)** - Complete installation guide (all platforms)
- **[.vscode/QUICKSTART.md](../.vscode/QUICKSTART.md)** - 5-minute setup guide
- **[.vscode/TESTING.md](../.vscode/TESTING.md)** - Testing and verification

## How It Works

### Architecture

Unlike platforms with native plugin support, VS Code integration uses a snippet-based approach:

```
Code Snippet → Expand in Chat → File Read → Copilot Follows Instructions
     ↓              ↓               ↓                    ↓
 !superpowers    [Tab]         Read SKILL.md      Apply framework
```

**Workflow:**
1. User types snippet prefix in Copilot Chat (e.g., `!superpowers`)
2. Presses Tab to expand snippet
3. Snippet contains instruction to read skill file
4. Presses Enter to send to Copilot
5. Copilot reads the skill markdown file
6. Copilot follows the skill instructions

### Skill Discovery

Skills are loaded manually via snippets:

| Snippet | Skill | Purpose |
|---------|-------|---------|
| `!superpowers` | Framework | Core framework |
| `!brainstorm` | Brainstorming | Design refinement |
| `!plan` | Writing Plans | Implementation planning |
| `!tdd` | Test-Driven Development | TDD workflow |
| `!debug` | Systematic Debugging | Debugging process |
| `!review` | Code Review | Pre-review checklist |
| `!verify` | Verification | Verify completion |
| `!skill` | Generic | Load any skill by name |

### Tool Mapping

When skills reference Claude Code tools, Copilot Chat uses these equivalents:

| Claude Code | GitHub Copilot Chat |
|-------------|---------------------|
| `Skill` tool | Snippet expansion + file reading |
| `TodoWrite` | TODO/FIXME comments in code |
| `Task` with subagents | Sequential steps (no parallel) |
| `Read`, `Write`, `Edit` | Native Copilot file operations |
| `Bash` | VS Code integrated terminal |

## Available Skills

All skills from the core Superpowers library work with Copilot Chat:

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

Load any skill with the corresponding snippet (e.g., `!tdd` for test-driven development).

## Workflow Examples

### Starting a New Feature

```
Open Copilot Chat (Ctrl+Shift+I / Cmd+Shift+I)

1. !superpowers [Tab] [Enter]       # Load framework
2. !brainstorm [Tab] [Enter]        # Design the feature
3. Answer Copilot's questions
4. !plan [Tab] [Enter]              # Create implementation plan
5. !tdd [Tab] [Enter]               # Switch to TDD mode
6. Implement the feature
7. !review [Tab] [Enter]            # Pre-review check
```

### Debugging an Issue

```
Open Copilot Chat

1. !superpowers [Tab] [Enter]       # Load framework
2. !debug [Tab] [Enter]             # Load systematic debugging
3. Follow the 4-phase process
4. !verify [Tab] [Enter]            # Verify fix works
```

### Code Review

```
Open Copilot Chat

1. !superpowers [Tab] [Enter]       # Load framework
2. !review [Tab] [Enter]            # Pre-review checklist
   [or]
3. !review-response [Tab] [Enter]   # Respond to feedback
```

## Project Configuration

### Team Setup

For team projects, include snippets in the repository:

```bash
# In your project root
mkdir -p .vscode
cp ~/.vscode/superpowers/.vscode/superpowers.code-snippets .vscode/
```

Add to `.vscode/settings.json`:
```json
{
  "files.associations": {
    "*.code-snippets": "jsonc"
  }
}
```

Team members clone the project and get snippets automatically.

### Project-Specific Skills

Create project-specific skills in `.vscode/skills/`:

```bash
mkdir -p .vscode/skills/my-project-workflow
```

Create `.vscode/skills/my-project-workflow/SKILL.md`:
```markdown
---
name: my-project-workflow
description: Use for this project's specific workflow
---

# Project Workflow

[Your project-specific instructions]
```

Add snippet to `.vscode/superpowers.code-snippets`:
```json
{
  "Project Workflow": {
    "prefix": "!workflow",
    "body": [
      "Read and follow .vscode/skills/my-project-workflow/SKILL.md"
    ],
    "description": "Load project-specific workflow"
  }
}
```

## Differences from Other Platforms

### What's Missing

Compared to Claude Code:

1. **No automatic context injection** - Must manually load with `!superpowers` each session
2. **No native slash commands** - Uses VS Code snippets instead
3. **No parallel agents** - Must use sequential execution
4. **Snippet-based approach** - Less elegant than native commands
5. **Session-based context** - Lost when starting new chat

### What Works

1. **All skill content** - Full skill library accessible
2. **All workflows** - TDD, brainstorming, planning all functional
3. **Personal skills** - Create your own in `~/.vscode/superpowers-personal/`
4. **Project skills** - Project-specific workflows supported
5. **Tool mapping** - All tools have Copilot equivalents

## Tips & Best Practices

### 1. Load Framework First

Always start Copilot Chat sessions with:
```
!superpowers [Tab] [Enter]
```

This establishes the Superpowers context.

### 2. One Skill at a Time

Load skills as needed:
```
!brainstorm    # For design
!plan          # For planning
!tdd           # For implementation
```

### 3. Use Project Snippets

Add `.vscode/superpowers.code-snippets` to your projects for team-wide consistency.

### 4. Create Shortcuts

Customize snippets for frequently-used workflows:
```json
{
  "Quick Start": {
    "prefix": "!start",
    "body": [
      "Read ~/.vscode/superpowers/skills/using-superpowers/SKILL.md",
      "Read ~/.vscode/superpowers/skills/brainstorming/SKILL.md",
      "Let's brainstorm this feature"
    ]
  }
}
```

### 5. New Session = Reload

When starting a new Copilot Chat:
- Framework context is lost
- Reload with `!superpowers`
- Then load specific skills

## Known Limitations

### Sequential Only

Skills that use parallel agents need adaptation:

```
Instead of: Launch 3 agents in parallel
Do: Task 1 → Task 2 → Task 3 sequentially
```

### Manual Loading

Unlike Claude Code's automatic skill discovery:
1. Must explicitly load framework each session
2. Snippet-based approach more manual
3. No automatic context injection

### Snippet Scope

Snippets only work in Copilot Chat input, not in code files. This is by design.

## Troubleshooting

### Snippets Not Expanding

1. **Check snippet location:**
   - Mac: `~/Library/Application Support/Code/User/snippets/`
   - Windows: `%APPDATA%\Code\User\snippets\`
   - Linux: `~/.config/Code/User/snippets/`

2. **Restart VS Code:**
   - Ctrl+Shift+P → "Reload Window"

3. **Use in Chat:**
   - Snippets work in Copilot Chat input only
   - Press Tab after typing prefix

### Skills Not Loading

1. **Verify repository:**
   ```bash
   ls ~/.vscode/superpowers/skills/
   ```

2. **Check paths:**
   - Snippets use `~/.vscode/superpowers/`
   - Should work on all platforms via Copilot

3. **Update repository:**
   ```bash
   cd ~/.vscode/superpowers && git pull
   ```

### Context Lost

**Expected behavior:**
- Copilot Chat context is session-based
- Starting new chat loses framework context
- Reload with `!superpowers` at start of each session

This is a platform limitation, not a bug.

## Updating

```bash
cd ~/.vscode/superpowers
git pull
```

Restart VS Code to pick up changes.

## Comparison to Other Platforms

| Feature | Claude Code | OpenCode | VS Code (Copilot) |
|---------|-------------|----------|-------------------|
| Setup Time | 2 min | 5 min | 5-10 min |
| Auto Context | ✅ | ✅ | ❌ |
| Slash Commands | ✅ | ✅ | ❌ (snippets) |
| Parallel Agents | ✅ | ⚠️ | ❌ |
| Personal Skills | ✅ | ✅ | ✅ |
| Project Skills | ✅ | ✅ | ✅ |
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

**Best overall experience:** Claude Code (native plugin, all features)

**Best for VS Code users:** This integration (works with existing setup)

See [platform comparison](platform-comparison.md) for detailed analysis.

## Getting Help

- **Installation issues:** See [.vscode/INSTALL.md](../.vscode/INSTALL.md)
- **GitHub Copilot help:** https://docs.github.com/copilot
- **Report bugs:** https://github.com/obra/superpowers/issues
- **Main docs:** https://github.com/obra/superpowers

## Alternative Platforms

For better Superpowers experience:

1. **[Claude Code](https://claude.ai/code)** - Native plugin, automatic context, all features ✅
2. **[OpenCode.ai](https://opencode.ai)** - Plugin system, native skills ✅
3. **VS Code with Copilot** - Works but requires manual setup ⚠️

## Contributing

Help improve VS Code integration:

1. Test on different platforms (Windows, Mac, Linux)
2. Try different workflows
3. Report what works and what doesn't
4. Share your snippet configurations
5. Document workarounds

Submit feedback via [GitHub issues](https://github.com/obra/superpowers/issues).
