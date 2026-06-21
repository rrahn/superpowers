---
name: docker-containers
description: >
  Multi-stage Docker builds, layer ordering for cache efficiency, security hardening
  (non-root USER, no secrets in images), BuildKit cache mounts, .dockerignore templates,
  Compose healthchecks with depends_on conditions, image tagging strategy, and
  cross-platform builds for Apple Silicon to linux/amd64. Load when: editing or creating
  a Dockerfile, docker-compose.yml, compose.yaml, or .dockerignore; containerizing an
  application; optimizing Docker image size or build speed; debugging container builds or
  runtime failures; setting up CI/CD pipelines that build Docker images. Marker files:
  Dockerfile, docker-compose.yml, docker-compose.yaml, compose.yml, compose.yaml,
  .dockerignore.
markers:
  - Dockerfile
  - docker-compose.yml
  - docker-compose.yaml
  - compose.yml
  - compose.yaml
  - .dockerignore
globs:
  - "**/Dockerfile*"
  - "**/docker-compose*.yml"
  - "**/docker-compose*.yaml"
  - "**/compose*.yml"
  - "**/compose*.yaml"
alwaysApply: false
tier: 3
user-invocable: true
---
# Docker & Container Best Practices

Universal patterns for building, securing, and running containerized applications.

---

## Multi-Stage Builds

Use a builder stage to install/compile, copy only runtime artifacts to the final image:

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /build/.venv /app/.venv
COPY src/ /app/src/
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
CMD ["python", "-m", "src.main"]
```

### Go Multi-Stage Build

```dockerfile
FROM golang:1.23-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app ./cmd/server

FROM gcr.io/distroless/static-debian12
COPY --from=builder /app /app
USER nonroot:nonroot
ENTRYPOINT ["/app"]
```

### TypeScript/Bun Multi-Stage Build

```dockerfile
FROM oven/bun:latest AS builder
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

FROM oven/bun:slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
USER bun
CMD ["bun", "run", "dist/index.js"]
```

---

## Layer Ordering (Least → Most Frequently Changing)

```dockerfile
FROM python:3.12-slim                          # 1. Base image (rarely changes)
RUN apt-get update && apt-get install -y \     # 2. System deps (rarely change)
    libpq-dev && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./                 # 3. Dep manifests (change occasionally)
RUN pip install uv && uv sync --frozen --no-dev
COPY src/ /app/src/                            # 4. App code (changes frequently)
```

Always clean up in the **same `RUN` layer** (removing packages, apt lists, pip caches)
to avoid baking cache files into the image layer.

---

## Security

```dockerfile
# Non-root user — never run as root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Use specific tags in production — never `latest`
FROM python:3.12.1-slim
```

- Never hardcode secrets or tokens in a `Dockerfile`
- Never `COPY .env` into a production image — inject secrets at runtime
- Minimise installed packages to reduce attack surface

---

## BuildKit Cache Mounts

```bash
export DOCKER_BUILDKIT=1
```

```dockerfile
# Persist package manager cache across builds — speeds up CI significantly
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

```bash
# Reuse registry cache in CI
docker build --cache-from myregistry/myapp:latest -t myapp:latest .
```

---

## .dockerignore Template

```
.git
__pycache__
*.py[cod]
.venv
*.egg-info/
dist/
build/
.pytest_cache
.coverage
htmlcov/
.vscode
.idea
.github/
.env
.env.*
!.env.example
docs/
*.log
```

---

## Docker Compose Patterns

> **Naming:** Docker Compose v2 prefers `compose.yaml` (or `compose.yml`). The legacy `docker-compose.yml` name still works but is no longer the default.

```yaml
services:
  app:
    build: .
    env_file: .env
    depends_on:
      db:
        condition: service_healthy    # Wait for healthy, not just started
    deploy:
      resources:
        limits: { cpus: '2', memory: 2G }

  db:
    image: postgres:15-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Optional service — only starts with: docker-compose --profile tools up
  localstack:
    image: localstack/localstack:latest
    profiles: ["tools"]

volumes:
  postgres_data:
```

---

## Application Healthcheck

Add a `HEALTHCHECK` in your app's Dockerfile so orchestrators detect unresponsive processes:

```dockerfile
# For HTTP services — adjust port and path to your app
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

For distroless or minimal images without `curl`, use a tiny static binary or the app's own CLI:

```dockerfile
HEALTHCHECK --interval=30s CMD ["/app", "healthcheck"]
```

---

## Development Compose Override

Use `compose.override.yaml` to layer dev-only settings (bind mounts, debug ports) on top of your production `compose.yaml`. Docker Compose merges them automatically:

```yaml
# compose.override.yaml — DO NOT commit to production
services:
  app:
    build:
      target: builder              # Use the builder stage with full tooling
    volumes:
      - .:/app                     # Bind-mount source for hot-reload
      - /app/node_modules          # Anonymous volume — preserve container deps
    environment:
      - DEBUG=1
    ports:
      - "9229:9229"                # Debugger port
```

---

## Tagging Strategy

Always push three tags per build:

```bash
VERSION=1.2.3
COMMIT=$(git rev-parse --short HEAD)
IMAGE=myregistry/myapp

docker tag myapp:build ${IMAGE}:${VERSION}   # Immutable release reference
docker tag myapp:build ${IMAGE}:${COMMIT}    # Exact build traceability
docker tag myapp:build ${IMAGE}:latest       # Convenience for local dev
```

---

## Cross-Platform Builds

Always specify `--platform` when targeting cloud (especially when building on Apple Silicon):

```bash
docker build --platform linux/amd64 -f Dockerfile -t myapp:latest .
```

---

## Debugging Builds

```bash
# Inspect an intermediate stage — get a shell inside the builder
docker build --target builder -t myapp:builder .
docker run -it myapp:builder /bin/bash

# Force clean rebuild
docker build --no-cache -t myapp:debug .

# Runtime inspection
docker logs -f <container>          # Stream logs
docker exec -it <container> bash    # Shell into running container
docker stats <container>            # Live CPU/memory usage

# Cleanup
docker system prune -a --volumes    # Remove all unused images, containers, volumes
docker system df                    # Show disk usage breakdown
```
