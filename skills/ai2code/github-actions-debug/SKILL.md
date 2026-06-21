---
name: github-actions-debug
description: >
  GitHub Actions debugging playbook — workflow syntax validation, runner diagnostics,
  secret/environment troubleshooting, OIDC federation debugging, and common error-to-root-cause
  mappings. Load when: investigating CI/CD failures, workflow errors, runner issues,
  OIDC/credential problems in GH Actions, or when `gh run view` shows unexpected failures.
  Trigger phrases: "workflow failed", "actions error", "CI broken", "runner", "OIDC token".
markers:
  - .github/workflows/
globs:
  - "**/.github/workflows/*.yml"
  - "**/.github/workflows/*.yaml"
alwaysApply: false
tier: 3
user-invocable: true
---
# GitHub Actions Debugging

A structured playbook for diagnosing and resolving GitHub Actions failures.

---

## 1. Quick Diagnostic Commands

Run these first to orient yourself:

```bash
# Recent workflow runs (status, conclusion, event)
gh run list --limit 5

# Failed step logs — this is your primary diagnostic tool
gh run view <run-id> --log-failed

# Structured run metadata (JSON for programmatic use)
gh run view <run-id> --json conclusion,status,event,headBranch,jobs

# List all workflows and their enabled/disabled state
gh workflow list

# Available secrets (names only — values are never exposed)
gh secret list

# Repository-level Actions permissions and policies
gh api repos/{owner}/{repo}/actions/permissions

# Re-run failed jobs only (avoids re-running passing jobs)
gh run rerun <run-id> --failed

# Download run logs for offline analysis
gh run view <run-id> --log > run.log
```

**Pro tip:** Combine `--json` output with `jq` for filtering:
```bash
gh run list --json status,conclusion,name,createdAt --jq '.[] | select(.conclusion == "failure")'
```

---

## 2. Common Error → Root Cause Mapping

| Error Message | Likely Cause | Fix |
|---|---|---|
| "Resource not accessible by integration" | GITHUB_TOKEN missing a required permission | Add the needed scope to the `permissions:` block |
| "Process completed with exit code 1" | Generic command failure — the real error is upstream | Read the full step log, not just the summary |
| "No hosted runner matching the labels" | Wrong `runs-on:` label or runner group misconfigured | Check available labels: `github-hosted` vs `self-hosted` tags |
| "HttpError: API rate limit exceeded" | Too many GitHub API calls in the workflow | Add retry logic, reduce calls, or use `GITHUB_TOKEN` (higher limit than PAT) |
| "Credentials could not be loaded" | OIDC/AWS credential setup failure | Ensure `permissions: id-token: write` — see §4 |
| "The template is not valid" | YAML syntax or expression error | Run `actionlint` locally; check for unquoted `${{ }}` in `if:` |
| "Context access might be invalid: secrets" | Secret unavailable (fork PRs cannot access secrets) | Check repository settings → fork PR secret access policy |
| "This request has been automatically failed" | A newer run cancelled this one via `concurrency:` | Review `concurrency:` group and `cancel-in-progress:` settings |
| "Error: action step exceeded the maximum execution time" | Step timeout (default: 6 hours) | Add `timeout-minutes:` to the step or investigate hang |
| "Waiting for a runner to pick up this job" (forever) | No matching runner available or runner at capacity | Check runner labels, runner group membership, and pool size |
| "Could not resolve action" | Action reference doesn't exist (typo, deleted tag) | Verify action path, tag, and that it's public or allowed |
| "Unable to resolve action ... version" | Pinned SHA/tag was force-pushed or deleted | Re-pin to a valid ref; prefer SHA pinning for security |

---

## 3. Workflow Permissions Reference

The `permissions:` block controls `GITHUB_TOKEN` scopes.

**Critical rule:** Setting ANY permission explicitly causes all others to default to `none`.

```yaml
permissions:
  contents: read       # Read repo contents (default if no permissions block)
  id-token: write      # REQUIRED for OIDC federation (AWS, GCP, Azure)
  pull-requests: write # Comment on PRs, update checks
  packages: write      # Push to GHCR / GitHub Packages
  issues: write        # Create/update issues
  actions: read        # List/view workflow runs
  deployments: write   # Create deployments
  statuses: write      # Set commit statuses
```

**Common mistakes:**
- Adding `permissions: id-token: write` without also adding `contents: read` → checkout fails
- Using `permissions: write-all` in production (overly broad — violates least privilege)
- Forgetting that job-level `permissions:` overrides workflow-level (not merges)

**Fork PR restrictions:**
- `GITHUB_TOKEN` in fork PRs always has `read` permissions only (security measure)
- Secrets are NOT passed to fork PR workflows (use `pull_request_target` with caution)

---

## 4. OIDC Debugging Checklist

When `aws-actions/configure-aws-credentials` or similar OIDC integrations fail:

### Workflow side
- [ ] `permissions: id-token: write` is set (at workflow OR job level)
- [ ] `contents: read` is also set (otherwise `actions/checkout` fails first)
- [ ] Action version is v4+ (older versions don't support OIDC)
- [ ] `role-to-assume:` ARN is correct and in the right account
- [ ] `aws-region:` is specified

### AWS IAM side
- [ ] OIDC identity provider exists for `token.actions.githubusercontent.com`
- [ ] Trust policy audience (`aud`) condition: `sts.amazonaws.com`
- [ ] Trust policy subject (`sub`) condition matches the calling repo:
  ```json
  "StringLike": {
    "token.actions.githubusercontent.com:sub": "repo:<org>/<repo>:*"
  }
  ```
- [ ] For environment-scoped: `repo:<org>/<repo>:environment:<env-name>`
- [ ] For branch-scoped: `repo:<org>/<repo>:ref:refs/heads/<branch>`
- [ ] Role ARN in workflow matches the actual IAM role
- [ ] No IP-based deny conditions (GitHub runner IPs rotate unpredictably)
- [ ] Thumbprint: AWS validates natively since July 2023 — remove thumbprint conditions if present

### Debugging the token itself
```bash
# In a workflow step, decode the OIDC token to inspect claims:
- name: Debug OIDC token
  run: |
    TOKEN=$(curl -sS -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
      "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=sts.amazonaws.com" | jq -r '.value')
    echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq .
```

---

## 5. Runner Image Changes

`ubuntu-latest` periodically migrates to new OS versions (e.g., 22.04 → 24.04).

### Common breakages after image updates
- **Preinstalled tool version changed** — Node, Python, Go, Java major/minor bumps
- **Docker engine version bumped** — new daemon behavior, changed defaults
- **System library versions changed** — OpenSSL, glibc, apt packages renamed
- **Default shell behavior changed** — bash version, set -e semantics
- **Removed preinstalled tools** — tools that were there before may be gone

### Fixes
- **Pin the image:** use `ubuntu-22.04` instead of `ubuntu-latest`
- **Add explicit setup steps:** `actions/setup-node@v4`, `actions/setup-python@v5`
- **Check the changelog:** [github.com/actions/runner-images/releases](https://github.com/actions/runner-images/releases)
- **Use a matrix** to test across multiple images during migration

---

## 6. Caching & Artifacts Gotchas

### Cache issues
- **Key mismatch → permanent miss:** hash includes files that change every run (timestamps, random seeds)
- **Restore-keys too broad:** restores stale cache that causes build failures
- **Size limit:** 10 GB per repository (LRU eviction after that)
- **Cross-branch:** caches from `main` are available to feature branches, not vice versa
- **Immutable keys:** once a cache key is written, it cannot be overwritten (use unique suffixes)

### Artifact issues
- **Retention:** 90 days default, configurable per-repo
- **Upload failures:** large files (>2 GB individual) or many small files (>10k) can timeout
- **Download in subsequent job:** use `needs:` to ensure upload job completes first
- **Name collisions:** multiple jobs uploading same artifact name → last one wins

### Debugging
```bash
# Check cache usage
gh api repos/{owner}/{repo}/actions/cache/usage

# List cache entries
gh actions-cache list

# Delete stale caches
gh actions-cache delete <key>
```

---

## 7. Self-Hosted Runner Troubleshooting

### Runner shows offline
1. Check the runner service: `sudo ./svc.sh status` or `systemctl status actions.runner.*`
2. Check network connectivity to `github.com` and `*.actions.githubusercontent.com`
3. Verify the runner is still registered: `gh api repos/{owner}/{repo}/actions/runners`
4. Check if registration token expired (re-register if >28 days idle)
5. Inspect runner logs: `_diag/Runner_*.log` and `_diag/Worker_*.log`

### Runner picks up job but fails
- **Tool cache empty:** self-hosted runners don't have preinstalled tools like hosted runners
- **Docker access:** runner user needs to be in the `docker` group
- **Disk space:** `/home/runner` or `/tmp` full → cleanup or add `pre-job` hook
- **Path issues:** tool not on PATH for the runner service context

### Stale/ghost runners
- Runners idle for 14+ days go offline but remain registered
- Registration tokens expire after 1 hour
- Auto-scaling runners should de-register on shutdown:
  ```bash
  ./config.sh remove --token <removal-token>
  ```

---

## 8. Debugging Steps (Ordered Procedure)

When a workflow fails, follow this sequence:

### Step 1: Identify the failure
```bash
gh run view <id> --json jobs --jq '.jobs[] | select(.conclusion == "failure") | {name, conclusion, steps: [.steps[] | select(.conclusion == "failure")]}'
```
Pinpoint: which workflow → which job → which step.

### Step 2: Get the logs
```bash
gh run view <id> --log-failed
```
Read the FULL output, not just the last line. The real error is often 20+ lines before "Process completed with exit code 1".

### Step 3: Compare with recent success
```bash
gh run list --workflow <name> --json conclusion,headSha,createdAt --jq '.[:10]'
```
Did this workflow pass recently? What commits landed between the last pass and this failure?

### Step 4: Check the trigger event
- `push` vs `pull_request` vs `workflow_dispatch` — different contexts, different permissions
- `pull_request` from fork → restricted secrets and tokens
- `schedule` → runs on the default branch HEAD, not a PR

### Step 5: Check permissions
Does `GITHUB_TOKEN` have the required scopes? (See §3)
Are secrets available in this context? (Fork PRs, environments with protection rules)

### Step 6: Check environment and secrets
```bash
gh secret list
gh variable list
gh api repos/{owner}/{repo}/environments
```
Is the secret actually set? Is the environment protection rule requiring approval?

### Step 7: Check dependency changes
- Did an action version change? (`uses: actions/checkout@v4` → `@v5`)
- Did the runner image change? (see §5)
- Did an external dependency (npm, pip, apt) release a breaking version?

### Step 8: Reproduce locally
```bash
# Install act (nektos/act) for local workflow execution
brew install act

# Run the specific job locally
act -j <job-name> --secret-file .secrets

# Or just validate syntax without running
actionlint .github/workflows/*.yml
```

**Limitations of `act`:** no OIDC, no caching, limited service container support, runner image differences.
