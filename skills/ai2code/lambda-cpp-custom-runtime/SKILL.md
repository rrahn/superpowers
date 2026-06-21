---
name: lambda-cpp-custom-runtime
description: >
  Build, package, and test C++ Lambda custom runtime handlers in Docker containers
  based on public.ecr.aws/lambda/provided:al2023. Use when: building a C++ Lambda
  function, using the Lambda provided base image, cross-compiling on Apple Silicon,
  diagnosing vendored .so incompatibilities in Lambda containers,
  testing Lambda containers locally with RIE, pushing Lambda images with
  docker buildx, or seeing errors like
  "fork/exec /var/runtime/bootstrap: no such file or directory",
  "AWS_LAMBDA_RUNTIME_API not set", "bootstrap: not found",
  or "UnsupportedMediaTypeException" when updating Lambda function code.
  Covers the custom runtime HTTP API, Dockerfile structure, RIE symlink fix,
  cross-platform builds, buildx provenance manifests, and static linking gotchas.
metadata:
  version: "1.2"
  sources: >
    https://docs.aws.amazon.com/lambda/latest/dg/runtimes-custom.html,
    https://docs.aws.amazon.com/lambda/latest/dg/images-create.html,
    https://github.com/aws/aws-lambda-runtime-interface-emulator
user-invocable: true
---

# C++ Lambda Custom Runtime — Build, Package, and Test

## Problem

AWS Lambda has no built-in C++ runtime. You must implement the custom runtime API
yourself: a bootstrap binary that polls for invocations and posts responses. The
official docs cover the HTTP API but skip the Docker packaging pitfalls — especially
the RIE symlink issue that causes `fork/exec /var/runtime/bootstrap: no such file or
directory` when testing locally, and the cross-compilation traps when building on
Apple Silicon.

## Trigger Conditions

- Error: `fork/exec /var/runtime/bootstrap: no such file or directory`
- Error: `AWS_LAMBDA_RUNTIME_API not set`
- Error: `bootstrap: not found` or `exec format error`
- Building a C++ Lambda function with Docker
- Using `public.ecr.aws/lambda/provided:al2023` base image
- Testing a Lambda container locally on macOS
- Cross-compiling C++ for Lambda on Apple Silicon (M1/M2/M3/M4)
- Pushing Lambda container images with `docker buildx build --push`
- Error: `UnsupportedMediaTypeException` when calling `update-function-code`

## Custom Runtime API

The bootstrap binary implements a simple HTTP polling loop against the Lambda Runtime API.

### Lifecycle

```
                    ┌─────────────────────────────────┐
                    │         INIT PHASE               │
                    │  Read AWS_LAMBDA_RUNTIME_API     │
                    │  One-time setup (load model, etc)│
                    └──────────────┬──────────────────┘
                                   │
              ┌────────────────────▼────────────────────┐
              │            INVOKE LOOP                   │
              │                                          │
              │  GET /runtime/invocation/next  (blocks)  │
              │  Extract Lambda-Runtime-Aws-Request-Id   │
              │  Process event payload                   │
              │  POST /runtime/invocation/{id}/response  │
              │  ── or on error ──                       │
              │  POST /runtime/invocation/{id}/error     │
              └──────────────────────────────────────────┘
```

### API Endpoints

All endpoints are relative to `http://${AWS_LAMBDA_RUNTIME_API}/2018-06-01/`:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `runtime/invocation/next` | GET | Long-poll for next event (no timeout) |
| `runtime/invocation/{id}/response` | POST | Send successful result |
| `runtime/invocation/{id}/error` | POST | Report invocation error |
| `runtime/init/error` | POST | Report initialization error |

### Minimal C++ Bootstrap (libcurl)

```cpp
#include <curl/curl.h>
#include <cstdlib>
#include <string>
#include <iostream>

static size_t write_cb(char* ptr, size_t size, size_t nmemb, std::string* data) {
    data->append(ptr, size * nmemb);
    return size * nmemb;
}

static size_t header_cb(char* buf, size_t size, size_t nmemb, std::string* req_id) {
    std::string header(buf, size * nmemb);
    const std::string prefix = "lambda-runtime-aws-request-id: ";
    if (header.size() > prefix.size() &&
        strncasecmp(header.c_str(), prefix.c_str(), prefix.size()) == 0) {
        *req_id = header.substr(prefix.size());
        while (!req_id->empty() && (req_id->back() == '\r' || req_id->back() == '\n'))
            req_id->pop_back();
    }
    return size * nmemb;
}

int main() {
    const char* api = std::getenv("AWS_LAMBDA_RUNTIME_API");
    if (!api) {
        std::cerr << "AWS_LAMBDA_RUNTIME_API not set\n";
        return 1;
    }
    std::string base = std::string("http://") + api + "/2018-06-01/runtime/";

    curl_global_init(CURL_GLOBAL_DEFAULT);

    while (true) {
        // 1. Get next invocation
        std::string event, request_id;
        CURL* curl = curl_easy_init();
        curl_easy_setopt(curl, CURLOPT_URL, (base + "invocation/next").c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &event);
        curl_easy_setopt(curl, CURLOPT_HEADERFUNCTION, header_cb);
        curl_easy_setopt(curl, CURLOPT_HEADERDATA, &request_id);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 0L);  // no timeout — long poll
        curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        // 2. Process and respond
        std::string response = "{\"statusCode\": 200, \"body\": \"Hello from C++\"}";

        curl = curl_easy_init();
        std::string url = base + "invocation/" + request_id + "/response";
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, response.c_str());
        curl_easy_perform(curl);
        curl_easy_cleanup(curl);
    }
}
```

## Docker Image Structure

### File Layout

```
/var/task/                    ← ${LAMBDA_TASK_ROOT}
├── bootstrap                 ← Your compiled binary (must be executable)
└── lib/                      ← Shared libraries (already on LD_LIBRARY_PATH)
    ├── libcurl.so.4
    └── libmylib.so

/var/runtime/
└── bootstrap                 ← Symlink to /var/task/bootstrap (for RIE)
```

### Dockerfile Template

```dockerfile
# --- Build stage ---
FROM --platform=linux/amd64 public.ecr.aws/lambda/provided:al2023 AS build

RUN dnf install -y gcc-c++ cmake libcurl-devel && dnf clean all

WORKDIR /build
COPY src/ src/
COPY CMakeLists.txt .

RUN cmake -B build -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_FLAGS="-march=x86-64 -O2" && \
    cmake --build build --parallel $(nproc)

# --- Runtime stage ---
FROM --platform=linux/amd64 public.ecr.aws/lambda/provided:al2023

COPY --from=build /build/build/bootstrap ${LAMBDA_TASK_ROOT}/bootstrap

# Copy only the shared libs your binary actually needs
COPY --from=build /usr/lib64/libcurl.so.4 ${LAMBDA_TASK_ROOT}/lib/

# RIE fix: /lambda-entrypoint.sh looks for /var/runtime/bootstrap
RUN ln -sf ${LAMBDA_TASK_ROOT}/bootstrap /var/runtime/bootstrap

ENTRYPOINT ["./bootstrap"]
```

## RIE Testing (The Non-Obvious Part)

The Lambda Runtime Interface Emulator (RIE) is baked into the `provided:al2023` base
image. It starts via `/lambda-entrypoint.sh`, which searches for the bootstrap binary in
this order: `/var/task/bootstrap` → `/opt/bootstrap` → `/var/runtime/bootstrap`. If your
binary is at `/var/task/bootstrap` and you pass `./bootstrap` as the handler argument, the
RIE should find it directly. However, if the handler arg doesn't resolve, RIE falls back
through the search path. The symlink ensures the fallback works:

```
fork/exec /var/runtime/bootstrap: no such file or directory
```

### Fix: Symlink in Dockerfile

```dockerfile
RUN ln -sf ${LAMBDA_TASK_ROOT}/bootstrap /var/runtime/bootstrap
```

In production Lambda, the service invokes your container's ENTRYPOINT directly and does not search `/var/runtime/bootstrap` — the symlink is only exercised by the RIE's fallback search.

> **Note:** `/lambda-entrypoint.sh` is baked into the base image layers and its exact
> behavior is opaque — the search order above was determined by testing, not from
> readable source.

### Local Testing Commands

```bash
# Build the image
docker build --platform linux/amd64 -t my-lambda .

# Run with RIE (use the base image's entrypoint)
docker run -d -p 9000:8080 \
  --entrypoint /lambda-entrypoint.sh \
  my-lambda ./bootstrap

# Invoke
curl -s -XPOST \
  "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"key": "value"}'
```

### If the Symlink Isn't in the Image

Override the entrypoint to create it at runtime:

```bash
docker run -d -p 9000:8080 \
  --entrypoint /bin/sh my-lambda \
  -c "mkdir -p /var/runtime && \
      ln -sf /var/task/bootstrap /var/runtime/bootstrap && \
      exec /lambda-entrypoint.sh ./bootstrap"
```

### Debugging RIE Issues

```bash
# Check the binary exists and is executable
docker run --rm --entrypoint /bin/sh my-lambda -c \
  "ls -la /var/task/bootstrap /var/runtime/bootstrap"

# Check shared library resolution
docker run --rm --entrypoint /bin/sh my-lambda -c \
  "ldd /var/task/bootstrap"

# Run bootstrap directly (bypasses RIE — will fail with RUNTIME_API error, but
# confirms the binary itself loads)
docker run --rm --entrypoint /var/task/bootstrap my-lambda
# Expected: "AWS_LAMBDA_RUNTIME_API not set" — this means the binary works
```

## Cross-Platform Builds (Apple Silicon)

Building on M1/M2/M3/M4 Macs for Lambda's x86_64 environment requires care.

### Rules

1. Use `--platform linux/amd64` on every `FROM` directive (both build and runtime stages).
2. Replace `-march=native` with `-march=x86-64` in all compiler flags — `native` targets
   ARM on Apple Silicon, producing binaries that crash on Lambda.
3. Expect slow builds (~5-6 min for large C++ libs) due to QEMU emulation.
4. Verify the binary architecture inside the container:

```bash
docker run --rm --entrypoint /bin/sh my-lambda -c \
  "file /var/task/bootstrap"
# Expected: ELF 64-bit LSB executable, x86-64
```

### CMake Flag Override

```cmake
# In CMakeLists.txt — never use -march=native for Lambda targets
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -march=x86-64 -O2")
```

## Static vs Shared Linking

### Prefer Static Linking

Static linking reduces cold start time (~50ms for C++ vs 2-6s for Python+SWIG) by
eliminating dynamic linker overhead. Use it for everything except very large
dependencies.

### Shared Library Gotchas

| Problem | Symptom | Fix |
|---------|---------|-----|
| Vendored libcurl linked against OpenSSL 1.1 | `libssl.so.1.1: not found` | Use AL2023's system libcurl instead of vendored |
| Vendored libstdc++ too old | `GLIBCXX_3.4.xx not found` | Remove vendored copy; use base image's system lib |
| Static libs built with older glibc | `__exp_finite` undefined symbols | Add finite math shims (see `glibc-finite-math-compat`) |
| Missing shared lib at runtime | `error while loading shared libraries` | Copy to `${LAMBDA_TASK_ROOT}/lib/` or static-link |

## Vendored Shared Library Diagnostic Workflow

Scientific C++ codebases often vendor shared libraries (`.so` files) compiled on older
systems. When building a Docker image with a modern base image (Amazon Linux 2023,
Ubuntu 22.04+), these vendored libs may be incompatible: linked against older OpenSSL,
older glibc, or older libstdc++. Follow this workflow to diagnose and resolve
incompatibilities systematically.

### Step 1: Identify Vendored Shared Libraries

List every `.so` in the vendor/dependency directory and check what each one links against:

```bash
# List all .so files in the vendor/dependency directory
find /build/dependencies/lib/ -name '*.so*' -type f

# Check what each .so was linked against
for so in /build/dependencies/lib/*.so*; do
  echo "=== $so ==="
  ldd "$so" 2>&1 | grep -E "not found|libssl|libcrypto|libstdc\+\+"
done
```

Any line containing `not found` is a hard failure. Lines showing `libssl`, `libcrypto`, or
`libstdc++` need version verification in the next step.

### Step 2: Check Symbol Version Requirements

Compare the version symbols each vendored lib requires against what the base image provides:

```bash
# Check GLIBCXX version requirements
# NOTE: Run objdump inside the Docker container (Linux), not on macOS —
# GNU objdump -p and LLVM objdump -p produce different output.
objdump -p /build/dependencies/lib/libfoo.so | grep GLIBCXX
# Compare against system:
strings /usr/lib64/libstdc++.so.6 | grep GLIBCXX | tail -5

# Check OpenSSL version requirements
ldd /build/dependencies/lib/libcurl.so.4 | grep -E "libssl|libcrypto"
# If it wants libssl.so.1.1 but system has libssl.so.3 → incompatible
```

If the vendored lib requires a symbol version higher than the system provides, it cannot
load. If the system version is higher, the vendored copy is unnecessary.

### Step 3: Decision Framework

| Vendored Library | System Has | Decision | Rationale |
|-----------------|-----------|----------|-----------|
| `libcurl.so` linked to OpenSSL 1.1 | OpenSSL 3.x | **Use system libcurl** | Install `libcurl-devel`, add `-lcurl` to link flags, remove vendored copy |
| `libstdc++.so.6` (GLIBCXX ≤ 3.4.11) | GLIBCXX 3.4.33+ | **Use system libstdc++** | Don't copy vendored copy to runtime image — system version is always newer |
| `libtensorflow.so` (custom build) | Not available | **Keep vendored** | No system package; copy to runtime image, run `ldconfig` |
| `librestclient-cpp.so` (niche lib) | Not available | **Keep vendored** | No system package; verify with `ldd` in runtime image |

**General rule**: If the system provides a newer, compatible version → use system. If the
lib is custom/niche and not in system repos → keep vendored but verify with `ldd` in the
final runtime image.

### Step 4: Verify in Runtime Image

After building the final image, confirm all shared libs resolve and no stale vendored
copies leaked in:

```bash
# Verify ALL shared libs resolve
docker run --rm --entrypoint /bin/sh my-lambda -c \
  "ldd /var/task/bootstrap | grep 'not found'"
# Expected: no output (all resolved)

# Check no vendored lib was accidentally included
docker run --rm --entrypoint /bin/sh my-lambda -c \
  "ls -la /var/task/lib/ /usr/lib64/libcurl* /usr/lib64/libstdc++*"
```

### Common Pitfalls

- Vendored `libcurl.so.4` built against OpenSSL 1.1 — as of early 2026, Amazon Linux
  2023 only has OpenSSL 3.x, NO compat packages exist
- Vendored `libstdc++.so.6` from an older GCC — system version is always sufficient
  for your code compiled on the same system
- Copying vendored libs "just in case" pollutes `LD_LIBRARY_PATH` and may shadow the
  correct system version
- Always run `ldd` in the RUNTIME stage (not builder) — builder may have dev packages
  that runtime doesn't

## Docker Buildx Provenance and Lambda (The OCI Manifest Trap)

When pushing Lambda container images with `docker buildx build --push`, buildx (v0.10+)
attaches **provenance attestations** by default. This produces an OCI image index
(manifest list) with multiple manifests: one for the actual image and one (or more) for
attestation data.

Lambda does not understand OCI image indexes with attestations. When you call
`update-function-code` pointing at an image pushed this way, Lambda returns:

```
UnsupportedMediaTypeException: The image manifest type
"application/vnd.oci.image.index.v1+json" is not supported by Lambda.
```

### Fix: Disable Provenance

```bash
docker buildx build --platform linux/amd64 --provenance=false \
  -t 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-lambda:latest \
  --push .
```

The `--provenance=false` flag tells buildx to push a plain Docker v2 manifest
(`application/vnd.docker.distribution.manifest.v2+json`) instead of an OCI manifest index.

### When This Applies

- Any `docker buildx build --push` to ECR for Lambda consumption (not just C++ runtimes)
- Both `provided:al2023` custom runtimes and managed runtimes (Python, Node, etc.)
- Does NOT affect ECS/Fargate — ECS accepts OCI manifest indexes

### Alternatives

```bash
# Alternative 1: Set BUILDX_NO_DEFAULT_ATTESTATIONS globally
export BUILDX_NO_DEFAULT_ATTESTATIONS=1
docker buildx build --platform linux/amd64 --push -t ... .

# Alternative 2: Use plain docker build + docker push (no buildx)
# This only works for native-platform builds (no cross-platform)
docker build -t ... .
docker push ...
```

### Verification

After pushing, verify the manifest type:

```bash
# Check the image manifest — should be a single manifest, not an index
aws ecr batch-get-image \
  --repository-name my-lambda \
  --image-ids imageTag=latest \
  --query 'images[0].imageManifest' \
  --output text --profile your-profile | python3 -c "
import sys, json
m = json.load(sys.stdin)
print(f\"mediaType: {m.get('mediaType', 'NOT SET')}\")
print(f\"Schema version: {m.get('schemaVersion', 'NOT SET')}\")
"
# Expected: mediaType: application/vnd.docker.distribution.manifest.v2+json
# NOT: application/vnd.oci.image.index.v1+json
```

## Cold Start Performance

| Approach | Typical Cold Start | Notes |
|----------|-------------------|-------|
| C++ custom runtime (static) | ~50ms | Container image deployment; zip deployments may be faster at ~15-45ms |
| C++ custom runtime (shared libs) | ~80-150ms | Depends on lib count/size |
| Python + SWIG wrapper | 2-6s (estimated) | Import overhead dominates |
| Python + subprocess to C++ | 1-3s (estimated) | Fork/exec overhead |

## Verification Checklist

After building and before deploying:

1. `file /var/task/bootstrap` shows `ELF 64-bit LSB executable, x86-64`
2. `ldd /var/task/bootstrap` resolves all shared libraries (no "not found")
3. Running the binary directly prints `AWS_LAMBDA_RUNTIME_API not set` (confirms it loads)
4. RIE test returns a valid response via `curl` to port 9000
5. `docker image inspect` shows `Architecture: amd64`

## Notes

- The `/var/runtime/bootstrap` symlink is the single most common failure when testing
  C++ Lambda containers locally. The error message gives no hint about the actual cause.
- In production Lambda, the real runtime service sets `AWS_LAMBDA_RUNTIME_API` and
  invokes `/var/task/bootstrap` directly — the RIE symlink is only needed for local testing.
- For Lambda functions that load large models or data files, use provisioned concurrency
  to amortize cold start across invocations.

## References

- [Custom Runtime API](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-custom.html)
- [Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [Lambda RIE](https://github.com/aws/aws-lambda-runtime-interface-emulator)
- [Lambda Base Images (ECR)](https://gallery.ecr.aws/lambda/provided)
