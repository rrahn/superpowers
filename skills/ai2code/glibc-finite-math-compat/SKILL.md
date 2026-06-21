---
name: glibc-finite-math-compat
description: >
  Fix linker errors for __exp_finite, __pow_finite, __acos_finite, and SIMD
  _ZGVbN4v___expf_finite symbols when linking static .a libraries compiled with
  -ffinite-math-only on glibc 2.31+. Use when: undefined reference to '__exp_finite'
  or any __*_finite variant, undefined reference to '_ZGVbN4v___expf_finite',
  linking vendor static libs on Amazon Linux 2023, Ubuntu 22.04+, Fedora 34+,
  or Docker multi-stage builds with newer glibc. Covers scalar C shims and
  x86_64 SIMD assembly shims.
metadata:
  version: "1.0"
  sources: "https://sourceware.org/glibc/wiki/Release/2.31, https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html"
user-invocable: true
---

# glibc Finite-Math Compatibility — Linking Static Libraries on glibc 2.31+

## Problem

Static C/C++ libraries compiled with GCC's `-ffinite-math-only` (or `-ffast-math`, which
implies it) generate calls to `__exp_finite`, `__pow_finite`, `__acos_finite`, etc. instead
of the standard `exp`, `pow`, `acos`.

In glibc <= 2.30, these `__*_finite` symbols were regular linkable symbols. Starting with
glibc 2.31, these `__*_finite` symbols were **removed from the static `libm.a`**. They
still exist in the shared `libm.so.6` for runtime compatibility, but **cannot be resolved
at static link time** when linking against `.a` archives, causing:

```
undefined reference to `__exp_finite'
undefined reference to `__pow_finite'
```

Additionally, GCC auto-vectorized code may reference SIMD variants like
`_ZGVbN4v___expf_finite` (SSE2, 4-wide float) and `_ZGVbN2v___log_finite` (SSE2, 2-wide
double). These SIMD `_finite` variants don't exist in libmvec at all — they need assembly
shims that forward to the non-finite equivalents.

You cannot recompile the static library (it's a vendor blob). You need shim objects.

## Trigger Conditions

- Linker error: `undefined reference to '__exp_finite'` (or any `__*_finite` variant)
- Linker error: `undefined reference to '_ZGVbN4v___expf_finite'` (SIMD variants)
- Linking static `.a` libraries on glibc >= 2.31 (Amazon Linux 2023, Ubuntu 22.04+, Fedora 34+, Debian 12+)
- Docker multi-stage builds where the builder glibc is newer than the original compile environment
- The static library was compiled with `-ffinite-math-only` or `-ffast-math`

## Solution

### Step 1: Identify Missing Symbols

Extract the undefined `_finite` symbols from linker output or the static library:

```bash
nm -u vendor_lib.a 2>/dev/null | grep '_finite'
# or from the linker error output, collect all __*_finite and _ZGV*_finite symbols
```

### Step 2: Create the Scalar Shim (`finite_math_shim.c`)

This C file defines all 34 `__*_finite` symbols as thin wrappers around standard libm
functions. The glibc `__*_finite` variants have identical signatures to their standard
counterparts, except `__gamma_r_finite` / `__gammaf_r_finite` which take an extra
`int *signgam` parameter.

```c
/* finite_math_shim.c
 *
 * Shim for __*_finite symbols removed from static libm.a in glibc 2.31+.
 * Compile: gcc -c -fPIC -O2 finite_math_shim.c -o finite_math_shim.o
 */
#include <math.h>

/* --- double variants --- */
double __acos_finite(double x)                  { return acos(x); }
double __asin_finite(double x)                  { return asin(x); }
double __atan2_finite(double y, double x)       { return atan2(y, x); }
double __cosh_finite(double x)                  { return cosh(x); }
double __exp_finite(double x)                   { return exp(x); }
double __exp2_finite(double x)                  { return exp2(x); }
double __fmod_finite(double x, double y)        { return fmod(x, y); }
double __hypot_finite(double x, double y)       { return hypot(x, y); }
double __log_finite(double x)                   { return log(x); }
double __log2_finite(double x)                  { return log2(x); }
double __log10_finite(double x)                 { return log10(x); }
double __pow_finite(double x, double y)         { return pow(x, y); }
double __sinh_finite(double x)                  { return sinh(x); }
double __sqrt_finite(double x)                  { return sqrt(x); }
double __remainder_finite(double x, double y)   { return remainder(x, y); }
double __scalb_finite(double x, double y)       { return scalb(x, y); }
double __gamma_r_finite(double x, int *signgam) { return lgamma_r(x, signgam); }  /* maps to lgamma_r — NOT tgamma */

/* --- float variants --- */
float __acosf_finite(float x)                   { return acosf(x); }
float __asinf_finite(float x)                   { return asinf(x); }
float __atan2f_finite(float y, float x)         { return atan2f(y, x); }
float __coshf_finite(float x)                   { return coshf(x); }
float __expf_finite(float x)                    { return expf(x); }
float __exp2f_finite(float x)                   { return exp2f(x); }
float __fmodf_finite(float x, float y)          { return fmodf(x, y); }
float __hypotf_finite(float x, float y)         { return hypotf(x, y); }
float __logf_finite(float x)                    { return logf(x); }
float __log2f_finite(float x)                   { return log2f(x); }
float __log10f_finite(float x)                  { return log10f(x); }
float __powf_finite(float x, float y)           { return powf(x, y); }
float __sinhf_finite(float x)                   { return sinhf(x); }
float __sqrtf_finite(float x)                   { return sqrtf(x); }
float __remainderf_finite(float x, float y)     { return remainderf(x, y); }
float __scalbf_finite(float x, float y)         { return scalbf(x, y); }
float __gammaf_r_finite(float x, int *signgam)  { return lgammaf_r(x, signgam); }
```

Compile:

```bash
gcc -c -fPIC -O2 finite_math_shim.c -o finite_math_shim.o
```

### Step 3: Create the SIMD Shim (`simd_finite_shim.S`) — x86_64 Only

GCC auto-vectorized code may call SIMD `_finite` variants that don't exist in libmvec.
These assembly shims forward to the non-finite libmvec equivalents via PLT.

```asm
/* simd_finite_shim.S
 *
 * SIMD shim for vectorized __*_finite symbols (x86_64 only).
 * Compile: gcc -c -fPIC simd_finite_shim.S -o simd_finite_shim.o
 * Link with: -lmvec
 */
    .text

    /* _ZGVbN4v___expf_finite -> _ZGVbN4v_expf (SSE2, 4-wide float) */
    .globl _ZGVbN4v___expf_finite
    .type  _ZGVbN4v___expf_finite, @function
_ZGVbN4v___expf_finite:
    jmp    _ZGVbN4v_expf@PLT
    .size  _ZGVbN4v___expf_finite, .-_ZGVbN4v___expf_finite

    /* _ZGVbN2v___log_finite -> _ZGVbN2v_log (SSE2, 2-wide double) */
    .globl _ZGVbN2v___log_finite
    .type  _ZGVbN2v___log_finite, @function
_ZGVbN2v___log_finite:
    jmp    _ZGVbN2v_log@PLT
    .size  _ZGVbN2v___log_finite, .-_ZGVbN2v___log_finite
```

Compile:

```bash
gcc -c -fPIC simd_finite_shim.S -o simd_finite_shim.o
```

### Step 4: Link Everything Together

Add the shim objects **before** the vendor library in the link order, and add `-lmvec`
if using the SIMD shim:

```bash
# Scalar only (most common case):
gcc -o myapp main.o finite_math_shim.o -lvendor -lm

# Scalar + SIMD:
gcc -o myapp main.o finite_math_shim.o simd_finite_shim.o -lvendor -lm -lmvec
```

Link order matters: shim objects must appear **before** the library that references the
`_finite` symbols so the linker sees the definitions first.

### Step 5: Integration Patterns

**CMake:**

```cmake
add_library(finite_math_shim OBJECT finite_math_shim.c)
target_compile_options(finite_math_shim PRIVATE -fPIC -O2)

# If SIMD shim needed:
enable_language(ASM)
add_library(simd_finite_shim OBJECT simd_finite_shim.S)
target_compile_options(simd_finite_shim PRIVATE -fPIC)

target_link_libraries(myapp PRIVATE
    finite_math_shim
    simd_finite_shim   # if needed
    vendor::lib
    m
    mvec                # if SIMD shim used
)
```

**Dockerfile (multi-stage):**

```dockerfile
COPY finite_math_shim.c simd_finite_shim.S /build/shims/
RUN gcc -c -fPIC -O2 /build/shims/finite_math_shim.c -o /build/shims/finite_math_shim.o \
 && gcc -c -fPIC /build/shims/simd_finite_shim.S -o /build/shims/simd_finite_shim.o
# Then include shim .o files in your link step
```

## Extending the SIMD Shim

If you encounter additional SIMD `_finite` symbols, decode the mangled name to determine
the forwarding target:

| Prefix | Meaning |
|--------|---------|
| `_ZGVbN4v_` | SSE2, 4-wide (float) |
| `_ZGVbN2v_` | SSE2, 2-wide (double) |
| `_ZGVdN8v_` | AVX2, 8-wide (float) |
| `_ZGVdN4v_` | AVX2, 4-wide (double) |
| `_ZGVeN16v_` | AVX-512, 16-wide (float) |
| `_ZGVeN8v_` | AVX-512, 8-wide (double) |

The pattern: strip `___` prefix and `_finite` suffix from the function name, keep the
`_ZGV*` prefix. Example: `_ZGVdN8v___expf_finite` forwards to `_ZGVdN8v_expf`.

Add a new `.globl` / `jmp` pair in the assembly file for each missing symbol.

## Verification

```bash
# 1. Confirm no remaining __*_finite undefined references:
nm -u myapp 2>/dev/null | grep '_finite' && echo "FAIL: unresolved _finite symbols" || echo "PASS"

# 2. Confirm the shim symbols are present:
nm myapp | grep '__exp_finite' | grep -q ' T ' && echo "PASS: shim linked" || echo "FAIL"

# 3. Runtime smoke test:
./myapp --version  # or whatever quick invocation confirms it loads
```

## Notes

- The scalar shim wrappers call standard libm functions which **do** perform NaN/Inf
  checks. The original `_finite` variants skipped those checks for speed. This means a
  minor performance regression on NaN/Inf edge cases — acceptable since the alternative
  is a link failure.
- `scalb` is obsolescent (use `scalbln`), but old vendor libs still reference it.
  Include `_XOPEN_SOURCE` or `_DEFAULT_SOURCE` if your toolchain warns about `scalb`.
- The `__gamma_r_finite` / `__gammaf_r_finite` functions map to `lgamma_r` / `lgammaf_r`
  (not `tgamma`). The `_r` suffix means they take a `signgam` output parameter.
- On aarch64/ARM, SIMD vectorization uses different name mangling — the `_ZGV` x86_64
  shim won't apply. Scalar shim works on all architectures.
- If linking a shared library (`.so`) rather than a static binary, the IFUNC symbols
  resolve at runtime and you likely don't need this shim at all.

## References

- [glibc 2.31 release notes](https://sourceware.org/glibc/wiki/Release/2.31) — `__*_finite` removal from static libm
- [GCC -ffinite-math-only docs](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html)
- [libmvec vector ABI](https://sourceware.org/glibc/wiki/libmvec) — `_ZGV` name mangling
