---
name: credential-lifecycle-debug
description: >
  Credential lifecycle debugging — SAML federation, OIDC trust, token expiry, credential_process
  bridges, SDK credential chain conflicts, and multi-provider authentication issues. Covers AWS,
  Azure, and GCP credential patterns. Load when: investigating ExpiredTokenException,
  InvalidClientTokenId, OIDC failures, SAML refresh issues, credential_process not being called,
  SDK credential caching bugs, or cross-account/cross-provider auth problems.
  Trigger phrases: "expired token", "credentials", "SAML", "OIDC", "credential_process",
  "InvalidClientTokenId", "token refresh", "assume role failed".
alwaysApply: false
tier: 3
user-invocable: true
---

# Credential Lifecycle Debugging

Systematic playbook for diagnosing authentication and credential expiry issues across
cloud providers. Covers the full lifecycle: issuance → caching → refresh → expiry → failure.

---

## Quick Diagnostic Commands

Run these first to establish baseline state. **Never output actual secret values.**

| Command | What it tells you |
|---------|-------------------|
| `aws sts get-caller-identity` | Which credentials are active (account, ARN, user ID) |
| `env \| grep -i 'aws\|azure\|gcp\|google' \| sort` | Credential env vars present (NEVER log values) |
| `aws configure list` | Which source each credential came from (env, config, iam-role, etc.) |
| `aws configure list --profile <name>` | Specific profile's credential resolution path |
| `cat ~/.aws/config \| grep -A5 '\[profile <name>\]'` | Profile configuration (safe to display) |
| `cat ~/.aws/credentials \| grep -A1 '\[<name>\]' \| grep x_security_token_expires` | Token freshness / expiry time |
| `launchctl list \| grep -i 'saml\|cred\|refresh'` | Check refresh LaunchAgents (macOS) |
| `systemctl --user list-timers` | Check refresh timers (Linux) |

---

## Credential Lifecycle Patterns

### SAML Federation (saml2aws)

```
IdP (Okta/ADFS/Ping) → SAML assertion → AWS STS → session credentials
└─ Credentials written to ~/.aws/credentials [profile-saml]
└─ Expires in 60 min (default)
└─ LaunchAgent/cron refreshes every 55 min
```

**Failure modes:**

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Refresh fails silently | IdP unreachable (VPN down) | Check VPN connectivity to IdP endpoint |
| Wrong credentials used | Profile name mismatch (e.g. `cpharm` vs `cpharm-saml`) | Verify profile separation — SDKs use public name, saml2aws writes to `-saml` suffix |
| Stale creds after reboot | LaunchAgent not loaded/running | `launchctl list \| grep saml` — re-load if missing |
| Refresh hangs | MFA prompt blocks non-interactive refresh | Configure TOTP or push-based MFA that doesn't require stdin |

### OIDC Federation (GitHub Actions, K8s, etc.)

```
Identity Provider → JWT token → AWS STS AssumeRoleWithWebIdentity → session
└─ Trust policy conditions (aud, sub, iss) must match
└─ Token typically valid 5-15 min (short-lived by design)
```

**Failure modes:**

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| AccessDenied on AssumeRoleWithWebIdentity | Trust policy condition mismatch | Check `StringEquals` vs `StringLike` for wildcards in subject |
| "Audience invalid" | Audience mismatch | Trust policy expects `sts.amazonaws.com` but token has custom aud |
| "Invalid identity token" | Subject claim format unexpected | Verify exact format (e.g. `repo:org/name:ref:refs/heads/main`) |
| Intermittent failures | Provider thumbprint stale | Re-fetch OIDC provider TLS certificate thumbprint |

### credential_process Bridge

```
SDK reads ~/.aws/config → finds credential_process → executes script
→ Script reads static creds from ~/.aws/credentials [profile-saml]
→ Returns JSON with { AccessKeyId, SecretAccessKey, SessionToken, Expiration }
→ SDK caches credentials, auto-refreshes when Expiration approaches
```

**Failure modes:**

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| "Error loading credentials" | Script not executable or not in PATH | `chmod +x` and use absolute path in config |
| Credentials never refresh | Script returns JSON without `Expiration` field | Add ISO 8601 `Expiration` from `x_security_token_expires` |
| credential_process never called | Same profile has static creds AND credential_process | SDK's `isStaticCredsProfile` check wins — use separate profile names |
| Module not found errors | Bun/Node follows symlinks, resolves imports from wrong dir | Add `node_modules` symlink or use `createRequire` with explicit path |

---

## SDK Credential Caching Bugs

### Node.js / JS SDK v3

- `fromIni()` memoizes credential providers at first call — never re-reads config
- `fromEnv()` reads env vars once, never re-reads on subsequent calls
- No built-in expiration awareness for static credentials (no `x_security_token_expires` parsing)
- **Workaround:** credential_process with `Expiration` field forces the SDK's refresh cycle
- If `AWS_PROFILE` and `AWS_ACCESS_KEY_ID` both set: env vars win (`fromEnv` runs before `fromIni` in `defaultProvider` chain)
- `isStaticCredsProfile` check in `resolveProfileData`: if `[profile]` has `aws_access_key_id` in credentials file, `credential_process` is **silently skipped**

**Critical sequence in `@aws-sdk/credential-provider-ini`:**
1. `isStaticCredsProfile(data)` → true if `aws_access_key_id` present → returns static creds
2. `isProcessProfile(data)` → checked only if (1) is false
3. `isAssumeRoleProfile(data)` → checked only if (1) and (2) are false

### Go SDK

- `fromEnv` provider checks environment variables first
- `SharedCredentialsProvider` reads from `~/.aws/credentials` file
- Process credential provider shells out to `credential_process`
- Caches with expiration awareness IF the provider returns an `Expiration` value
- **Process context matters:** detached processes, `setpgid`, and process groups may not inherit expected env vars

### Python (boto3 / botocore)

- Credential resolution cached per `Session` instance (not per API call)
- `botocore.credentials.RefreshableCredentials` handles auto-refresh IF source supports it
- AssumeRole credentials auto-refresh; static credentials from `[profile]` do NOT
- `credential_process` credentials refresh correctly (botocore parses `Expiration`)

---

## Cross-Provider Patterns

### Azure (Entra ID)

| Command | Purpose |
|---------|---------|
| `az account get-access-token` | Current token status and expiry |
| `az account show` | Active subscription and tenant |
| `curl -H Metadata:true "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/"` | Managed Identity IMDS check |

- Token cache location: `~/.azure/msal_token_cache.json`
- `az login` tokens valid ~1 hour (access) / ~24 hours (refresh)
- Managed Identity tokens fetched from IMDS (169.254.169.254) — no file storage
- Service Principal: check client secret expiry in App Registration

### GCP

| Command | Purpose |
|---------|---------|
| `gcloud auth list` | Active account(s) |
| `gcloud auth application-default print-access-token` | ADC token validity |
| `gcloud auth application-default login` | Refresh ADC credentials |

- Service account key files: no auto-expiry but check organizational rotation policies
- Workload Identity Federation: verify pool/provider config matches incoming token claims
- ADC resolution order: `GOOGLE_APPLICATION_CREDENTIALS` env → gcloud CLI creds → metadata server

---

## Environment Inheritance Debugging

Credentials fail when processes don't inherit the expected environment:

| Context | Behavior | Gotcha |
|---------|----------|--------|
| `direnv` | Injects vars on `cd` | Child processes inherit parent's env at spawn time, not current direnv state |
| tmux sessions | Inherit env from tmux **server** (when it started) | Not from current shell — `tmux setenv` updates server env for new panes only |
| LaunchAgents / systemd units | Get minimal env (no direnv, no shell rc files) | Must set `EnvironmentVariables` / `Environment=` explicitly |
| `exec env VAR=val command` | Replaces shell — new process gets explicit env only | Previous env vars lost unless passed through |

**Inspect process environment:**

```bash
# Linux
cat /proc/<pid>/environ | tr '\0' '\n' | grep AWS

# macOS
ps eww <pid> | tr ' ' '\n' | grep AWS
```

---

## Troubleshooting Decision Tree

```
Credential error?
├── ExpiredTokenException
│   ├── Is refresh mechanism running?
│   │   ├── YES → Check credential_process returns Expiration field
│   │   └── NO  → Start/reload the refresh agent (launchctl load / systemctl enable)
│   └── Is process long-running (>60 min)?
│       └── YES → Needs credential_process bridge or SDK with refresh support
│
├── InvalidClientTokenId
│   ├── Are credentials from the right account?
│   │   └── Run `aws sts get-caller-identity` to verify
│   ├── Were credentials rotated/revoked?
│   │   └── Re-generate via IAM or re-run SAML login
│   └── Is the region correct?
│       └── Some services require region-specific endpoints
│
├── Could not load credentials / NoCredentialProviders
│   ├── Are env vars present? → `env | grep AWS`
│   ├── Does the profile exist? → `grep profile ~/.aws/config`
│   ├── Is credential_process executable? → `ls -la $(grep credential_process ~/.aws/config | awk '{print $NF}')`
│   └── Is the process inheriting env? → Check parent process environment
│
├── Access Denied (403)
│   └── This is an AUTHORIZATION error, not authentication
│       └── Wrong diagnostic path — credentials are valid but lack permission
│       └── Debug with IAM policy simulator or CloudTrail
│
└── Multiple credential sources warning
    └── Both env vars and profile active simultaneously
        └── Unset one source: `unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN`
        └── Or: remove `AWS_PROFILE` from environment
```

---

## Security Rules

These are non-negotiable when debugging credentials:

1. **NEVER** output actual credential values (access keys, secret keys, session tokens, client secrets)
2. **NEVER** write credentials to non-secure locations (logs, issue trackers, chat)
3. When showing env vars, display names only: `AWS_ACCESS_KEY_ID=<set>` or `AWS_ACCESS_KEY_ID=[REDACTED]`
4. When suggesting fixes, reference secure sources:
   - `credential_process` scripts
   - Secret managers (Vault, Secrets Manager, Key Vault)
   - Environment injection from trusted sources (LaunchAgent, systemd, CI/CD secrets)
5. When copying credential files for debugging, use `mktemp` with restrictive permissions (`chmod 600`)
6. **NEVER** suggest disabling TLS verification or certificate validation as a credential fix
