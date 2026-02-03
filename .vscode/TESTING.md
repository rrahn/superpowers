# VS Code Integration Testing Guide

This document describes how to test and verify the VS Code Superpowers integration.

## Test Environment Setup

### Prerequisites

- VS Code installed
- Continue.dev extension OR GitHub Copilot Chat
- Git installed
- Internet connection for cloning repository

### Test Platforms

Test on multiple platforms if possible:
- [ ] macOS
- [ ] Linux (Ubuntu/Debian)
- [ ] Windows 10/11

## Installation Testing

### Test 1: Continue.dev Installation

**Steps:**
1. Install Continue extension: `code --install-extension Continue.continue`
2. Clone Superpowers: `git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers`
3. Copy example config: `cp ~/.vscode/superpowers/.vscode/continue-config.example.json ~/.continue/config.json`
4. Add your API key to `~/.continue/config.json`
5. Restart VS Code
6. Open Continue sidebar (Ctrl+Shift+L / Cmd+Shift+L)

**Expected Result:**
- Continue sidebar opens
- Slash commands are available (type `/` to see them)
- `/superpowers` command appears in the list

**Pass Criteria:**
- [ ] Continue extension installs without errors
- [ ] Repository clones successfully
- [ ] Config file is valid JSON
- [ ] Continue sidebar opens
- [ ] Slash commands are visible

### Test 2: GitHub Copilot Installation

**Steps:**
1. Install Copilot: `code --install-extension GitHub.copilot-chat`
2. Clone Superpowers: `git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers`
3. Create project: `mkdir test-project && cd test-project`
4. Copy snippets: `mkdir -p .vscode && cp ~/.vscode/superpowers/.vscode/superpowers.code-snippets .vscode/`
5. Open project in VS Code
6. Open Copilot Chat (Ctrl+Shift+I / Cmd+Shift+I)

**Expected Result:**
- Copilot Chat opens
- Typing `!superpowers` and pressing Tab expands snippet

**Pass Criteria:**
- [ ] Copilot extensions install without errors
- [ ] Repository clones successfully
- [ ] Snippets file copied
- [ ] Copilot Chat opens
- [ ] Snippets expand correctly

## Functional Testing

### Test 3: Load Framework (Continue)

**Steps:**
1. Open Continue sidebar
2. Type: `/superpowers`
3. Press Enter

**Expected Result:**
- Agent loads the using-superpowers skill
- Agent acknowledges having superpowers
- Agent mentions tool mappings
- Agent lists available skills or indicates readiness

**Pass Criteria:**
- [ ] Command executes without errors
- [ ] Agent confirms framework loaded
- [ ] Agent doesn't try to reload the skill
- [ ] Response time < 10 seconds

### Test 4: Load Framework (Copilot)

**Steps:**
1. Open Copilot Chat
2. Type: `!superpowers` and press Tab
3. Press Enter to send

**Expected Result:**
- Snippet expands with full framework loading instructions
- Agent acknowledges loading framework
- Agent mentions tool mappings

**Pass Criteria:**
- [ ] Snippet expands correctly
- [ ] Agent confirms framework loaded
- [ ] Response makes sense
- [ ] Response time < 10 seconds

### Test 5: Load Specific Skill (Continue)

**Steps:**
1. In Continue, type: `/skill brainstorming`
2. Observe response
3. Try: `/brainstorm` (shortcut)

**Expected Result:**
- Agent loads brainstorming skill
- Agent starts asking design questions or confirms ready to brainstorm

**Pass Criteria:**
- [ ] Both commands work
- [ ] Skill content is loaded
- [ ] Agent behavior changes to match skill
- [ ] No file read errors

### Test 6: Load Specific Skill (Copilot)

**Steps:**
1. In Copilot Chat, type: `!brainstorm` and press Tab
2. Press Enter

**Expected Result:**
- Snippet expands
- Agent loads brainstorming skill
- Agent starts design discussion

**Pass Criteria:**
- [ ] Snippet expands correctly
- [ ] Agent loads skill
- [ ] Agent behavior appropriate for skill

### Test 7: Brainstorming Workflow

**Steps:**
1. Load framework: `/superpowers` (Continue) or `!superpowers` (Copilot)
2. Load brainstorming: `/brainstorm` (Continue) or `!brainstorm` (Copilot)
3. Say: "I want to build a REST API for a todo app"
4. Answer the agent's questions

**Expected Result:**
- Agent asks clarifying questions
- Agent explores design alternatives
- Agent doesn't jump straight to implementation
- Agent presents design in digestible chunks

**Pass Criteria:**
- [ ] Agent asks 3+ clarifying questions
- [ ] Agent explores alternatives
- [ ] Agent doesn't write code immediately
- [ ] Workflow feels like Socratic dialogue

### Test 8: Planning Workflow

**Steps:**
1. Load framework
2. Load planning: `/plan` (Continue) or `!plan` (Copilot)
3. Describe a simple feature: "Add a user registration endpoint"

**Expected Result:**
- Agent creates implementation plan
- Plan has bite-sized tasks
- Each task includes file paths and verification steps

**Pass Criteria:**
- [ ] Plan is created
- [ ] Tasks are small (2-5 minutes each)
- [ ] File paths are specified
- [ ] Verification steps included

### Test 9: TDD Workflow

**Steps:**
1. Load framework
2. Load TDD: `/tdd` (Continue) or `!tdd` (Copilot)
3. Ask to implement a simple function: "Create a function to validate email addresses"

**Expected Result:**
- Agent writes test first
- Agent explains why test should fail
- Agent writes minimal implementation
- Agent verifies test passes

**Pass Criteria:**
- [ ] Test written before implementation
- [ ] Agent mentions RED-GREEN-REFACTOR
- [ ] Implementation is minimal
- [ ] Agent verifies test passes

### Test 10: Path Resolution (Cross-Platform)

**Steps:**
1. Check config file paths
2. Try loading framework
3. Check for "file not found" errors

**Platform-Specific:**
- macOS/Linux: `~/.vscode/superpowers/...`
- Windows: `C:/Users/.../` or `%USERPROFILE%\.vscode\...`

**Pass Criteria:**
- [ ] Paths resolve correctly on each platform
- [ ] No file not found errors
- [ ] Skills load successfully

## Error Handling Testing

### Test 11: Invalid Skill Name

**Steps:**
1. Try: `/skill nonexistent-skill` (Continue)
2. Or manually type: "Read ~/.vscode/superpowers/skills/nonexistent-skill/SKILL.md"

**Expected Result:**
- Agent reports file not found or skill doesn't exist
- Agent suggests checking available skills

**Pass Criteria:**
- [ ] Error is caught gracefully
- [ ] Agent doesn't crash
- [ ] Helpful error message

### Test 12: Missing Configuration

**Steps:**
1. Remove API key from Continue config
2. Try to use `/superpowers`

**Expected Result:**
- Error about missing API key
- Clear indication of what's wrong

**Pass Criteria:**
- [ ] Error is clear
- [ ] No silent failures
- [ ] Agent doesn't crash

### Test 13: Malformed Config

**Steps:**
1. Add a syntax error to Continue config (e.g., trailing comma)
2. Restart VS Code
3. Open Continue

**Expected Result:**
- Continue reports JSON parsing error
- Extension doesn't load silently

**Pass Criteria:**
- [ ] Error is visible
- [ ] Error message mentions JSON
- [ ] Can recover by fixing config

## Integration Testing

### Test 14: Continue Context Providers

**Steps:**
1. Open a file with Continue
2. Pin the file (Continue's pin feature)
3. Use `/superpowers` and ask a question about the file

**Expected Result:**
- Agent has access to both Superpowers skills and file context
- Agent can answer questions about the pinned file
- Context providers work alongside Superpowers

**Pass Criteria:**
- [ ] File context is available
- [ ] Superpowers skills work
- [ ] No conflicts between contexts

### Test 15: Multiple Skills in Sequence

**Steps:**
1. Load framework: `/superpowers`
2. Load brainstorming: `/brainstorm`
3. After design discussion, load planning: `/plan`
4. After plan, load TDD: `/tdd`

**Expected Result:**
- Each skill loads successfully
- Agent transitions between skills
- Context from previous skill is retained

**Pass Criteria:**
- [ ] All skills load
- [ ] No confusion between skills
- [ ] Conversation context maintained

## Performance Testing

### Test 16: Response Time

**Steps:**
1. Load framework
2. Measure time to first response
3. Load a skill
4. Measure time to skill loading

**Expected Result:**
- Framework loads < 10 seconds
- Skills load < 5 seconds
- Responses are timely

**Pass Criteria:**
- [ ] Framework load < 10s
- [ ] Skill load < 5s
- [ ] Interactive response time acceptable

### Test 17: Large Skill Files

**Steps:**
1. Load a complex skill (e.g., `test-driven-development`)
2. Check if full content is loaded
3. Verify agent follows all instructions

**Expected Result:**
- Entire skill content is processed
- Agent doesn't truncate instructions
- All checklists and steps are followed

**Pass Criteria:**
- [ ] Full skill loaded
- [ ] No truncation
- [ ] Complete instructions followed

## Documentation Testing

### Test 18: Installation Docs Accuracy

**Steps:**
1. Follow `.vscode/INSTALL.md` step by step
2. Note any unclear instructions
3. Note any errors or omissions

**Pass Criteria:**
- [ ] All steps are clear
- [ ] All commands work
- [ ] No missing information
- [ ] Screenshots/examples accurate

### Test 19: Quick Start Docs

**Steps:**
1. Follow `.vscode/QUICKSTART.md` as a new user
2. Time how long it takes
3. Note any confusion

**Expected Result:**
- Setup complete in < 10 minutes
- All examples work
- No major confusion

**Pass Criteria:**
- [ ] Setup time < 10 minutes
- [ ] All examples work
- [ ] Clear for beginners

### Test 20: README.vscode.md Completeness

**Steps:**
1. Read `docs/README.vscode.md`
2. Check all links work
3. Verify examples are correct

**Pass Criteria:**
- [ ] All links valid
- [ ] Examples work
- [ ] Information is complete
- [ ] Tool mapping is accurate

## Compatibility Testing

### Test 21: Continue.dev Version Compatibility

**Test with:**
- Latest stable Continue version
- Previous major version (if available)

**Pass Criteria:**
- [ ] Works with latest version
- [ ] Config format compatible
- [ ] Slash commands work

### Test 22: VS Code Version Compatibility

**Test with:**
- Latest stable VS Code
- VS Code Insiders (if available)

**Pass Criteria:**
- [ ] Works on latest stable
- [ ] No deprecated API usage
- [ ] Extensions install

## Reporting Test Results

For each test:
- [ ] Test passed
- [ ] Test failed - describe issue
- [ ] Test blocked - describe blocker
- [ ] Test not applicable - explain why

Document any issues found:
1. Test number and name
2. Platform (OS, VS Code version, extension version)
3. Steps to reproduce
4. Expected vs actual result
5. Error messages (if any)
6. Screenshots (if applicable)

## Success Criteria

The VS Code integration is considered successful if:
- [ ] 90%+ of tests pass on all platforms
- [ ] All critical workflows function (brainstorming, planning, TDD)
- [ ] Documentation is clear and complete
- [ ] Installation process is straightforward
- [ ] No critical bugs remain

## Known Limitations

Document these as expected behavior, not bugs:
- Manual skill loading required each session (vs Claude Code auto-inject)
- No parallel agent support
- File reading overhead
- No native TodoWrite tool

These are platform limitations, not bugs to fix.
