---
name: uv-docker-builds
description: >
  Fix Python uv package manager pitfalls in multi-stage Docker builds — empty venv
  from hardlink breakage with cache mounts, ModuleNotFoundError from editable installs
  in multi-stage copies, and setuptools-scm version detection without .git directory.
  Use when: uv sync in Docker produces an empty .venv, ModuleNotFoundError for your
  own package in a runtime stage, LookupError from setuptools-scm unable to detect
  version, or building Python containers with uv and multi-stage Dockerfiles.
  Covers --link-mode=copy, --no-editable, and SETUPTOOLS_SCM_PRETEND_VERSION.
metadata:
  version: "1.0"
  sources: >
    https://docs.astral.sh/uv/guides/integration/docker/,
    https://setuptools-scm.readthedocs.io/en/latest/config/
user-invocable: true
---

# uv in Docker — Three Pitfalls That Break Multi-Stage Builds

## Problem

Using `uv` as the Python package manager inside Docker multi-stage builds introduces
three non-obvious failures. Each produces misleading errors that look like missing
dependencies or broken installs, when the root cause is a mismatch between uv's default
behavior and Docker's layer isolation model.

## Trigger Conditions

- Empty `.venv/lib/python3.x/site-packages/` after `uv sync` in Docker
- `ModuleNotFoundError` for your own package in the runtime stage, but dependencies work
- `LookupError: setuptools-scm was unable to detect version for ...`
- Error: `pretend-version` or `SETUPTOOLS_SCM_PRETEND_VERSION` in build logs
- Building a Python project with `uv sync` and `--mount=type=cache` in a Dockerfile
- Multi-stage Docker build where `.venv` is copied from builder to runtime stage

---

## Pitfall 1: Empty venv — Hardlink Breakage with Cache Mounts

### Symptom

After `uv sync` with `--mount=type=cache`, the `.venv` directory exists but
`site-packages` is empty or missing packages. The build succeeds without errors, but the
runtime container fails with `ModuleNotFoundError` for every dependency.

### Root Cause

On Linux, uv defaults to **hardlinks** (`--link-mode=hardlink`) when installing packages
from cache. With `RUN --mount=type=cache,target=/root/.cache/uv`, the cache mount is
temporary — it exists only during that `RUN` instruction. uv creates hardlinks from the
cache mount into `.venv/lib/python3.x/site-packages/`. When the `RUN` finishes and the
cache mount disappears, the hardlinks become **dangling** — they point to inodes that no
longer exist in the committed layer.

### Fix

Force uv to **copy** files instead of hardlinking:

```dockerfile
# Option A: Environment variable (applies to all uv commands)
ENV UV_LINK_MODE=copy

# Option B: Per-command flag
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --link-mode=copy
```

### When This Does NOT Apply

- If you are NOT using `--mount=type=cache` (no cache mount = no hardlink target to
  disappear), uv installs normally. But cache mounts significantly speed up rebuilds, so
  they are standard practice.
- On macOS Docker Desktop, the filesystem may use copies regardless, so the bug may not
  reproduce locally — it appears only in Linux CI or linux/amd64 buildx builds.

---

## Pitfall 2: ModuleNotFoundError — Editable Install in Multi-Stage

### Symptom

Dependencies work fine, but importing your own package fails with `ModuleNotFoundError`
in the runtime stage. The builder stage works correctly.

### Root Cause

By default, `uv sync` installs the current project in **editable mode**. This creates a
`.pth` file in `site-packages/` that points to the source directory (e.g.,
`/app/src/zing_service`). In a multi-stage build, only `.venv` is copied to the runtime
stage — the source directory `/app/src/` is not copied. The `.pth` file points to a path
that does not exist in the runtime image.

```
# What editable mode creates in site-packages/:
zing_service.pth  ->  contains: /app/src
# But /app/src doesn't exist in the runtime stage!
```

### Fix

Use `--no-editable` to install the project as a regular package (copies files into
`site-packages/` instead of creating a `.pth` pointer):

```dockerfile
# Two-phase install pattern:
# Phase 1: Install dependencies only (no project yet)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --link-mode=copy

# Phase 2: Copy source and install the project as a non-editable package
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --link-mode=copy
```

The two-phase approach also maximizes Docker layer caching — dependencies are cached as
long as `pyproject.toml` and `uv.lock` don't change.

### When This Does NOT Apply

- Development containers where the source is mounted as a volume — editable mode is
  correct there, because the source directory is always present.
- Single-stage builds where the source stays in the image.

---

## Pitfall 3: setuptools-scm Without .git

### Symptom

Build fails with:

```
LookupError: setuptools-scm was unable to detect version for '/app'
```

Or the installed package has version `0.0.0` or similar placeholder.

### Root Cause

`setuptools-scm` derives the package version from git tags and commit history. Standard
Docker best practice excludes `.git/` from the build context (via `.dockerignore`) because
it is large, changes constantly (breaking layer cache), and is not needed at runtime.
Without `.git/`, setuptools-scm cannot detect the version and fails.

### Fix

Use `SETUPTOOLS_SCM_PRETEND_VERSION` to inject the version at build time:

```dockerfile
# In Dockerfile — set a default, allow override at build time
ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0-dev
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${SETUPTOOLS_SCM_PRETEND_VERSION}
```

Build with a real version from git:

```bash
docker build \
  --build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$(git describe --tags --always) \
  -t myapp .
```

Or in CI:

```bash
docker build \
  --build-arg SETUPTOOLS_SCM_PRETEND_VERSION=${CI_COMMIT_TAG:-$(git describe --tags --always)} \
  -t myapp .
```

### When This Does NOT Apply

- Projects that don't use `setuptools-scm` for versioning (check `pyproject.toml` for
  `[tool.setuptools_scm]` or `dynamic = ["version"]` with `setuptools-scm` in
  build-system requires).
- If `.git/` is included in the Docker context (not recommended but works).

---

## Complete Dockerfile Pattern

This pattern combines all three fixes:

```dockerfile
# =============================================================================
# Stage 1: Build
# =============================================================================
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /usr/local/bin/uv

WORKDIR /app

# Fix #3: setuptools-scm without .git
ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0-dev
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${SETUPTOOLS_SCM_PRETEND_VERSION}

# Dependencies first (layer caching)
COPY pyproject.toml uv.lock ./

# Fix #1: --link-mode=copy prevents hardlink breakage with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --link-mode=copy

# Source + project install
COPY src/ src/

# Fix #2: --no-editable installs into site-packages, not a .pth file
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --link-mode=copy

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.12-slim-bookworm

RUN groupadd -r app && useradd -r -g app -d /app app
WORKDIR /app

# Copy only the venv — source is installed inside it (non-editable)
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER app
CMD ["python", "-m", "your_app"]
```

## Verification

After building, verify all three fixes work:

```bash
# 1. Check venv is not empty (Fix #1)
docker run --rm --entrypoint /bin/sh myapp -c \
  "ls /app/.venv/lib/python3.12/site-packages/ | head -20"
# Expected: populated with package directories

# 2. Check own package is importable (Fix #2)
docker run --rm myapp python -c "import your_package; print(your_package.__version__)"
# Expected: version string, no ModuleNotFoundError

# 3. Check no .pth files for your package (Fix #2)
docker run --rm --entrypoint /bin/sh myapp -c \
  "find /app/.venv/lib -name '*.pth' -exec cat {} +"
# Expected: no .pth pointing to /app/src

# 4. Check version is set correctly (Fix #3)
docker run --rm myapp python -c "import your_package; print(your_package.__version__)"
# Expected: the version you passed via --build-arg, not "0.0.0"
```

## Notes

- These three pitfalls interact: you can hit all three in one build and see only the most
  confusing error (empty venv). Fix them in order: link mode first, then editable, then
  version.
- `UV_LINK_MODE=copy` as an environment variable is simpler than per-command flags if you
  have multiple `uv sync` calls. But `ENV` persists into the runtime stage — harmless but
  unnecessary. Use `ARG` if you prefer a build-only variable.
- The `--frozen` flag ensures uv uses the lockfile exactly as committed — no resolution
  at build time. This is essential for reproducible builds.
- These patterns apply to any uv version. The hardlink default has been present since
  uv's first Linux release and is unlikely to change (it's a performance optimization).

## References

- [uv Docker integration guide](https://docs.astral.sh/uv/guides/integration/docker/)
- [setuptools-scm configuration](https://setuptools-scm.readthedocs.io/en/latest/config/)
- [Docker BuildKit cache mounts](https://docs.docker.com/build/cache/backends/)
