# VS Code Superpowers Quick Start

Get up and running with Superpowers in VS Code in 5 minutes.

## Prerequisites

- VS Code installed
- Continue.dev extension (or GitHub Copilot Chat)
- An Anthropic API key (for Claude) or other LLM provider

## Option 1: Continue.dev (Recommended)

### 1. Install Continue

```bash
code --install-extension Continue.continue
```

### 2. Clone Superpowers

**macOS / Linux:**
```bash
git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/obra/superpowers.git "$env:USERPROFILE\.vscode\superpowers"
```

### 3. Copy Example Config

**macOS / Linux:**
```bash
# Create Continue config directory
mkdir -p ~/.continue

# Copy example config
cp ~/.vscode/superpowers/.vscode/continue-config.example.json ~/.continue/config.json

# Edit to add your API key
# Replace YOUR_ANTHROPIC_API_KEY with your actual key
```

**Windows (PowerShell):**
```powershell
# Create Continue config directory
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.continue"

# Copy example config
Copy-Item "$env:USERPROFILE\.vscode\superpowers\.vscode\continue-config.example.json" "$env:USERPROFILE\.continue\config.json"

# Edit to add your API key
# Replace YOUR_ANTHROPIC_API_KEY with your actual key
```

### 4. Edit Config

Open `~/.continue/config.json` (or `%USERPROFILE%\.continue\config.json` on Windows) and replace:
```json
"apiKey": "YOUR_ANTHROPIC_API_KEY"
```

With your actual Anthropic API key.

### 5. Test It!

1. Restart VS Code
2. Open Continue sidebar: `Ctrl+Shift+L` (Windows/Linux) or `Cmd+Shift+L` (Mac)
3. Type: `/superpowers`
4. You should see it load the framework!

### 6. Try a Skill

Type any of these:
- `/brainstorm` - Start a design discussion
- `/plan` - Create an implementation plan
- `/tdd` - Switch to test-driven development mode
- `/debug` - Load systematic debugging

## Option 2: GitHub Copilot

### 1. Install Copilot

```bash
code --install-extension GitHub.copilot
code --install-extension GitHub.copilot-chat
```

### 2. Clone Superpowers

Same as Continue.dev instructions above.

### 3. Copy Snippets to Your Project

In your project, create `.vscode/` directory:
```bash
mkdir -p .vscode
cp ~/.vscode/superpowers/.vscode/superpowers.code-snippets .vscode/
```

### 4. Use Snippets

1. Open Copilot Chat: `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Shift+I` (Mac)
2. Type `!superpowers` in the chat input and press Tab
3. Press Enter to send the message
4. Copilot will load the framework!

**Note:** With Copilot, you need to load the framework manually each session.

## Quick Reference

### Continue.dev Commands

| Command | Purpose |
|---------|---------|
| `/superpowers` | Load framework |
| `/brainstorm` | Design refinement |
| `/plan` | Implementation planning |
| `/tdd` | Test-driven development |
| `/debug` | Systematic debugging |
| `/review` | Pre-code-review check |
| `/skill <name>` | Load any skill |

### GitHub Copilot Snippets

Type in chat and press Tab:

| Snippet | Purpose |
|---------|---------|
| `!superpowers` | Load framework |
| `!brainstorm` | Design refinement |
| `!plan` | Implementation planning |
| `!tdd` | Test-driven development |
| `!debug` | Systematic debugging |
| `!review` | Pre-code-review check |
| `!skill` | Load specific skill |

## Example Workflows

### Creating a New Feature

**Continue.dev:**
```
1. /superpowers
2. /brainstorm
   [Answer questions to refine design]
3. /plan
   [Get implementation plan]
4. /tdd
   [Implement with test-first approach]
5. /review
   [Check before submitting]
```

**GitHub Copilot:**
```
1. Type: !superpowers [Tab] [Enter]
2. Type: !brainstorm [Tab] [Enter]
   [Answer questions to refine design]
3. Type: !plan [Tab] [Enter]
   [Get implementation plan]
4. Type: !tdd [Tab] [Enter]
   [Implement with test-first approach]
5. Type: !review [Tab] [Enter]
   [Check before submitting]
```

### Debugging an Issue

**Continue.dev:**
```
1. /superpowers
2. /debug
   [Follow 4-phase debugging process]
3. /verify
   [Ensure fix actually works]
```

**GitHub Copilot:**
```
1. !superpowers [Tab] [Enter]
2. !debug [Tab] [Enter]
   [Follow 4-phase debugging process]
3. !verify [Tab] [Enter]
   [Ensure fix actually works]
```

## Troubleshooting

### "File not found" errors

Check your paths:
- Continue config should reference `~/.vscode/superpowers/skills/...`
- On Windows, use forward slashes: `C:/Users/...` or escape backslashes: `C:\\Users\\...`

### Continue not showing slash commands

1. Check config syntax - ensure valid JSON (no trailing commas)
2. Restart VS Code
3. Check Continue output: View → Output → Continue

### Copilot snippets not working

1. Ensure `.vscode/superpowers.code-snippets` exists in your project
2. Try typing the prefix and pressing Tab
3. Check VS Code snippets: File → Preferences → User Snippets

### Skills not loading

1. Verify clone: `ls ~/.vscode/superpowers/skills/`
2. Check file paths in config match your installation
3. Try absolute paths instead of `~`

## Next Steps

- **Full docs**: [.vscode/INSTALL.md](../.vscode/INSTALL.md)
- **Platform comparison**: [docs/README.vscode.md](../docs/README.vscode.md)
- **Create personal skills**: Add to `~/.vscode/superpowers-personal/`
- **Project config**: Add `.continue/config.json` to your projects

## Getting Help

- Issues: https://github.com/obra/superpowers/issues
- Continue docs: https://docs.continue.dev
- Copilot docs: https://docs.github.com/copilot

## What's Next?

Once you're comfortable with the basics:

1. **Learn the skills** - Explore `~/.vscode/superpowers/skills/` to see what's available
2. **Create personal skills** - Add your own workflows
3. **Configure projects** - Add project-specific configs
4. **Share configs** - Help others get started

## Platform Comparison

| Feature | Claude Code | Continue.dev | Copilot |
|---------|-------------|--------------|---------|
| Setup time | 2 min | 5 min | 10 min |
| Auto-context | ✅ | ❌ | ❌ |
| Slash commands | ✅ | ✅ | ❌ |
| Ease of use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

For the best experience, consider [Claude Code](https://claude.ai/code) with native plugin support!
