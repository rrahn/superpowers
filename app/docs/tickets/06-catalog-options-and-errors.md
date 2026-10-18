# 06: Catalog repository options, auth, and friendly errors

**What to build:** `--repo` / `--ref` (and `SKILLCTL_REPO` / `SKILLCTL_REF`) select another catalog; `GITHUB_TOKEN` / `GH_TOKEN` are sent when set; rate limits, 404s, and network errors render as one-line actionable messages with a non-zero exit code.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] Repo/ref override works for every catalog command
- [ ] Token never printed
- [ ] Rate limit message mentions setting a token
- [ ] A truncated git tree (huge repos) is reported, not silently listed partially
- [ ] One failing `SKILL.md` fetch yields an actionable message, not a traceback
- [ ] The default `httpx.Client` is closed when the command ends
