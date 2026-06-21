---
name: infrastructure-terraform
description: >
  Terraform infrastructure-as-code patterns and AWS CLI safety guardrails — remote state
  (S3+DynamoDB locking), variable validation, S3 bucket hardening, ECS deployment circuit
  breakers, JMESPath queries, and troubleshooting (stuck locks, imports, refresh-only plans).
  CRITICAL: contains the destructive command gating protocol — never run aws delete/terminate/
  destroy or terraform apply without this skill loaded. Load when: editing *.tf files, running
  terraform plan/apply/import, running aws CLI commands that modify infrastructure, creating
  S3 buckets or DynamoDB tables, or working in a terraform/ directory. Marker files: *.tf,
  *.tfvars, .terraform.lock.hcl, backend.tf, terraform/.
markers:
  - terraform/
  - .terraform.lock.hcl
globs:
  - "**/*.tf"
  - "**/*.tfvars"
alwaysApply: false
tier: 3
user-invocable: true
---
# Infrastructure & Terraform

Generalizable practices for managing cloud infrastructure with Terraform and the AWS CLI.

---

## Project Structure

```
terraform/
├── main.tf          # Resource definitions
├── variables.tf     # Input variables with validation
├── outputs.tf       # Output values
├── locals.tf        # name_prefix, common_tags
├── backend.tf       # Remote state
├── provider.tf      # Provider + version constraints
└── environments/    # dev.tfvars, prod.tfvars
```

---

## Remote State (S3 + DynamoDB)

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "<your-state-bucket>"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

## Plan → Apply Workflow

**NEVER run `terraform apply` without a prior `plan`. NEVER auto-approve.**

```bash
# 1. Format and validate
terraform fmt -recursive && terraform validate

# 2. Generate a saved plan
terraform plan -out=tfplan -var-file=environments/<env>.tfvars

# 3. Review plan output — STOP and ask for user approval
#    Summarize: resources to add, change, destroy. Highlight any destroys.

# 4. Apply only after explicit approval
terraform apply tfplan
```

- The `-out=tfplan` flag ensures the exact reviewed plan is what gets applied.
- If the plan shows unexpected destroys, investigate before proceeding.
- For `-refresh-only` applies (state drift correction), the same flow applies: plan first, review, then apply.

---

## Variables — Validation & Sensitive

```hcl
# variables.tf
variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test, or prod."
  }
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true   # never echoed in plan/apply output
}
```

---

## Locals — name_prefix & common_tags

```hcl
# locals.tf
locals {
  name_prefix = "${var.project}-${var.environment}"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Usage
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"
  tags = local.common_tags
}
```

---

## Conditional Logic by Environment

```hcl
retention_in_days = var.environment == "prod" ? 30 : 7
skip_final_snapshot = var.environment != "prod"
```

---

## S3 Hardening

```hcl
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } }
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket                  = aws_s3_bucket.main.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

---

## ECS Deployment Circuit Breaker

```hcl
resource "aws_ecs_service" "app" {
  # ...
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true   # auto-rollback on failed deployment
  }
}
```

---

## Destructive Command Gating

**Never execute these without explicit user confirmation:**

- `aws s3 rm` / `aws s3 rb` — delete objects or buckets
- `aws ec2 terminate-instances`
- `aws rds delete-db-cluster` / `delete-db-instance`
- `aws ecs delete-service` / `delete-cluster`
- `aws ecr delete-repository`
- `aws secretsmanager delete-secret`
- `aws lambda delete-function`
- `terraform state rm <addr>` — removes a resource from state without destroying it (orphans the live resource — Terraform will no longer manage it)
- `terraform state mv <src> <dst>` — moves/renames a resource in state (if wrong, the old address gets destroyed on next apply and the new address gets recreated)
- Any command with `delete`, `terminate`, `remove`, `destroy`, or `--force`

Protocol: explain blast radius → ask for explicit confirmation → wait for approval.

---

## Pre-command: Verify Identity

Before any infrastructure change, confirm the active account and profile:

```bash
echo "AWS_PROFILE=$AWS_PROFILE"
aws sts get-caller-identity
# Verify the Account field matches your intended target
```

⚠️ **Profile contamination risk:** `AWS_PROFILE` set in one terminal (or via direnv) can leak into child processes, editor shells, and AI agent sessions. Always verify the active profile — don't assume it matches the project you're working in. If `AWS_PROFILE` and `AWS_ACCESS_KEY_ID` are both set, the explicit keys take precedence and `AWS_PROFILE` is silently ignored.

If credentials are expired (`ExpiredToken` / `InvalidClientTokenId`), refresh before retrying.

---

## JMESPath Queries for Programmatic Parsing

```bash
# Extract a single field
aws ecs describe-services --cluster my-cluster --services my-service \
  --query 'services[0].status' --output text

# Filter a list
aws ec2 describe-instances \
  --query 'Reservations[].Instances[?State.Name==`running`].InstanceId' \
  --output json

# Pipe to jq
aws secretsmanager list-secrets --output json | jq '.SecretList[].Name'
```

---

## Resource Protection

Use `prevent_destroy` on stateful resources that should never be accidentally deleted:

```hcl
resource "aws_s3_bucket" "backups" {
  bucket = "my-critical-bucket"

  lifecycle {
    prevent_destroy = true
  }
}
```

Terraform will **error and refuse** any plan that would destroy a `prevent_destroy` resource. Apply this to: S3 buckets, databases (RDS, DynamoDB), KMS keys, and any resource where data loss is unrecoverable. To intentionally remove the resource, you must first set `prevent_destroy = false`, apply, then remove.

---

## Troubleshooting

```bash
# Stuck lock            terraform force-unlock <lock-id>
# Import existing       terraform import aws_ecs_cluster.main <name>
# Refresh-only plan     terraform apply -refresh-only
# Debug output          TF_LOG=DEBUG terraform plan 2>&1 | tee tf-debug.log
# Validate / format     terraform validate && terraform fmt -recursive
# Inspect state         terraform state list / terraform state show <addr>
```
