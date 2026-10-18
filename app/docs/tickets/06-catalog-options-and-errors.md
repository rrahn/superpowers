# 06: Catalog repository options, auth, and friendly errors

**What to build:** `--repo` / `--ref` (and `SKILLCTL_REPO` / `SKILLCTL_REF`) select another catalog; `GITHUB_TOKEN` / `GH_TOKEN` are sent when set; rate limits, 404s, and network errors render as one-line actionable messages with a non-zero exit code.

**Blocked by:** 04

**Status:** done

- [x] Repo/ref override works for every catalog command
- [x] Token never printed
- [x] Rate limit message mentions setting a token
- [x] A truncated git tree (huge repos) is reported, not silently listed partially
- [x] One failing `SKILL.md` fetch yields an actionable message, not a traceback
- [x] The default `httpx.Client` is closed when the command ends
