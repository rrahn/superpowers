# 0001: Install into Copilot's primary skill locations only

**Status:** accepted

VS Code Copilot reads personal skills from `~/.copilot/skills/`, `~/.claude/skills/`, `~/.agents/skills/`
and project skills from `.github/skills/`, `.claude/skills/`, `.agents/skills/`
([docs](https://code.visualstudio.com/docs/copilot/customization/agent-skills)).

`skillctl` installs into and lists only the Copilot-first locations: `~/.copilot/skills/` (global scope)
and `<repo root>/.github/skills/` (local scope). `.github/` is also where the repo's other
Copilot customizations live, which keeps project skills discoverable for reviewers.

Supporting other harnesses means adding another scope adapter; nothing else changes.
