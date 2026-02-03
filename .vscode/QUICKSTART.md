# VS Code Superpowers Quick Start with GitHub Copilot Chat

Get up and running with Superpowers in VS Code using GitHub Copilot in 5 minutes.

## Prerequisites

- VS Code installed
- GitHub Copilot subscription
- Git installed

## Quick Install

### 1. Install GitHub Copilot Extensions

```bash
code --install-extension GitHub.copilot
code --install-extension GitHub.copilot-chat
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

### 3. Copy Snippets (Global - Recommended)

**macOS:**
```bash
mkdir -p ~/Library/Application\ Support/Code/User/snippets/
cp ~/.vscode/superpowers/.vscode/superpowers.code-snippets ~/Library/Application\ Support/Code/User/snippets/
```

**Linux:**
```bash
mkdir -p ~/.config/Code/User/snippets/
cp ~/.vscode/superpowers/.vscode/superpowers.code-snippets ~/.config/Code/User/snippets/
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path "$env:APPDATA\Code\User\snippets"
Copy-Item "$env:USERPROFILE\.vscode\superpowers\.vscode\superpowers.code-snippets" "$env:APPDATA\Code\User\snippets\"
```

### 4. Test It!

1. Restart VS Code (or reload: Ctrl+Shift+P → "Reload Window")
2. Open Copilot Chat: `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Shift+I` (Mac)
3. Type: `!superpowers` and press Tab
4. You should see the snippet expand!
5. Press Enter to send to Copilot
6. Copilot will load the framework

## Quick Reference

### Available Snippets

Type in Copilot Chat and press Tab:

| Snippet | Purpose |
|---------|---------|
| `!superpowers` | Load framework |
| `!brainstorm` | Design refinement |
| `!plan` | Implementation planning |
| `!tdd` | Test-driven development |
| `!debug` | Systematic debugging |
| `!review` | Pre-code-review check |
| `!verify` | Verify completion |
| `!skill` | Load any skill by name |
| `!skills` | List all available skills |

### Usage Pattern

1. Type snippet prefix (e.g., `!brainstorm`)
2. Press **Tab** to expand
3. Press **Enter** to send to Copilot

## Example Workflows

### Creating a New Feature

```
Open Copilot Chat (Ctrl+Shift+I)

1. !superpowers [Tab] [Enter]
   → Framework loads

2. !brainstorm [Tab] [Enter]
   → Answer design questions

3. !plan [Tab] [Enter]
   → Get implementation plan

4. !tdd [Tab] [Enter]
   → Implement with TDD

5. !review [Tab] [Enter]
   → Check before submitting
```

### Debugging an Issue

```
Open Copilot Chat

1. !superpowers [Tab] [Enter]
   → Load framework

2. !debug [Tab] [Enter]
   → Follow 4-phase debugging

3. !verify [Tab] [Enter]
   → Ensure fix works
```

### Code Review

```
Open Copilot Chat

1. !superpowers [Tab] [Enter]
   → Load framework

2. !review [Tab] [Enter]
   → Run pre-review checklist
```

## Troubleshooting

### Snippets not expanding

1. **Check snippet location:**
   - Mac: `~/Library/Application Support/Code/User/snippets/`
   - Windows: `%APPDATA%\Code\User\snippets\`
   - Linux: `~/.config/Code/User/snippets/`

2. **Restart VS Code:**
   - Ctrl+Shift+P → "Reload Window"

3. **Try in Copilot Chat:**
   - Snippets only work in Chat input
   - Press Tab after typing prefix

### "File not found" errors

1. **Verify clone:**
   ```bash
   ls ~/.vscode/superpowers/skills/
   ```

2. **Check paths:**
   - Snippets use `~/.vscode/superpowers/`
   - This should work on all platforms

### Copilot not following instructions

1. **Load framework first:**
   - Always start with `!superpowers`

2. **New session needed:**
   - Start fresh Copilot Chat
   - Reload framework

## Next Steps

- **Full docs:** [INSTALL.md](INSTALL.md)
- **All skills:** See `~/.vscode/superpowers/skills/` directory
- **Create custom skills:** Add to `~/.vscode/superpowers-personal/`

## Tips

### Start Every Session with Framework

Always begin new Copilot Chat sessions with:
```
!superpowers [Tab] [Enter]
```

This establishes the Superpowers context.

### Use Skill Shortcuts

Instead of manually typing file paths, use the shortcuts:
- `!brainstorm` instead of typing the full path
- `!tdd` instead of referencing the TDD skill file
- etc.

### Project-Specific Setup

For team projects, copy snippets to `.vscode/`:
```bash
mkdir -p .vscode
cp ~/.vscode/superpowers/.vscode/superpowers.code-snippets .vscode/
```

Team members just need to clone your project to get the snippets.

## Platform Note

**GitHub Copilot in VS Code** provides a functional Superpowers experience, but with some limitations:

- ⚠️ Manual loading each session (no auto-context)
- ⚠️ Snippet-based (no native slash commands)
- ⚠️ No parallel agent support

For the best experience, consider **[Claude Code](https://claude.ai/code)** which has:
- ✅ Native plugin support
- ✅ Automatic context injection
- ✅ All features working out of the box

But if you're already using VS Code and Copilot, Superpowers still provides valuable workflows!

## Getting Help

- Issues: https://github.com/obra/superpowers/issues
- Main docs: https://github.com/obra/superpowers
- Copilot docs: https://docs.github.com/copilot

---

**Ready to go!** Open Copilot Chat and type `!superpowers` to get started. 🚀
