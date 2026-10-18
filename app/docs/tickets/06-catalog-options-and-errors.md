# 06: Catalog repository options, auth, and friendly errors

**What to build:** `--repo` / `--ref` (and `SKILLCTL_REPO` / `SKILLCTL_REF`) select another catalog; `GITHUB_TOKEN` / `GH_TOKEN` are sent when set; rate limits, 404s, and network errors render as one-line actionable messages with a non-zero exit code.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Repo/ref override works for every catalog command
- [ ] Token never printed
- [ ] Rate limit message mentions setting a token
