---
name: aws-iam-debug
description: >
  AWS IAM debugging playbook — policy evaluation logic, AccessDenied root cause analysis,
  role assumption chains, permission boundaries, SCPs, resource policies, and credential
  chain resolution. Load when: investigating AccessDenied errors, IAM policy issues,
  AssumeRole failures, credential resolution problems, or permission boundaries.
  Trigger phrases: "AccessDenied", "not authorized", "IAM", "assume role", "permission boundary".
alwaysApply: false
tier: 3
user-invocable: true
---
# AWS IAM Debugging Playbook

Systematic approach to diagnosing and resolving AWS IAM access issues.

---

## Quick Diagnostic Commands

Start every IAM debugging session with these:

```bash
# Who am I? (most important first step)
aws sts get-caller-identity

# Simulate whether a principal can perform an action
aws iam simulate-principal-policy \
  --policy-source-arn <principal-arn> \
  --action-names <action> \
  --resource-arns <resource-arn>

# Inspect a role's trust policy (who can assume it)
aws iam get-role --role-name <name>

# List all policies attached to a role
aws iam list-attached-role-policies --role-name <name>

# Get the actual policy document (need the version ID)
aws iam get-policy-version --policy-arn <arn> --version-id <vid>

# Search CloudTrail for recent denied events
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=<event> \
  --max-results 5

# Check SCPs on an OU or account
aws organizations list-policies-for-target \
  --target-id <ou-or-account-id> \
  --filter SERVICE_CONTROL_POLICY
```

---

## IAM Policy Evaluation Logic

AWS evaluates policies in a specific order. Understanding this flowchart is the key to all IAM debugging:

```
Request arrives
→ Check SCPs (org level) → Explicit Deny? → DENIED
→ Check resource-based policies → Allow + same account? → maybe ALLOWED
→ Check identity-based policies → Allow present?
→ Check permission boundaries → Allow present?
→ Check session policies (if assumed role)
→ Final: if all levels have an applicable Allow and no Deny → ALLOWED
→ Otherwise → DENIED (implicit deny)
```

### Key Rules

1. **Explicit Deny ALWAYS wins** — over any Allow at any level, period.
2. **Implicit Deny is the default** — absence of an Allow = denied.
3. **Cross-account requires bilateral allow** — BOTH the resource policy AND the caller's identity policy must allow. Exception: resource policy with a full principal ARN (not just account ID) grants access without needing the identity policy.
4. **Permission boundary is an intersection** — the action must be allowed in BOTH the identity policy AND the permission boundary. The boundary can't grant; it can only restrict.
5. **SCPs are an outer boundary** — they can't grant permissions, only restrict. An SCP Allow doesn't grant access; it merely doesn't block it.
6. **Session policies further restrict** — passed via `--policy` in AssumeRole, they act like an additional permission boundary on the session.

---

## Common AccessDenied Patterns & Fixes

| Pattern | Likely Cause | Diagnostic |
|---------|-------------|------------|
| AccessDenied on `s3:GetObject` | Bucket policy denies, or caller lacks permission | Check bucket policy + identity policy; check S3 Block Public Access settings |
| AccessDenied on `sts:AssumeRole` | Trust policy doesn't allow the principal | `aws iam get-role` — inspect trust policy's `Principal` and `Condition` block |
| AccessDenied with "explicit deny in SCP" | Organization SCP blocking the action | `aws organizations list-policies-for-target` on the account/OU |
| AccessDenied with permission boundary | Action not in boundary document | Compare the boundary's allowed actions to the requested action |
| AccessDenied for cross-account access | Missing bilateral allow | Need Allow in BOTH source identity policy AND target resource policy |
| `User: arn:aws:sts::xxx:assumed-role/...` | Role session, not IAM user | Check the **role's** policies, not the user who assumed it |
| AccessDenied after MFA condition | `aws:MultiFactorAuthPresent` condition failing | Ensure session was created with MFA; check token expiry |
| AccessDenied on `kms:Decrypt` | KMS key policy doesn't allow caller | IAM policy alone isn't enough for KMS — key policy must explicitly enable it |

---

## AssumeRole Chain Debugging

Role assumption creates sessions, and each hop creates new credentials with potentially different permissions:

```
User (identity policies)
  → AssumeRole → Role A (Role A's policies + optional session policy)
    → AssumeRole → Role B (Role B's policies + optional session policy)
```

### Common Failure Points

- **Trust policy Principal mismatch** — the ARN in the trust policy must exactly match the assuming entity (watch for assumed-role ARNs vs user ARNs)
- **Condition block** — most common culprit for "works from CLI but not from service":
  - `aws:SourceAccount` — wrong account
  - `sts:ExternalId` — missing or wrong external ID
  - `aws:SourceIp` / `aws:VpcSourceIp` — IP/VPC CIDR blocking
  - `aws:PrincipalOrgID` — must be in the same org
- **Session policies** — `--policy` or `--policy-arns` in the AssumeRole call further restrict the session
- **`sts:RoleSessionName` constraints** — trust policy may require a specific session name pattern
- **Role chaining limits** — max 1 hour session for role-to-role chaining (can't extend)

### Debugging Steps

```bash
# 1. Verify who is trying to assume
aws sts get-caller-identity

# 2. Get the target role's trust policy
aws iam get-role --role-name <target-role> --query 'Role.AssumeRolePolicyDocument'

# 3. Check if the trust policy's Principal matches your caller identity
# 4. Check Condition keys — compare against your actual request context
# 5. Attempt with --debug to see the full error
aws sts assume-role --role-arn <arn> --role-session-name test --debug
```

---

## Service-Linked Roles

Service-linked roles (SLRs) are pre-defined by AWS services and can't have their policies modified:

- If a service can't perform an action, the SLR might not exist yet
- SLRs are created automatically by some services, manually for others
- You can't attach/detach policies from SLRs

```bash
# List all service-linked roles
aws iam list-roles --path-prefix /aws-service-role/

# Check if a specific service's SLR exists
aws iam list-roles --path-prefix /aws-service-role/<service>.amazonaws.com/
```

---

## Resource Policy Gotchas

### S3

- Bucket policies are resource-based — can grant cross-account without identity policy changes
- **Block Public Access** settings override bucket policy Allows (4 settings, any one can block)
- Object ownership (BucketOwnerEnforced) disables ACLs entirely

### KMS

- **KMS key policy is required** — unlike most services, IAM policies alone are NOT sufficient
- The key policy must contain the "IAM enable" statement (`"kms:*"` to the account root) OR explicitly allow the caller
- Without it, even `AdministratorAccess` can't use the key
- Cross-account KMS: need both key policy Allow AND caller's identity policy Allow

### Lambda

- Resource policy needed for cross-account or cross-service invocation
- `aws lambda get-policy --function-name <name>` to inspect
- API Gateway, S3, EventBridge all need resource policy grants on the function

### SQS / SNS

- Queue/topic policies for cross-account publish/subscribe
- `aws sqs get-queue-attributes --attribute-names Policy`

---

## Credential Chain Order (AWS SDK)

All AWS SDKs resolve credentials in this order (first match wins):

```
1. Environment variables
   → AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY [+ AWS_SESSION_TOKEN]
2. Shared credentials file
   → ~/.aws/credentials [profile] — static or from saml2aws
3. AWS config file
   → ~/.aws/config [profile] — credential_process, sso-session, role assumption
4. ECS container credentials
   → AWS_CONTAINER_CREDENTIALS_RELATIVE_URI (ECS task role)
5. EC2 instance metadata (IMDS)
   → Instance profile via metadata service (v1 or v2)
```

### Common Credential Conflicts

- **Env vars shadow everything** — if `AWS_ACCESS_KEY_ID` is set (e.g., via direnv, Docker, CI), profile-based credentials are never consulted
- **AWS_PROFILE + env vars** — the JS SDK v3 warns "Multiple credential sources detected"; behavior varies by SDK version
- **credential_process vs static** — if a `[profile]` section has BOTH static keys and `credential_process`, static wins (SDK checks `isStaticCredsProfile` first)
- **saml2aws + SDK caching** — SDKs cache credentials in memory with no expiry awareness for static creds; use `credential_process` bridge for automatic refresh

### Diagnostic

```bash
# See exactly which credentials are being used
aws sts get-caller-identity --debug 2>&1 | grep -i "credential"

# Check what env vars might be interfering
env | grep -i AWS

# Test with explicit profile
aws sts get-caller-identity --profile <profile-name>
```

---

## Debugging Tips

1. **Use `--debug`** — the AWS CLI's debug output shows the full HTTP request, headers, and the signed action. Look for the authorization header to see which credentials were used.

2. **CloudTrail is your friend** — denied requests still appear in CloudTrail with `errorCode: AccessDenied` and `errorMessage` containing the specific denied action and resource.

3. **IAM Access Analyzer** — `aws accessanalyzer` can identify overly permissive policies and help narrow down what's actually needed.

4. **Policy Simulator (console)** — the IAM Policy Simulator in the AWS Console provides visual policy debugging with condition context.

5. **Check region conditions** — `aws:RequestedRegion` conditions in SCPs or identity policies can deny actions in unexpected regions.

6. **Tag-based conditions** — `aws:ResourceTag/*` and `aws:RequestTag/*` conditions silently deny when tags don't match.

7. **Service-specific quirks:**
   - ECR: need `ecr:GetAuthorizationToken` on `*` (not on the repo ARN)
   - S3: `s3:ListBucket` is on the bucket ARN, `s3:GetObject` is on the object ARN (`bucket/*`)
   - IAM: most IAM actions are global (us-east-1 only), regardless of where you call from

8. **VPC Endpoint policies** — if traffic routes through a VPC endpoint, the endpoint policy is an additional restriction layer not shown in the standard evaluation flow.
