# Platform Comparison: Superpowers Across AI Coding Assistants

This guide helps you choose the right platform for using Superpowers.

## Quick Comparison

| Feature | Claude Code | OpenCode | Codex | VS Code (Copilot) |
|---------|-------------|----------|-------|-------------------|
| **Setup Time** | 2 min | 5 min | 5 min | 5-10 min |
| **Native Plugin** | ✅ | ✅ | ⚠️ CLI | ❌ |
| **Auto Context** | ✅ | ✅ | ❌ | ❌ |
| **Skill Discovery** | ✅ Auto | ✅ Auto | 🔧 CLI | 🔧 Snippets |
| **Slash Commands** | ✅ | ✅ | 🔧 CLI | ❌ |
| **Parallel Agents** | ✅ | ⚠️ Limited | ❌ | ❌ |
| **TodoWrite Tool** | ✅ | ⚠️ update_plan | ⚠️ update_plan | ⚠️ Comments |
| **Personal Skills** | ✅ | ✅ | ✅ | ✅ |
| **Project Skills** | ✅ | ✅ | ✅ | ✅ |
| **Cost** | $ Subscription | Free/Paid | $ API | $ Subscription |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

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

### 4. VS Code with GitHub Copilot

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
| VS Code (Copilot) | Snippet expansion + manual reference | ⭐⭐⭐ |

### Workflow Efficiency

**Time to start working with skills:**

| Platform | First Time | Subsequent Sessions |
|----------|------------|---------------------|
| Claude Code | 2 min | 0 min (auto) |
| OpenCode | 5 min | 0 min (auto) |
| Codex | 5 min | 1 min (CLI) |
| VS Code (Copilot) | 5-10 min | 1-2 min (snippets) |

### Model Support

| Platform | Models | Flexibility |
|----------|--------|-------------|
| Claude Code | Claude only | Low |
| OpenCode | Multiple* | High |
| Codex | OpenAI | Medium |
| VS Code (Copilot) | GitHub models | Low |

*OpenCode model support depends on configuration

### Cost Analysis

**Monthly Cost Estimates:**

| Platform | Cost | Notes |
|----------|------|-------|
| Claude Code | ~$20-30/mo | Subscription |
| OpenCode | $0-50/mo | API costs only |
| Codex | $10-100/mo | API costs vary |
| VS Code (Copilot) | $10-20/mo | Subscription |

Costs vary based on usage patterns.

## Use Case Recommendations

### Professional Development Team
**Recommendation:** Claude Code
- Best tool integration
- Parallel agents
- Team features
- Support

### Open Source Project
**Recommendation:** OpenCode
- Open source tools
- Free infrastructure
- Community support
- Flexible models

### Solo Developer (Budget-Conscious)
**Recommendation:** VS Code with Copilot
- Subscription-based (predictable cost)
- Works with existing VS Code
- GitHub integration
- Active development

### Existing VS Code User
**Recommendation:** VS Code with Copilot
- No workflow change
- Keep existing extensions
- Familiar environment
- Easy integration

### Existing Copilot User
**Recommendation:** Add Superpowers via Snippets
- Already paying for Copilot
- Simple snippets setup
- No additional cost
- Enhanced workflows

### Heavy Automation User
**Recommendation:** Codex or OpenCode
- CLI integration
- Scriptable
- CI/CD friendly
- Flexible

### Learning AI-Assisted Development
**Recommendation:** VS Code with Copilot
- Lower barrier to entry
- Good documentation
- Active community
- Works with familiar editor

## Migration Paths

### From Claude Code to VS Code
1. Export personal skills
2. Copy skills to VS Code location
3. Set up snippets
4. Test workflows

**Effort:** Medium (2-3 hours)

### From Copilot to Enhanced Copilot
1. Already have Copilot
2. Clone Superpowers repository
3. Set up snippets
4. Start using skills

**Effort:** Low (30 minutes)

### From VS Code to Claude Code
1. Export snippets and skills
2. Install Claude Code plugin
3. Skills work automatically
4. Enhanced features available

**Effort:** Low (30 minutes)

### From OpenCode to VS Code
1. Skills compatible
2. Set up Copilot Chat
3. Create snippets for skills
4. Adjust tool references

**Effort:** Medium (2 hours)

## Decision Matrix

Choose based on priorities:

**Priority: Best Experience**
→ Claude Code

**Priority: Open Source**
→ OpenCode

**Priority: Cost**
→ VS Code with Copilot (subscription)

**Priority: VS Code**
→ VS Code with Copilot

**Priority: Existing Copilot**
→ Add Superpowers via Snippets

**Priority: Automation**
→ Codex or OpenCode

**Priority: Flexibility**
→ OpenCode

**Priority: Team Features**
→ Claude Code

## Summary Recommendations

### 🥇 Best Overall: Claude Code
Native integration, full features, best UX

### 🥈 Best Open Source: OpenCode
Native skills, good integration, free

### 🥉 Best for VS Code: GitHub Copilot + Superpowers
Works with existing setup, snippet-based

### 🎖️ Best Value: GitHub Copilot + Superpowers
Use existing subscription, no additional cost

### 🏅 Best for Beginners: VS Code with Copilot
Familiar editor, good docs, easy to start

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

**VS Code with Copilot:**
```bash
code --install-extension GitHub.copilot-chat
git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers
# Follow: .vscode/INSTALL.md
```

## Still Undecided?

Try VS Code with Copilot if you're already using it:
- Simple snippet setup
- Works with existing subscription
- Can switch to other platforms later
- Good introduction to Superpowers

Then migrate to Claude Code or OpenCode if you want native integration.

## Questions?

- **General**: https://github.com/obra/superpowers/issues
- **VS Code**: See `.vscode/INSTALL.md`
- **OpenCode**: See `docs/README.opencode.md`
- **Codex**: See `docs/README.codex.md`
