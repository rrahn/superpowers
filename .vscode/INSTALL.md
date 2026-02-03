# Installing Superpowers for VS Code with GitHub Copilot Chat

VS Code doesn't have a built-in plugin system for AI coding agents, but you can use Superpowers with **GitHub Copilot Chat** through VS Code code snippets.

## Prerequisites

- [Visual Studio Code](https://code.visualstudio.com) installed
- [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) subscription
- [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) extension installed
- Git installed

## Installation Steps

### Step 1: Install GitHub Copilot Extensions

Install both Copilot extensions from VS Code marketplace:

```bash
code --install-extension GitHub.copilot
code --install-extension GitHub.copilot-chat
```

Or install from the VS Code Extensions marketplace (Ctrl+Shift+X / Cmd+Shift+X).

### Step 2: Clone Superpowers

Clone the repository to your system:

**macOS / Linux:**
```bash
git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/obra/superpowers.git "$env:USERPROFILE\.vscode\superpowers"
```

**Windows (Command Prompt):**
```cmd
git clone https://github.com/obra/superpowers.git "%USERPROFILE%\.vscode\superpowers"
```

### Step 3: Set Up Code Snippets

You have two options for setting up the snippets:

#### Option A: Global Snippets (Recommended)

Copy the snippets file to your global VS Code configuration:

**macOS / Linux:**
```bash
mkdir -p ~/Library/Application\ Support/Code/User/snippets/
cp ~/.vscode/superpowers/.vscode/superpowers.code-snippets ~/Library/Application\ Support/Code/User/snippets/
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path "$env:APPDATA\Code\User\snippets"
Copy-Item "$env:USERPROFILE\.vscode\superpowers\.vscode\superpowers.code-snippets" "$env:APPDATA\Code\User\snippets\"
```

**Windows (Command Prompt):**
```cmd
mkdir "%APPDATA%\Code\User\snippets" 2>nul
copy "%USERPROFILE%\.vscode\superpowers\.vscode\superpowers.code-snippets" "%APPDATA%\Code\User\snippets\"
```

#### Option B: Project-Specific Snippets

Copy the snippets to each project where you want to use Superpowers:

```bash
# In your project directory
mkdir -p .vscode
cp ~/.vscode/superpowers/.vscode/superpowers.code-snippets .vscode/
```

### Step 4: Verify Installation

1. Open VS Code
2. Open Copilot Chat (Ctrl+Shift+I / Cmd+Shift+I)
3. In the chat input, type `!superpowers` and press Tab
4. You should see the snippet expand with framework loading instructions
5. Press Enter to send the message to Copilot

## Usage

### Loading the Framework

At the start of any new Copilot Chat session:

1. Open Copilot Chat (Ctrl+Shift+I / Cmd+Shift+I)
2. Type `!superpowers` and press Tab
3. Press Enter to send

This loads the Superpowers framework and makes all skills available.

### Loading Specific Skills

Use the snippet shortcuts to load individual skills:

| Snippet | Skill | Purpose |
|---------|-------|---------|
| `!superpowers` | Framework | Load core framework |
| `!skill` | Generic | Load any skill by name |
| `!brainstorm` | Brainstorming | Design refinement |
| `!plan` | Writing Plans | Implementation planning |
| `!tdd` | Test-Driven Development | TDD workflow |
| `!debug` | Systematic Debugging | Debugging process |
| `!review` | Code Review | Pre-review checklist |
| `!verify` | Verification | Verify completion |
| `!worktree` | Git Worktrees | Parallel branches |
| `!skills` | List | Show all available skills |

**Usage pattern:**
1. Type the snippet prefix (e.g., `!brainstorm`)
2. Press Tab to expand
3. Press Enter to send to Copilot

### Example Workflow

**Creating a new feature:**
```
1. Open Copilot Chat
2. Type: !superpowers [Tab] [Enter]
   (Framework loads)
3. Type: !brainstorm [Tab] [Enter]
   (Start design discussion)
4. Answer Copilot's questions
5. Type: !plan [Tab] [Enter]
   (Create implementation plan)
6. Type: !tdd [Tab] [Enter]
   (Switch to TDD mode)
7. Implement the feature
8. Type: !review [Tab] [Enter]
   (Run pre-review checks)
```

## Skill Locations

All skills are available in the cloned repository:

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

When skills reference Claude Code tools, Copilot Chat uses these equivalents:

| Claude Code Tool | GitHub Copilot Chat Equivalent |
|------------------|--------------------------------|
| `Skill` | Snippet expansion + file reading |
| `TodoWrite` | TODO/FIXME comments in code |
| `Task` with subagents | Sequential steps (no parallel support) |
| `Read`, `Write`, `Edit` | Native Copilot file operations |
| `Bash` | VS Code integrated terminal |

## Updating

Pull the latest changes from the repository:

```bash
cd ~/.vscode/superpowers
git pull
```

After updating, restart VS Code or reload the window (Ctrl+Shift+P / Cmd+Shift+P → "Reload Window").

## Troubleshooting

### Snippets not expanding

1. **Check snippet file location:**
   - Global: `~/Library/Application Support/Code/User/snippets/` (Mac) or `%APPDATA%\Code\User\snippets\` (Windows)
   - Project: `.vscode/superpowers.code-snippets` in your project

2. **Verify snippet syntax:**
   - Open the snippets file and ensure it's valid JSON
   - No trailing commas, proper formatting

3. **Try different scope:**
   - Snippets work in Copilot Chat input
   - Press Tab after typing the prefix
   - Make sure you're in the chat input, not the editor

### Skills not loading

1. **Verify repository clone:**
   ```bash
   ls ~/.vscode/superpowers/skills/
   ```
   Should show all skill directories

2. **Check file paths in snippets:**
   - On Windows, paths may need adjustment
   - Use forward slashes: `C:/Users/...` or escape backslashes: `C:\\Users\\...`

3. **Restart VS Code:**
   - Sometimes needed after adding snippets
   - Ctrl+Shift+P / Cmd+Shift+P → "Reload Window"

### Copilot doesn't follow skill instructions

1. **Framework must be loaded first:**
   - Use `!superpowers` at the start of each chat session
   - This establishes context

2. **Skills reference outdated:**
   - Always use current file content
   - Run `git pull` to update

3. **Clear and restart:**
   - Start a new Copilot Chat session
   - Load framework fresh with `!superpowers`

### File path issues on Windows

If using Windows, you may need to adjust paths:

- **Use forward slashes:** `C:/Users/YourName/.vscode/superpowers/...`
- **Or escape backslashes:** `C:\\Users\\YourName\\.vscode\\superpowers\\...`
- **Or use variables:** `%USERPROFILE%\.vscode\superpowers\...` (may not work in all contexts)

The snippets use `~/.vscode/superpowers/` which typically works on all platforms when Copilot reads the files.

## Creating Personal Skills

You can create your own skills in a separate directory:

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

Then add a snippet for it in your snippets file:

```json
{
  "My Custom Skill": {
    "prefix": "!myskill",
    "body": [
      "Read and follow ~/.vscode/superpowers-personal/my-skill/SKILL.md"
    ],
    "description": "Load my custom skill"
  }
}
```

## Known Limitations

**GitHub Copilot Chat Integration Limitations:**

1. **Manual loading required** - Must use snippets to load framework each session (no automatic context injection)
2. **No slash commands** - Unlike Continue.dev, Copilot doesn't support custom slash commands
3. **Snippet-based approach** - Less elegant than native command systems
4. **No parallel agent support** - Skills using parallel agents must adapt to sequential execution
5. **Session-based** - Framework context lost when starting new chat session

**Despite these limitations**, Superpowers provides valuable workflows and discipline for AI-assisted development with GitHub Copilot in VS Code.

## Getting Help

- **Report issues:** https://github.com/obra/superpowers/issues
- **Main documentation:** https://github.com/obra/superpowers
- **Copilot docs:** https://docs.github.com/copilot

## Alternative Platforms

For a better Superpowers experience with more native integration:

1. **[Claude Code](https://claude.ai/code)** - Native plugin support, automatic context, all features ✅
2. **[OpenCode.ai](https://opencode.ai)** - Plugin system, native skills ✅
3. **VS Code** - Works with GitHub Copilot, but requires manual setup ⚠️

See the [platform comparison](../docs/platform-comparison.md) for more details.
