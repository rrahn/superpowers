---
name: lambda-async-job-processing
description: >
  Async job processing architecture using FastAPI on ECS, Lambda async invocation,
  DynamoDB for job state, S3 for results, and SSE for real-time progress. Explains
  why Lambda async invoke is preferred over SQS for long-running jobs. Use when:
  designing long-running compute jobs on Lambda, choosing between SQS and Lambda
  async invoke, implementing SSE from DynamoDB polling, handling Lambda crash/timeout
  recovery, or seeing the SQS visibility timeout problem (long retry delay for 15-min
  Lambda). Covers the 202-before-invoke pattern, stale job detection, per-item error
  handling, and cost model.
metadata:
  version: "1.0"
  sources: "https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html, https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-time-series.html"
user-invocable: true
---

# Lambda Async Job Processing

## 1. Problem

Long-running compute jobs (30 seconds to 15 minutes) break the synchronous HTTP
request-response model. Users submit work via an API and expect:

- **Immediate acknowledgment** — don't hold an HTTP connection open for minutes
- **Real-time progress** — know what percentage is done, not just "pending"
- **Reliable completion** — if the compute crashes, detect it and report failure
- **Cost efficiency** — pay only for compute time, not idle polling infrastructure

Failure modes are diverse and must all be handled:

| Failure | Cause | Symptom |
|---------|-------|---------|
| Lambda OOM | Undersized memory | Process killed, no application-level error |
| Lambda timeout | Job exceeds 15-min limit | Abrupt termination mid-execution |
| Transient AWS error | S3/DynamoDB throttle | SDK call fails, retryable |
| Bad input | Invalid parameters | Deterministic failure, not retryable |
| Invoke failure | Lambda service error | 500 from `invoke()` call |

The architecture must distinguish between pre-submission errors (return 400/500
synchronously) and post-submission failures (track via job state). Users must never
be left wondering whether their job is running, succeeded, or silently died.

## 2. Architecture Overview

```
Client                API (ECS/FastAPI)              AWS Services
──────                ────────────────              ────────────
  │                         │
  ├─POST /jobs─────────────►│
  │                         ├─ Validate input
  │                         ├─ Upload to S3 ──────────► S3 (inputs/)
  │                         ├─ Create job record ─────► DynamoDB (PENDING)
  │◄─── 202 {job_id} ──────┤  ← COMMITMENT POINT
  │                         │
  │                         ├─ background: invoke ────► Lambda (async)
  │                         │                           │
  │                         │                           ├─ Update → PROCESSING
  ├─GET /jobs/{id}/stream──►│                           ├─ Process items...
  │                         ├─ Poll DynamoDB ◄──────────┤  (update progress)
  │◄─── SSE: progress ─────┤                           │
  │◄─── SSE: progress ─────┤                           ├─ Upload results → S3
  │◄─── SSE: completed ────┤◄──────────────────────────┤─ Update → COMPLETED
  │                         │
```

### The 202-Before-Invoke Pattern

Return HTTP 202 to the client BEFORE invoking Lambda. This is the commitment point:

- **Before 202**: validation errors return 400, server errors return 500. No job record exists.
- **After 202**: the job record exists in DynamoDB. ALL subsequent failures (invoke failure,
  Lambda crash, timeout) are tracked via job state — never lost.

This decouples request handling from compute invocation. If the Lambda invoke call itself
fails, a background task updates the job to FAILED. The client discovers this via SSE or
polling the job status endpoint.

```python
# FastAPI endpoint — the commitment point
@router.post("/jobs", status_code=202)
async def submit_job(request: JobRequest) -> JobResponse:
    validate_input(request)                          # 400 if bad
    s3_key = upload_input(request.payload)            # 500 if S3 down
    job = create_job_record(request.user_id, s3_key)  # 500 if DynamoDB down
    # ── COMMITMENT POINT: 202 returned after this line ──
    background_tasks.add_task(invoke_lambda, job.job_id, s3_key)
    return JobResponse(job_id=job.job_id, status="PENDING")
```

## 3. Why Lambda Async Invoke (Not SQS)

### The SQS Visibility Timeout Problem

SQS → Lambda event source mapping requires:

```
visibility_timeout ≥ 6 × Lambda_timeout + MaximumBatchingWindowInSeconds
```

For a 15-minute (900s) Lambda with no batching window: 6 × 900 = 5400s (90 min).
The minimum is ≥ 900s (`≥ Lambda_timeout`), but AWS recommends ≥ 5400s (6×) for
safety. Add `MaximumBatchingWindowInSeconds` if a batch window is configured.

**The problem**: if a job fails after 30 seconds, the message stays invisible for the
remaining visibility timeout (870s min, up to 5370s) before retry. Unacceptable.

**Mitigations evaluated and rejected:**

| Mitigation | Why It Fails |
|------------|-------------|
| `ChangeMessageVisibility(0)` on failure | Only works for caught exceptions. Lambda OOM, timeout, and segfault kill the process — no cleanup code runs. |
| Self-re-enqueue on failure | Same crash problem. Dead process can't enqueue anything. |
| Short visibility + extend periodically | Adds heartbeat complexity. Still fails on crash — no heartbeat = wait for full timeout. |
| SQS + Step Functions | Adds $25/million state transitions. Overkill for simple invoke-and-track. |

### Lambda Async Invoke

`InvocationType='Event'` returns 202 immediately. Lambda runs in the background with
built-in retry at ~1min and ~2min intervals (configurable via `EventInvokeConfig`).

```python
import boto3
lambda_client = boto3.client("lambda")

async def invoke_lambda(job_id: str, input_s3_key: str) -> None:
    try:
        lambda_client.invoke(
            FunctionName="compute-processor",
            InvocationType="Event",
            Payload=json.dumps({
                "job_id": job_id,
                "input_s3_key": input_s3_key,
            }).encode(),
        )
    except Exception:
        # Invoke itself failed — mark job as FAILED immediately
        update_job_status(job_id, "FAILED", error="Lambda invoke failed")
```

### Recommended Lambda Configuration

```python
# Terraform / CDK config
max_retry_attempts = 0          # Disable job-level retry (see §4)
dead_letter_queue = sqs_dlq_arn # Monitor failures
timeout = 900                   # 15 minutes max
memory_size = 2048              # Right-size for workload
```

## 4. Why No Job-Level Retry

Disable Lambda async invoke retries (`max_retry_attempts=0`). Most compute failures
are deterministic — retrying produces the same result:

| Deterministic (don't retry) | Transient (retry at SDK level) |
|-----------------------------|-------------------------------|
| Bad input data | S3 GetObject 503 |
| License/auth expired | DynamoDB ProvisionedThroughputExceeded |
| Resource limit exceeded | Network timeout |
| OOM (same input = same OOM) | Lambda service 500 (rare) |
| Timeout (same input = same timeout) | |

Handle transient AWS errors WITHIN the Lambda handler using SDK-level exponential
backoff (see §8). This retries individual API calls, not the entire job.

Job-level retry wastes compute: a 14-minute job that fails writing results would
re-run all 14 minutes of compute. SDK-level retry on the final write costs seconds.

Route failed invocations to an SQS dead-letter queue for monitoring and alerting.
Operators can inspect the DLQ and manually re-submit if a failure was truly transient.

## 5. DynamoDB Job State

### Table Design

```
Table: jobs
  job_id        (S)  — PK, UUID v4
  user_id       (S)  — Owner
  status        (S)  — PENDING | PROCESSING | COMPLETED | FAILED
  progress      (N)  — 0-100 percentage
  created_at    (S)  — ISO 8601
  updated_at    (S)  — ISO 8601, used for stale detection
  result_s3_key (S)  — S3 key for output artifact
  error_message (S)  — Human-readable failure reason
  item_summary  (M)  — Per-item success/fail counts
  options       (M)  — Job configuration (preserved for debugging)
  ttl           (N)  — Unix epoch for auto-deletion

GSI: user-jobs-index
  PK: user_id
  SK: created_at (descending for "most recent first")
```

### State Machine

```
  PENDING ──invoke──► PROCESSING ──success──► COMPLETED
     │                    │
     │                    └──failure──► FAILED
     └──invoke fails──► FAILED
```

Transitions are enforced via conditional writes:

```python
table.update_item(
    Key={"job_id": job_id},
    UpdateExpression="SET #s = :new_status, updated_at = :now",
    ConditionExpression="#s = :expected_status",
    ExpressionAttributeNames={"#s": "status"},
    ExpressionAttributeValues={
        ":new_status": "PROCESSING",
        ":expected_status": "PENDING",
        ":now": datetime.utcnow().isoformat(),
    },
)
```

Use **On-Demand capacity mode**. At low-to-moderate volume (<1000 jobs/day), cost is
negligible (~$0.003/month). Switch to Provisioned only if sustained throughput exceeds
cost threshold.

Set TTL to auto-delete job records after 30 days. Completed results in S3 can use
separate lifecycle policies.

## 6. SSE Streaming via DynamoDB Polling

### Why Polling (Not DynamoDB Streams)

DynamoDB Streams would require: a consumer Lambda to read the stream → a fan-out
mechanism (Redis pub/sub, SNS, or WebSocket API Gateway) to route events to the
correct SSE connection on the correct ECS instance. That is three additional services
for marginally lower latency.

Polling `GetItem` on a single job_id every 500ms is simple, cheap, and sufficient.
At 500ms intervals, a 5-minute job makes ~600 reads. With on-demand pricing at
$0.125/million read request units (us-east-1, Standard table), that costs $0.000075
per job.

### Implementation

```python
from fastapi import Request
from fastapi.responses import StreamingResponse
import asyncio, json

@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str, request: Request) -> StreamingResponse:
    return StreamingResponse(
        _stream_events(job_id, request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
async def _stream_events(job_id: str, request: Request):
    last_status = None
    last_progress = None
    while True:
        if await request.is_disconnected():
            break
        job = get_job(job_id, consistent_read=True)
        if job is None:
            yield _sse({"event_type": "error", "message": "Job not found"})
            break
        # Detect stale jobs (see §7)
        if _is_stale(job):
            mark_job_failed(job_id, "Job timed out (no progress update)")
            job["status"] = "FAILED"
        # Emit on change
        if job["status"] != last_status or job.get("progress") != last_progress:
            last_status = job["status"]
            last_progress = job.get("progress")
            yield _sse(_build_event(job))
        # Terminal states end the stream
        if job["status"] in ("COMPLETED", "FAILED"):
            break
        await asyncio.sleep(0.5)

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
```

### SSE Event Format

Use unnamed events (no `event:` field) with a `event_type` discriminator in the JSON
payload. This matches the `EventSource.onmessage` handler pattern on the client.

```
data: {"event_type": "status", "status": "PROCESSING", "progress": 0}

data: {"event_type": "progress", "status": "PROCESSING", "progress": 45}

data: {"event_type": "completed", "status": "COMPLETED", "result_url": "/jobs/abc/result"}

data: {"event_type": "failed", "status": "FAILED", "error": "Out of memory"}
```

Use `ConsistentRead=True` on the `GetItem` call. Eventually consistent reads can lag
by up to 1 second, adding perceptible delay to progress updates.

## 7. Stale Job Detection (Crash Recovery)

Lambda crashes (OOM, timeout, segfault) produce no application-level error. The job
stays in PROCESSING forever unless detected externally. Three mechanisms handle this:

### Fast Path: Invoke Failure

If `lambda_client.invoke()` raises after retries (~1-2 seconds), the background task
immediately updates DynamoDB to FAILED. The client sees failure within seconds.

### SSE Handler Detection

The SSE polling loop checks `updated_at` on every read. If the job is PROCESSING and
`updated_at` exceeds a threshold (Lambda timeout + 60s buffer), mark it FAILED:

```python
from datetime import datetime, timedelta

STALE_THRESHOLD = timedelta(minutes=16)  # Lambda timeout (15m) + 1m buffer

def _is_stale(job: dict) -> bool:
    if job["status"] not in ("PENDING", "PROCESSING"):
        return False
    updated = datetime.fromisoformat(job["updated_at"])
    return datetime.utcnow() - updated > STALE_THRESHOLD
```

### Periodic Cleanup (Safety Net)

A background task scans for stale jobs every 5-10 minutes. This catches jobs where
no SSE client is connected (e.g., user closed the browser):

```python
# Query GSI or scan with filter
response = table.scan(
    FilterExpression="(#s = :pending OR #s = :processing) AND updated_at < :cutoff",
    ExpressionAttributeNames={"#s": "status"},
    ExpressionAttributeValues={
        ":pending": "PENDING",
        ":processing": "PROCESSING",
        ":cutoff": cutoff_iso,
    },
)
for item in response["Items"]:
    mark_job_failed(item["job_id"], "Stale job detected (no progress)")
```

### Conditional Writes Prevent Races

Multiple SSE clients or the cleanup task may detect the same stale job simultaneously.
Conditional writes ensure only the first update succeeds:

```python
def mark_job_failed(job_id: str, reason: str) -> None:
    try:
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #s = :failed, error_message = :reason, updated_at = :now",
            ConditionExpression="#s IN (:pending, :processing)",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":failed": "FAILED", ":reason": reason,
                ":pending": "PENDING", ":processing": "PROCESSING",
                ":now": datetime.utcnow().isoformat(),
            },
        )
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        pass  # Already terminal — another writer got there first
```

## 8. SDK-Level Retry Strategy

Inside the Lambda handler, use two retry tiers:

### Standard Tier (routine calls)

- **Retries**: 5, exponential backoff (100ms base, 2x multiplier, 3s max)
- **Total wait**: ~6s worst case
- **Use for**: S3 GetObject, DynamoDB progress updates, intermediate writes

### Aggressive Tier (final result writes)

- **Retries**: 8-10, exponential backoff (200ms base, 2x multiplier, 30s max)
- **Total wait**: ~60s worst case
- **Use for**: S3 PutObject (final result), DynamoDB status → COMPLETED

Aggressive retry on final writes is critical: all expensive compute is done, results
are in memory, and the Lambda invocation is about to end. Spending 30-60 seconds
retrying saves re-running minutes of compute.

### Retryable Conditions

Retry on: HTTP 500, 502, 503, 504, 429 (throttle), `ConnectionError`, `ReadTimeoutError`.
Do NOT retry: 400, 403, 404 (client errors are deterministic).

```python
from botocore.config import Config
standard_config = Config(retries={"max_attempts": 5, "mode": "adaptive"})
# Note: "adaptive" mode is experimental per AWS docs. Use "standard" if stability is preferred.
aggressive_config = Config(retries={"max_attempts": 10, "mode": "adaptive"})
s3_standard = boto3.client("s3", config=standard_config)
s3_aggressive = boto3.client("s3", config=aggressive_config)
```

## 9. Per-Item Error Handling

When a job processes multiple items, isolate failures per item:

```python
results = []
errors = []
for i, item in enumerate(items):
    try:
        result = process_item(item)
        results.append({"item_id": item["id"], "status": "success", "data": result})
    except Exception as e:
        errors.append({"item_id": item["id"], "status": "failed", "error": str(e)})
    update_progress(job_id, progress=int((i + 1) / len(items) * 100))

if results:
    # At least one success → COMPLETED with partial results
    upload_results(job_id, results)
    final_status = "COMPLETED"
else:
    # ALL items failed → FAILED
    final_status = "FAILED"

update_job_status(job_id, final_status, item_summary={
    "total": len(items), "succeeded": len(results), "failed": len(errors),
})
```

A job with 8/10 successful items is COMPLETED (partial success), not FAILED. Include
the per-item summary so the client can display which items need attention.

## 10. S3 Artifact Convention

```
{bucket}/{prefix}/inputs/{job_id}/input.json
{bucket}/{prefix}/results/{job_id}/output.json
```

Use S3 for all job artifacts because:
- Shareable via presigned URLs (no API proxy needed for downloads)
- Exceeds Lambda payload limits (6MB sync, 1MB async)
- Persistent and durable (11 nines)
- Lifecycle policies for automatic cleanup

Generate presigned URLs in the API layer for client downloads. Set expiry to 1 hour.

## 11. Cost Model

Estimated cost for **500 jobs/month**, average 2-minute execution, 2048MB Lambda:

| Service | Usage | Monthly Cost |
|---------|-------|-------------|
| Lambda | 500 × 120s × 2048MB (120K GB-s) | ~$2.00 |
| DynamoDB (on-demand) | ~500 writes + ~300K reads (SSE) | ~$0.04 |
| S3 | ~1GB stored + transfers | ~$0.05 |
| ECS (API) | 0.25 vCPU / 0.5GB (shared) | ~$30-50 |
| **Total** | | **~$32-52** |

> **Note:** Lambda includes a permanent free tier of 400,000 GB-seconds/month. At 120K GB-seconds,
> this workload is fully covered — actual Lambda cost is $0.00 within the free tier.
> The $2.00 figure represents the marginal cost if the free tier is consumed by other workloads.

DynamoDB polling is essentially free at this scale. The dominant cost is ECS for the
API layer (which serves other endpoints too) and Lambda compute.
**Cost optimization levers:**
- Lambda ARM/Graviton: 20% cheaper than x86 at same memory
- Lambda memory right-sizing: use AWS Lambda Power Tuning to find optimal memory/cost
- S3 Intelligent-Tiering for results accessed infrequently after initial download

## 12. Rejected Alternatives

| Alternative | Why Rejected |
|-------------|-------------|
| **SQS → Lambda** | Visibility timeout problem (§3). Minutes-to-90-minute retry delay on failure. |
| **Step Functions Express** | 5-minute execution cap. Insufficient for 15-min jobs. |
| **Step Functions Standard** | $25/million state transitions. 25x cost of async invoke for simple jobs. |
| **S3-only state** | No conditional updates, no indexes, no atomic transitions. Requires scan for listing. |
| **EventBridge** | Adds routing complexity for same latency. No advantage over direct invoke. |
| **DynamoDB Streams → SSE** | Requires consumer Lambda + fan-out (Redis/SNS) to route to correct ECS instance. Three services for marginally lower latency. |
| **WebSockets (API GW)** | $0.25/million connection-minutes + $1/million messages. Requires connection management. SSE is simpler for server→client push. |
| **Synchronous invoke + long poll** | Holds HTTP connection for minutes. Load balancer timeouts, connection drops, no progress visibility. |

## 13. Verification Checklist

Use these scenarios to validate any implementation of this pattern:

- [ ] Submit valid job → receive 202 with `job_id` before Lambda starts
- [ ] Connect SSE → receive progress events at ~500ms intervals
- [ ] Job completes → SSE emits `completed` event with result URL
- [ ] Submit invalid input → receive 400 (no job record created)
- [ ] Kill Lambda mid-execution → stale detection marks FAILED within threshold
- [ ] Lambda invoke fails → job marked FAILED within seconds (fast path)
- [ ] Process 10 items, 2 fail → COMPLETED with `succeeded: 8, failed: 2`
- [ ] Two SSE clients watch same job → both receive events, no race on stale detection
- [ ] Job with no SSE client → periodic cleanup marks stale jobs FAILED
- [ ] DynamoDB conditional write on already-terminal job → no-op (no error)
