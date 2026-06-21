# Dolt Backup / Remote Push

Read this when setting up S3 backup for a beads database, troubleshooting push failures,
or configuring AWS credentials for auto-push.

---

## Overview

Beads databases are backed up via Dolt's native push to an AWS S3 + DynamoDB backend. The legacy
JSONL git backup (`backup.enabled`, `backup.git-push`) is **disabled** to avoid polluting project
git history with `bd: backup ...` commits.

## Configuration per project

```bash
# These should already be set — verify with bd config get <key>
backup.enabled    = false    # JSONL git backup disabled
backup.git-push   = false    # no git commits/pushes for backup
dolt.auto-push    = true     # push to S3 after every write (debounced 5 min)
```

## Remote setup

Two layers of credential configuration are needed:

1. **Per-remote CLI config** — stored in `.beads/dolt/<db>/config.json`, used by `dolt push` CLI
2. **direnv `.envrc`** — exports explicit AWS credentials into the environment, used by the Dolt SQL server's `CALL DOLT_PUSH`

Beads routes S3 pushes through `CALL DOLT_PUSH` in the SQL server (not the CLI). The SQL server
uses the standard Go AWS SDK credential chain, which reads environment variables — **not** the
per-remote CLI config. Without the `.envrc`, pushes fail with `ExpiredTokenException`.

```bash
# 1. Create .envrc in the project root (for SQL server credentials)
cat > .envrc << 'EOF'
export AWS_PROFILE=cpharm
export AWS_REGION=us-east-1

# Export explicit credentials for the Dolt SQL server (Go AWS SDK doesn't
# reliably resolve AWS_PROFILE in all process contexts)
eval "$(AWS_PROFILE=cpharm aws configure export-credentials --format env 2>/dev/null)"
EOF
direnv allow .

# 2. Stop the embedded Dolt server (required for --aws-creds-* flags)
bd dolt stop

# 3. Add remote via dolt CLI (NOT bd dolt remote add — bd doesn't support AWS flags)
cd .beads/dolt/<db-name>
dolt remote add origin "aws://[DoltRemotes:pf-cpharm-dolt-backups]/<project-name>" \
    --aws-region us-east-1 \
    --aws-creds-type role \
    --aws-creds-profile cpharm

# 4. Return to project root, restart server with direnv env, verify push
cd ~/Code/<project>
eval "$(direnv export zsh)"       # load .envrc into current shell
bd dolt start                      # server inherits AWS creds from env
bd dolt push                       # verify push works
```

**This does not conflict with project-specific AWS accounts.** Terraform providers use explicit
`profile = "..."` in their configuration, which takes precedence over `AWS_PROFILE` in the
environment. The `.envrc` only affects tools that rely on the default SDK credential chain.

## How auto-push works

| Aspect | Detail |
|--------|--------|
| Trigger | `PersistentPostRun` after every `bd` write command |
| Debounce | Skips if last push was < 5 min ago (`dolt.auto-push-interval`) |
| Change detection | Compares `DOLT_HASHOF('HEAD')` vs last pushed hash |
| State file | `.beads/push-state.json` (not in Dolt DB to avoid merge conflicts) |
| Credential refresh | AWS SDK reads env vars set by direnv; SAML tokens refresh every 55 min via LaunchAgent, but server must be restarted to pick up new creds |

## Common pitfalls

- **Do not use `bd dolt remote add`** for S3 remotes — it cannot pass `--aws-creds-profile` and the push will fail with credential errors
- **Server must be stopped** before running `dolt remote add` with credential flags — Dolt CLI refuses if a server is running
- **Port collisions** affect push too — if the wrong server is running, auto-push sends the wrong project's data to S3
- **direnv `.envrc` is required** — the SQL server uses `CALL DOLT_PUSH` which reads env vars, not per-remote CLI config. Without the `.envrc`, pushes fail with expired/missing credentials
- **Server restart after SAML refresh** — the Dolt server process caches env vars from startup. After a SAML token refresh, `bd dolt stop` + any `bd` command restarts the server with fresh creds
