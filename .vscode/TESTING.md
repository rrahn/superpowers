# VS Code Integration Testing Guide

This document describes how to test and verify the VS Code Superpowers integration with GitHub Copilot Chat.

## Test Environment Setup

### Prerequisites

- VS Code installed
- GitHub Copilot Chat extension
- Git installed
- Active GitHub Copilot subscription

### Test Platforms

Test on multiple platforms if possible:
- [ ] macOS
- [ ] Linux (Ubuntu/Debian)
- [ ] Windows 10/11

## Installation Testing

### Test 1: GitHub Copilot Installation

**Steps:**
1. Install Copilot extensions: `code --install-extension GitHub.copilot-chat`
2. Clone Superpowers: `git clone https://github.com/obra/superpowers.git ~/.vscode/superpowers`
3. Copy snippets to global location (see platform-specific paths in QUICKSTART.md)
4. Restart VS Code
5. Open Copilot Chat (Ctrl+Shift+I / Cmd+Shift+I)

**Expected Result:**
- Extensions install without errors
- Repository clones successfully
- Snippets file copied to correct location
- Copilot Chat opens

**Pass Criteria:**
- [ ] Copilot extensions install successfully
- [ ] Repository clones without errors
- [ ] Snippets file exists in correct location
- [ ] Copilot Chat is accessible

### Test 2: Snippet Expansion

**Steps:**
1. Open Copilot Chat
2. Type: `!superpowers`
3. Press Tab

**Expected Result:**
- Snippet expands with full framework loading text
- Multiple lines of instruction appear
- Text includes tool mapping and available skills

**Pass Criteria:**
- [ ] Snippet expands on Tab press
- [ ] Full content is visible
- [ ] No JSON errors or malformed text

## Functional Testing

### Test 3: Load Framework

**Steps:**
1. Open Copilot Chat
2. Type: `!superpowers` and press Tab
3. Press Enter to send

**Expected Result:**
- Copilot processes the message
- Copilot acknowledges loading framework
- Copilot mentions having superpowers
- Copilot references tool mappings

**Pass Criteria:**
- [ ] Message sends successfully
- [ ] Copilot confirms framework loaded
- [ ] Response time < 10 seconds
- [ ] No errors in response

### Test 4: Load Specific Skill

**Steps:**
1. In Copilot Chat, type: `!brainstorm` and press Tab
2. Press Enter to send
3. Observe response

**Expected Result:**
- Snippet expands with brainstorming skill path
- Copilot loads brainstorming skill
- Copilot starts asking design questions or confirms ready to brainstorm

**Pass Criteria:**
- [ ] Snippet expands correctly
- [ ] Skill loads without errors
- [ ] Copilot behavior matches skill (Socratic questioning)
- [ ] No file not found errors

### Test 5: Multiple Skills in Sequence

**Steps:**
1. Load framework: `!superpowers` [Tab] [Enter]
2. Load brainstorming: `!brainstorm` [Tab] [Enter]
3. After design discussion, load planning: `!plan` [Tab] [Enter]

**Expected Result:**
- Each skill loads successfully
- Copilot transitions between skills appropriately
- Context from previous skill is retained

**Pass Criteria:**
- [ ] All skills load without errors
- [ ] Transitions are smooth
- [ ] Conversation context maintained

### Test 6: Brainstorming Workflow

**Steps:**
1. Load framework: `!superpowers` [Tab] [Enter]
2. Load brainstorming: `!brainstorm` [Tab] [Enter]
3. Say: "I want to build a REST API for a todo app"
4. Answer Copilot's questions

**Expected Result:**
- Copilot asks clarifying questions
- Copilot explores design alternatives
- Copilot doesn't jump to implementation
- Socratic dialogue approach

**Pass Criteria:**
- [ ] Copilot asks 3+ clarifying questions
- [ ] Design exploration before coding
- [ ] No premature code generation
- [ ] Workflow feels like design refinement

### Test 7: Planning Workflow

**Steps:**
1. Load framework
2. Load planning: `!plan` [Tab] [Enter]
3. Describe feature: "Add user registration endpoint"

**Expected Result:**
- Copilot creates implementation plan
- Plan has small, bite-sized tasks
- Each task includes file paths and verification

**Pass Criteria:**
- [ ] Plan is generated
- [ ] Tasks are appropriately sized
- [ ] File paths specified
- [ ] Verification steps included

### Test 8: TDD Workflow

**Steps:**
1. Load framework
2. Load TDD: `!tdd` [Tab] [Enter]
3. Ask to implement: "Create email validation function"

**Expected Result:**
- Copilot writes test first
- Copilot explains RED-GREEN-REFACTOR
- Implementation is minimal
- Copilot verifies test passes

**Pass Criteria:**
- [ ] Test before implementation
- [ ] TDD methodology mentioned
- [ ] Minimal implementation
- [ ] Test verification included

### Test 9: List Skills

**Steps:**
1. Load framework
2. Use: `!skills` [Tab] [Enter]

**Expected Result:**
- Copilot lists all available skills
- Skills are organized by category
- Each skill has description

**Pass Criteria:**
- [ ] Skills list appears
- [ ] All major skills included
- [ ] Categorized/organized
- [ ] Descriptions provided

## Path Resolution Testing (Cross-Platform)

### Test 10: Path Resolution

**Platform-Specific Steps:**

**macOS/Linux:**
```bash
# Verify repository location
ls ~/.vscode/superpowers/skills/

# Test snippet expansion
# Should reference ~/.vscode/superpowers/skills/...
```

**Windows:**
```powershell
# Verify repository location
Get-ChildItem $env:USERPROFILE\.vscode\superpowers\skills\

# Test snippet expansion
# Should reference ~/.vscode/superpowers/skills/... (usually works via Copilot)
```

**Pass Criteria:**
- [ ] Repository exists at expected location
- [ ] Snippets reference correct paths
- [ ] No file not found errors
- [ ] Skills load successfully

## Error Handling Testing

### Test 11: Invalid Skill Name

**Steps:**
1. Manually type in Copilot Chat: "Read ~/.vscode/superpowers/skills/nonexistent-skill/SKILL.md"
2. Send message

**Expected Result:**
- Copilot reports file doesn't exist
- Graceful error handling
- Suggestion to check available skills

**Pass Criteria:**
- [ ] Error caught gracefully
- [ ] No Copilot crash
- [ ] Helpful error message

### Test 12: Missing Repository

**Steps:**
1. Temporarily rename repository: `mv ~/.vscode/superpowers ~/.vscode/superpowers-backup`
2. Try using a snippet: `!superpowers` [Tab] [Enter]
3. Restore: `mv ~/.vscode/superpowers-backup ~/.vscode/superpowers`

**Expected Result:**
- Copilot reports file not found
- Clear error message
- Can recover after restoring repository

**Pass Criteria:**
- [ ] Error is reported
- [ ] Error message is clear
- [ ] No silent failure

### Test 13: Malformed Snippet File

**Steps:**
1. Backup snippets file
2. Add syntax error to snippets JSON (e.g., trailing comma)
3. Restart VS Code
4. Try to use snippets

**Expected Result:**
- VS Code may report JSON error on load
- Snippets don't expand
- Can recover by fixing JSON

**Pass Criteria:**
- [ ] Error is detected
- [ ] Clear indication of problem
- [ ] Recoverable by fixing syntax

## Integration Testing

### Test 14: Context Retention

**Steps:**
1. Start Copilot Chat
2. Load framework: `!superpowers` [Tab] [Enter]
3. Discuss a topic with Copilot
4. Load a skill: `!brainstorm` [Tab] [Enter]
5. Check if previous context is maintained

**Expected Result:**
- Conversation context retained
- Skill loads on top of existing context
- Coherent conversation flow

**Pass Criteria:**
- [ ] Context maintained
- [ ] No conversation reset
- [ ] Coherent flow

### Test 15: Session Persistence

**Steps:**
1. Load framework in Copilot Chat
2. Close Copilot Chat panel
3. Reopen Copilot Chat
4. Check if framework is still loaded

**Expected Result:**
- Framework context lost (expected behavior)
- Must reload with `!superpowers` again

**Pass Criteria:**
- [ ] Behavior is documented
- [ ] Users know to reload each session
- [ ] Clear in documentation

## Performance Testing

### Test 16: Response Time

**Steps:**
1. Measure time for snippet expansion (should be instant)
2. Measure time for Copilot to process framework load (< 10s)
3. Measure time for skill loading (< 5s)

**Expected Result:**
- Snippet expansion: instant
- Framework load: < 10 seconds
- Skill load: < 5 seconds

**Pass Criteria:**
- [ ] Snippet expansion instant
- [ ] Framework load < 10s
- [ ] Skill load < 5s
- [ ] Acceptable user experience

### Test 17: Large Skill Files

**Steps:**
1. Load complex skill: `!tdd` [Tab] [Enter]
2. Verify full content processed
3. Check all instructions followed

**Expected Result:**
- Entire skill loaded
- No truncation
- All checklists and steps available

**Pass Criteria:**
- [ ] Full skill content processed
- [ ] No truncation
- [ ] Complete instructions available

## Documentation Testing

### Test 18: Installation Docs Accuracy

**Steps:**
1. Follow `INSTALL.md` step by step on clean system
2. Note any unclear instructions
3. Note any errors or omissions

**Pass Criteria:**
- [ ] All steps clear and accurate
- [ ] All commands work
- [ ] No missing information
- [ ] Platform-specific instructions correct

### Test 19: Quick Start Accuracy

**Steps:**
1. Follow `QUICKSTART.md` as new user
2. Time the setup process
3. Note any confusion

**Expected Result:**
- Setup complete in < 10 minutes
- All examples work
- Clear for beginners

**Pass Criteria:**
- [ ] Setup time < 10 minutes
- [ ] All examples functional
- [ ] Beginner-friendly

## Compatibility Testing

### Test 20: VS Code Version Compatibility

**Test with:**
- Latest stable VS Code
- VS Code Insiders (if available)

**Pass Criteria:**
- [ ] Works on latest stable
- [ ] Snippets function correctly
- [ ] No deprecated features

### Test 21: Copilot Extension Version

**Test with:**
- Latest Copilot Chat extension
- Note version number

**Pass Criteria:**
- [ ] Works with current version
- [ ] No compatibility issues
- [ ] Document tested version

## Reporting Test Results

For each test:
- [ ] Test passed
- [ ] Test failed - describe issue
- [ ] Test blocked - describe blocker
- [ ] Test not applicable - explain why

Document any issues:
1. Test number and name
2. Platform (OS, VS Code version, Copilot version)
3. Steps to reproduce
4. Expected vs actual result
5. Error messages (if any)
6. Screenshots (if helpful)

## Success Criteria

The VS Code integration is successful if:
- [ ] 90%+ of tests pass on all platforms
- [ ] Core workflows function (brainstorming, planning, TDD)
- [ ] Documentation is clear and accurate
- [ ] Installation is straightforward
- [ ] No critical bugs

## Known Limitations (Expected Behavior)

These are not bugs, but documented limitations:
- Manual skill loading each session (no auto-inject like Claude Code)
- Snippet-based approach (no native slash commands)
- No parallel agent support
- Session-based context (lost when chat restarted)

These limitations are inherent to the GitHub Copilot Chat platform and are documented in user guides.
