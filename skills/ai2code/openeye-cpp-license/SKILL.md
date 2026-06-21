---
name: openeye-cpp-license
description: >
  OpenEye/Cadence C++ toolkit license debugging — SIGSEGV during static init when
  OE_LICENSE is invalid/missing/placeholder, NULL+0x50 vtable crash in
  oi_add_license_fixed_key before main(), Cadence license format migration
  (#PRODUCT: oechem), signal handler diagnostic technique, and Docker container
  license injection. Load when: exit code 139 from OpenEye-linked binary, SIGSEGV
  at startup with no output, addr=0x50 in crash dump, oi_add_license_fixed_key or
  OEChemRequireLicenseOnce in backtrace, license validation fails after Cadence
  format change, or building containers with OpenEye C++ toolkits.
metadata:
  version: "1.1"
  sources: "empirical testing, OpenEye toolkit documentation"
user-invocable: true
---

# OpenEye/Cadence C++ Toolkit License Debugging

## 1. The Problem

When a C++ binary statically links OpenEye libraries (`liboechem.a`, `liboefizzchem.a`, etc.) and runs with an **invalid, missing, or placeholder** `OE_LICENSE` file, it crashes with **SIGSEGV during program startup — BEFORE `main()` is called**.

This is extremely misleading because:

- The crash looks like a build or linking bug
- It happens during `.init_array` execution (static constructors)
- **No error message is printed**
- Exit code is **139** (SIGSEGV), not a license error code

### Root Cause

OpenEye static libraries contain global constructors that initialize the license system during `.init_array` execution. The initialization calls `OEPlatform::oi_add_license_fixed_key()`, which reads the license file pointed to by `OE_LICENSE`. If the license is invalid or a placeholder, the internal license stream object is **NULL**, and the code dereferences `NULL + 0x50` (vtable access at offset 80), causing SIGSEGV.

### Diagnostic Signature

All of these together confirm the license crash:

| Signal | `SIGSEGV` at `addr=0x50` (NULL + 80 bytes = vtable offset) |
|--------|-------------------------------------------------------------|
| si_code | `1 (MAPERR)` — accessing unmapped memory |
| Backtrace | All frames in the main binary (not shared libs) |
| Frame chain | `_GLOBAL__sub_I_<File>.cpp` -> `OEChemRequireLicenseOnce()` -> `oi_add_license_fixed_key()` -> CRASH |
| Behavior | Does NOT crash with a valid license file |

## 2. Diagnosis Technique

### Step 1: Build a Signal Handler Shared Library

Compile this on the **host** (or inside the container), then `LD_PRELOAD` it to capture the crash details:

```c
// sighandler.c
// Linux x86_64 only — macOS uses DYLD_INSERT_LIBRARIES and different ucontext
// Compile: gcc -shared -fPIC -o sighandler.so sighandler.c -ldl
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <ucontext.h>
#include <execinfo.h>

void crash_handler(int sig, siginfo_t *si, void *ctx) {
    ucontext_t *uc = (ucontext_t *)ctx;
    fprintf(stderr, "\n=== SIGNAL %d CAUGHT ===\n", sig);
    fprintf(stderr, "Fault addr: %p\n", si->si_addr);
    fprintf(stderr, "si_code: %d\n", si->si_code);
    fprintf(stderr, "RIP: 0x%llx\n",
            (unsigned long long)uc->uc_mcontext.gregs[REG_RIP]);
    void *bt[64];
    int n = backtrace(bt, 64);
    fprintf(stderr, "\nBacktrace (%d frames):\n", n);
    backtrace_symbols_fd(bt, n, 2);
    _exit(1);
}

__attribute__((constructor)) void install_handler(void) {
    struct sigaction sa = {0};
    sa.sa_sigaction = crash_handler;
    sa.sa_flags = SA_SIGINFO | SA_RESETHAND;
    sigaction(SIGSEGV, &sa, NULL);
}
```

### Step 2: Run with LD_PRELOAD (Linux only — macOS uses `DYLD_INSERT_LIBRARIES`)

```bash
LD_PRELOAD=/path/to/sighandler.so ./your_binary
```

### Step 3: Map the Crash Address

```bash
nm your_binary | sort > symbols.txt
# Find the RIP address from the crash output in symbols.txt
# Look for oi_add_license_fixed_key, oi_query_license_information,
# or OEChemRequireLicenseOnce near the crash address
```

### Step 4: Confirm It's a License Issue

```bash
# Set a VALID license and re-run — crash disappears
export OE_LICENSE=/path/to/valid/oe_license.txt
./your_binary  # Should work now
```

## 3. The Fix

**Set `OE_LICENSE` to a valid, non-empty license file containing the `oechem` product license.**

```bash
export OE_LICENSE=/path/to/oe_license.txt
```

### Obtaining the License

Contact your OpenEye/Cadence account representative or check your organization's
internal license server. The license file is typically named `oe_license.txt`.

### Docker Containers

Mount or copy the license into the container:

```dockerfile
# Option A: Build-time COPY (if license is in build context)
COPY oe_license.txt /opt/openeye/oe_license.txt
ENV OE_LICENSE=/opt/openeye/oe_license.txt

# Option B: Runtime mount (preferred — no secrets in image)
# docker run -v /host/path/oe_license.txt:/opt/openeye/oe_license.txt:ro \
#   -e OE_LICENSE=/opt/openeye/oe_license.txt your_image
```

### Corporate Environments: Why curl Fails in Docker Builds

In corporate networks (Pfizer, banks, etc.), internal license servers use TLS certificates
signed by an internal CA (e.g., Pfizer's corporate root CA). Docker build containers do
NOT have these corporate CA certificates installed — they only have the public Mozilla CA
bundle.

Attempting to download the license during `docker build` fails:

```dockerfile
# This FAILS in corporate Docker builds:
RUN curl -fsSL https://internal-server.corp.com/oe_license.txt -o /opt/openeye/oe_license.txt
# Error: SSL certificate problem: unable to verify the first certificate
```

**Fix**: Download the license file locally (where corporate CAs are trusted), then `COPY`
it into the image:

```bash
# On your workstation (has corporate CA certs):
curl -fsSL https://internal-server.corp.com/oe_license.txt -o oe_license.txt
```

```dockerfile
# In Dockerfile — COPY the locally-downloaded file:
COPY oe_license.txt /opt/openeye/oe_license.txt
ENV OE_LICENSE=/opt/openeye/oe_license.txt
```

Add the license file to `.gitignore` — it contains proprietary keys:

```gitignore
oe_license.txt
```

**Alternative** (if you must download during build): inject the corporate CA cert bundle
into the build stage. This is fragile and ties the image to a specific corporate
infrastructure:

```dockerfile
# Less preferred — corporate CA injection
COPY corporate-ca-bundle.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
RUN curl -fsSL https://internal-server.corp.com/oe_license.txt -o /opt/openeye/oe_license.txt
```

### Validating the License File

Before running, verify the file is not empty and contains the oechem product:

```bash
# Check file exists and is non-empty
test -s "$OE_LICENSE" || echo "ERROR: OE_LICENSE file missing or empty"

# Check it contains oechem product (handles both old and Cadence formats)
grep -qi "oechem" "$OE_LICENSE" || echo "ERROR: No oechem product in license"
```

## 4. Cadence License Format Change

OpenEye was acquired by **Cadence Design Systems**. The license file format changed.

### Old Format (pre-Cadence)

```
#oechem <license-data-on-same-line>
```

Lines start directly with `#oechem`.

### New Cadence Format

```
#PRODUCT: oechem
#EXP_DATE: 2026 09 30
#FEATURES: python;java;clr
#LICENSEE: Company Name
#SITE: Global Sites
LICENSE_KEY: <64-char-hex-string>
```

Key differences:

| Field | Old Format | Cadence Format |
|-------|-----------|----------------|
| Product identifier | `#oechem` (line prefix) | `#PRODUCT: oechem` (metadata line) |
| Product name case | lowercase | **lowercase** (oechem, bioisostere, fastrocs) |
| License key | Embedded in `#oechem` line | Separate `LICENSE_KEY:` line (**no `#` prefix**) |
| Structure | Single line per product | Multi-line block per product |

### Code Implications

If your code validates license file content, search for `"oechem"` (not `"#oechem"`) to handle both formats:

```cpp
// BAD — breaks with Cadence format
if (line.find("#oechem") != std::string::npos) { ... }

// GOOD — works with both formats
if (line.find("oechem") != std::string::npos) { ... }
```

```python
# BAD
has_license = any(line.startswith("#oechem") for line in lines)

# GOOD
has_license = any("oechem" in line.lower() for line in lines)
```

## 5. Quick Decision Tree

```
Binary crashes with exit code 139 (SIGSEGV)?
  |
  +-- Is OE_LICENSE set?
  |     |
  |     +-- NO --> Set OE_LICENSE to valid license file. Done.
  |     |
  |     +-- YES --> Is the file non-empty and valid?
  |           |
  |           +-- NO (empty/placeholder) --> Replace with real license. Done.
  |           |
  |           +-- YES --> Use LD_PRELOAD signal handler to get backtrace.
  |                 |
  |                 +-- Shows oi_add_license_fixed_key? --> License issue
  |                 |     despite file existing. Check format, expiry,
  |                 |     product coverage.
  |                 |
  |                 +-- Different backtrace? --> Not a license issue.
  |                       Investigate as normal SIGSEGV.
```

## 6. Verification

```bash
# 1. Verify OE_LICENSE is set and file exists
test -s "$OE_LICENSE" && echo "PASS: License file exists" || echo "FAIL: Missing/empty"

# 2. Verify oechem product present (both formats)
grep -qi "oechem" "$OE_LICENSE" && echo "PASS: oechem found" || echo "FAIL: No oechem"

# 3. Run binary — should NOT exit with code 139
./your_binary --version; echo "Exit code: $?"
# Expected: normal output, exit code 0 (not 139)
```

## 7. Common Mistakes

1. **Placeholder license in Docker image**: Build scripts that copy a dummy `oe_license.txt` with placeholder content. The file exists but contains no valid license data.

2. **Expired license**: The file is valid format but past `#EXP_DATE`. Same SIGSEGV behavior.

3. **Wrong product**: License file has other OpenEye products but not `oechem`. The binary needs the specific product it was linked against.

4. **Format validation checking `#oechem`**: After Cadence migration, the prefix changed to `#PRODUCT: oechem`. Code that checks for the old prefix silently fails.

5. **Assuming the crash is a build bug**: The SIGSEGV-before-main pattern looks identical to a linking error or missing symbol. Always check `OE_LICENSE` first when OpenEye libs are involved.

## 8. Environment Checklist

Before running any OpenEye-linked binary:

```bash
# 1. OE_LICENSE is set
echo "OE_LICENSE=${OE_LICENSE:-(NOT SET)}"

# 2. File exists and is non-empty
ls -la "$OE_LICENSE" 2>/dev/null || echo "FILE NOT FOUND"

# 3. Contains oechem product
grep -c -i "oechem" "$OE_LICENSE" 2>/dev/null || echo "NO OECHEM PRODUCT"

# 4. Check expiry (Cadence format)
grep "#EXP_DATE:" "$OE_LICENSE" 2>/dev/null || echo "No expiry found (old format?)"
```
