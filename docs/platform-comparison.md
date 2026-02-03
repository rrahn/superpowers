# Platform Comparison: Superpowers Across AI Coding Assistants

This guide helps you choose the right platform for using Superpowers.

## Quick Comparison

| Feature | Claude Code | OpenCode | Codex | VS Code (Continue) | VS Code (Copilot) |
|---------|-------------|----------|-------|-------------------|-------------------|
| **Setup Time** | 2 min | 5 min | 5 min | 5 min | 10 min |
| **Native Plugin** | ✅ | ✅ | ⚠️ CLI | ❌ | ❌ |
| **Auto Context** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Skill Discovery** | ✅ Auto | ✅ Auto | 🔧 CLI | 🔧 Config | 🔧 Snippets |
| **Slash Commands** | ✅ | ✅ | 🔧 CLI | ✅ | ❌ |
| **Parallel Agents** | ✅ | ⚠️ Limited | ❌ | ❌ | ❌ |
| **TodoWrite Tool** | ✅ | ⚠️ update_plan | ⚠️ update_plan | ⚠️ update_plan | ⚠️ Comments |
| **Personal Skills** | ✅ | ✅ | ✅ | ✅ | ⚠️ Manual |
| **Project Skills** | ✅ | ✅ | ✅ | ✅ | ⚠️ Snippets |
| **Cost** | $ Subscription | Free/Paid | $ API | $ API | $ Subscription |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

**Legend:**
- ✅ Full support
- ⚠️ Partial/workaround available
- 🔧 Requires configuration
- ❌ Not available
- $ Paid service

## Detailed Comparison

### 1. Claude Code (Best Experience)

**Pros:**
- Native plugin system - most seamless experience
- Automatic context injection - skills always available
- Full tool support (Skill, TodoWrite, Task, etc.)
- Parallel agent execution
- Built-in skill discovery
- Regular updates and improvements
- Best for: Teams, professional developers, complex projects

**Cons:**
- Requires subscription
- Closed source
- Limited to Claude AI models

**Best For:**
- Professional development teams
- Complex multi-agent workflows
- Projects requiring parallel execution
- Users who want "it just works" experience

**Setup Effort:** ⭐ (2 minutes)

### 2. OpenCode (Great Alternative)

**Pros:**
- Native skill system
- Plugin architecture
- Automatic bootstrap
- Good documentation
- Free and open source
- Custom skills support
- Best for: Open source contributors, developers wanting customization

**Cons:**
- Smaller community than VS Code
- Limited parallel agent support
- Some tool mapping needed
- Less mature than Claude Code

**Best For:**
- Developers who want open source
- Users comfortable with configuration
- Projects not requiring heavy parallelization
- Budget-conscious teams

**Setup Effort:** ⭐⭐ (5 minutes)

### 3. Codex (Experimental)

**Pros:**
- CLI-based approach
- Good for automation
- Works with OpenAI models
- Flexible integration
- Best for: Automation, scripting, CI/CD integration

**Cons:**
- Experimental/less polished
- CLI overhead
- No parallel agents
- Requires manual skill loading
- Smaller user base

**Best For:**
- Automation workflows
- Developers comfortable with CLI
- OpenAI Codex users
- Scripting use cases

**Setup Effort:** ⭐⭐ (5 minutes)

### 4. VS Code with Continue.dev (Good Compromise)

**Pros:**
- Works with existing VS Code setup
- Supports multiple AI models (Claude, GPT, local)
- Slash commands for skills
- Open source
- Active development
- Large user base
- Good documentation
- Best for: VS Code users, multi-model users, developers wanting flexibility

**Cons:**
- Manual skill loading each session
- No automatic context
- No parallel agents
- File reading overhead
- More setup than Claude Code

**Best For:**
- VS Code users
- Developers wanting model flexibility
- Teams with existing VS Code workflows
- Open source advocates

**Setup Effort:** ⭐⭐⭐ (5-10 minutes)

### 5. VS Code with GitHub Copilot (Workable)

**Pros:**
- Works with GitHub Copilot subscription
- Large user base
- Integrated with GitHub
- Regular updates
- Best for: GitHub Copilot users who want better workflows

**Cons:**
- No slash commands (use snippets)
- Manual loading each session
- Most manual of all options
- Snippets can be clunky
- No automatic skill discovery
- Requires project setup

**Best For:**
- Existing GitHub Copilot users
- Users who don't want another subscription
- Simple workflow needs

**Setup Effort:** ⭐⭐⭐⭐ (10-15 minutes)

## Feature Deep Dive

### Skill Loading

| Platform | Method | Ease |
|----------|--------|------|
| Claude Code | Automatic + `Skill` tool | ⭐⭐⭐⭐⭐ |
| OpenCode | `skill` tool | ⭐⭐⭐⭐⭐ |
| Codex | CLI commands | ⭐⭐⭐⭐ |
| Continue | `/skill` slash command | ⭐⭐⭐⭐ |
| Copilot | Manual reference in chat | ⭐⭐⭐ |

### Workflow Efficiency

**Time to start working with skills:**

| Platform | First Time | Subsequent Sessions |
|----------|------------|---------------------|
| Claude Code | 2 min | 0 min (auto) |
| OpenCode | 5 min | 0 min (auto) |
| Codex | 5 min | 1 min (CLI) |
| Continue | 5 min | 30 sec (/superpowers) |
| Copilot | 10 min | 2 min (snippets) |

### Model Support

| Platform | Models | Flexibility |
|----------|--------|-------------|
| Claude Code | Claude only | Low |
| OpenCode | Multiple* | High |
| Codex | OpenAI | Medium |
| Continue | Any (Claude, GPT, local) | Very High |
| Copilot | GitHub models | Low |

*OpenCode model support depends on configuration

### Cost Analysis

**Monthly Cost Estimates:**

| Platform | Cost | Notes |
|----------|------|-------|
| Claude Code | ~$20-30/mo | Subscription |
| OpenCode | $0-50/mo | API costs only |
| Codex | $10-100/mo | API costs vary |
| Continue | $10-100/mo | API costs vary |
| Copilot | $10-20/mo | Subscription |

Costs vary based on usage patterns.

## Use Case Recommendations

### Professional Development Team
**Recommendation:** Claude Code
- Best tool integration
- Parallel agents
- Team features
- Support

### Open Source Project
**Recommendation:** OpenCode or Continue
- Open source tools
- Free infrastructure
- Community support
- Flexible models

### Solo Developer (Budget-Conscious)
**Recommendation:** Continue.dev
- Pay per use (API)
- Multi-model support
- VS Code integration
- Active community

### Existing VS Code User
**Recommendation:** Continue.dev
- No workflow change
- Keep existing extensions
- Familiar environment
- Easy integration

### Existing Copilot User
**Recommendation:** Continue.dev or Copilot + Superpowers
- Already paying for Copilot? Add skills via snippets
- Want better experience? Try Continue.dev
- Both options available

### Heavy Automation User
**Recommendation:** Codex or Continue
- CLI integration
- Scriptable
- CI/CD friendly
- Flexible

### Learning AI-Assisted Development
**Recommendation:** Continue.dev
- Lower barrier to entry
- Good documentation
- Active community
- Flexible models

## Migration Paths

### From Claude Code to VS Code
1. Export personal skills
2. Install Continue.dev
3. Convert skills to Continue config
4. Test workflows

**Effort:** Medium (2-3 hours)

### From Copilot to Continue
1. Keep Copilot for completions
2. Install Continue for chat/skills
3. Use both together
4. Gradually transition

**Effort:** Low (1 hour)

### From Continue to Claude Code
1. Export Continue config
2. Install Claude Code plugin
3. Skills work automatically
4. Enhanced features available

**Effort:** Low (30 minutes)

### From OpenCode to VS Code
1. Skills compatible
2. Install Continue
3. Map skills to slash commands
4. Adjust tool references

**Effort:** Medium (2 hours)

## Decision Matrix

Choose based on priorities:

**Priority: Best Experience**
→ Claude Code

**Priority: Open Source**
→ OpenCode or Continue.dev

**Priority: Cost**
→ Continue.dev (pay per use)

**Priority: VS Code**
→ Continue.dev

**Priority: Existing Copilot**
→ Continue.dev or Copilot + Snippets

**Priority: Automation**
→ Codex or Continue.dev

**Priority: Flexibility**
→ Continue.dev

**Priority: Team Features**
→ Claude Code

## Summary Recommendations

### 🥇 Best Overall: Claude Code
Native integration, full features, best UX

### 🥈 Best Open Source: OpenCode
Native skills, good integration, free

### 🥉 Best for VS Code: Continue.dev
Flexible, multi-model, active development

### 🎖️ Best Value: Continue.dev
Pay per use, no subscription, flexible

### 🏅 Best for Beginners: Continue.dev
Good docs, large community, easy setup

## Getting Started

Ready to choose? Here's how to start:

**Claude Code:**
```bash
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

**OpenCode:**
```bash
git clone https://github.com/obra/superpowers.git ~/.config/opencode/superpowers
# Follow: docs/README.opencode.md
```

**Continue.dev:**
```bash
code --install-extension Continue.continue
git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers
# Follow: .vscode/QUICKSTART.md
```

**Copilot:**
```bash
code --install-extension GitHub.copilot-chat
git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers
# Follow: .vscode/INSTALL.md
```

## Still Undecided?

Try Continue.dev first:
- Easy to set up
- Works with multiple models
- Can switch to other platforms later
- Good introduction to Superpowers

Then migrate to Claude Code or OpenCode if you want native integration.

## Questions?

- **General**: https://github.com/obra/superpowers/issues
- **VS Code**: See `.vscode/INSTALL.md`
- **OpenCode**: See `docs/README.opencode.md`
- **Codex**: See `docs/README.codex.md`
