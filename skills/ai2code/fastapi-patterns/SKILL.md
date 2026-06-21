---
name: fastapi-patterns
description: >
  FastAPI application patterns — project structure, lifespan startup/shutdown, Pydantic
  models with field validators, dependency injection via Annotated[T, Depends(...)],
  endpoint decorators (response_model, operation_id, summary), custom exception handlers,
  pydantic-settings config, timing middleware, pagination, health/readiness probes, rate
  limiting, and response caching. Load when: fastapi appears in pyproject.toml or
  requirements.txt dependencies, editing files that import from fastapi or starlette,
  creating new API endpoints or routers, adding middleware, or setting up Pydantic
  request/response models. Trigger phrases: "add endpoint", "create API", "FastAPI app",
  "lifespan", "Depends", "health check", "rate limit", "response_model".
markers:
  - "pyproject.toml"
  - "requirements.txt"
dependencies:
  - fastapi
  - starlette
globs:
  - "**/routers/**/*.py"
  - "**/dependencies.py"
  - "**/main.py"
alwaysApply: false
tier: 2
user-invocable: true
---
# FastAPI Development Patterns

## Project Structure

Organize by domain, not by file type:

```
src/<package>/
├── main.py           # App entry point
├── dependencies.py   # Shared dependency functions
├── middleware.py     # Custom middleware
├── settings.py       # Configuration
├── routers/          # Route modules (one per domain)
├── models/           # Pydantic request/response models
├── services/         # Business logic
└── clients/          # External API/service clients
```

## Application Setup

Use `lifespan` for startup/shutdown instead of deprecated `@app.on_event`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize pools, clients, caches
    yield
    # Shutdown: close pools, flush buffers

app = FastAPI(title="My API", version="1.0.0", lifespan=lifespan)
```

## Pydantic Models

Use `Field(description=..., example=...)` on every field. Use `field_validator` for input constraints. Set `from_attributes = True` on response models for ORM compatibility:

```python
from pydantic import BaseModel, Field, field_validator

class ItemRequest(BaseModel):
    name: str = Field(..., description="Item name", example="widget")
    quantity: int = Field(default=1, description="Requested quantity", example=5)

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("quantity must be >= 1")
        return v

class ItemResponse(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}
```

## Dependency Injection

Use `Annotated[Type, Depends(...)]` syntax. Never access shared resources directly in route handlers:

```python
from typing import Annotated
from fastapi import Depends

async def get_service(client: Annotated[HttpClient, Depends(get_client)]) -> MyService:
    return MyService(client)

@router.get("/items/{id}")
async def get_item(id: str, service: Annotated[MyService, Depends(get_service)]):
    return await service.get(id)
```

Override dependencies in tests without monkeypatching:

```python
def test_get_item():
    mock = AsyncMock()
    mock.get.return_value = {"id": "1", "name": "widget"}
    app.dependency_overrides[get_service] = lambda: mock
    assert TestClient(app).get("/items/1").status_code == 200
    app.dependency_overrides.clear()
```

## Endpoint Decorators

Every endpoint MUST include `response_model`, `operation_id`, and `summary`:

```python
@router.get(
    "/items/{id}",
    response_model=ItemResponse,
    operation_id="get_item_by_id",
    summary="Get item by ID",
    responses={404: {"description": "Item not found"}},
)
async def get_item(id: str, service: Annotated[MyService, Depends(get_service)]) -> ItemResponse:
    ...
```

## Error Handling

Register custom exception handlers on `app`:

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

class NotFoundError(Exception):
    pass

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors(), "body": exc.body})
```

Never leak raw stack traces. Use a status envelope for streaming:

```json
{"status": "ok",    "data": [...],        "error": null}
{"status": "error", "data": [...partial], "error": {"message": "...", "detail": "..."}}
```

## Configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_title: str = "My API"
    api_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}

settings = Settings()
```

## Timing Middleware

```python
import time
from starlette.middleware.base import BaseHTTPMiddleware

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
        return response

app.add_middleware(TimingMiddleware)
```

## CORS Middleware

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],  # or ["*"] for dev only
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
    max_age=600,
)
```

Never use `allow_origins=["*"]` with `allow_credentials=True` in production — browsers reject it. List explicit origins instead.

## Background Tasks

Inject `BackgroundTasks` for fire-and-forget work that runs after the response is sent:

```python
from fastapi import BackgroundTasks

async def send_notification(user_id: str, message: str) -> None:
    # e.g. send email, write audit log, push webhook
    ...

@router.post("/orders", response_model=OrderResponse, operation_id="create_order", summary="Create order")
async def create_order(
    order: OrderRequest,
    bg: BackgroundTasks,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    result = await service.create(order)
    bg.add_task(send_notification, result.user_id, f"Order {result.id} confirmed")
    return result
```

## Pagination

```python
from fastapi import Query

@router.get("/items", response_model=..., operation_id="list_items", summary="List items")
async def list_items(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
):
    return {"items": await service.list(skip, limit), "skip": skip, "limit": limit, "total": await service.count()}
```

## Health vs Readiness

Separate liveness (process alive?) from readiness (dependencies up?):

```python
@router.get("/health", operation_id="health_check", summary="Liveness probe")
async def health():
    return {"status": "ok", "version": settings.api_version}

@router.get("/ready", operation_id="readiness_check", summary="Readiness probe")
async def ready():
    try:
        await db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not ready")
```

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.get("/items/{id}")
@limiter.limit("30/minute")
async def get_item(request: Request, id: str):
    ...
```

## Response Caching

```python
from fastapi_cache.decorator import cache

@router.get("/items/{id}", response_model=ItemResponse, operation_id="get_item", summary="Get item")
@cache(expire=3600)
async def get_item(id: str):
    return await service.get(id)
```

## Async Testing

The sync `TestClient` can mask concurrency bugs. Use `httpx.AsyncClient` with `ASGITransport` for async tests:

```python
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.anyio
async def test_get_item():
    mock = AsyncMock()
    mock.get.return_value = {"id": "1", "name": "widget"}
    app.dependency_overrides[get_service] = lambda: mock
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/items/1")
            assert resp.status_code == 200
            assert resp.json()["name"] == "widget"
    finally:
        app.dependency_overrides.clear()
```

Requires `httpx` and `anyio` (or `pytest-asyncio` with `@pytest.mark.asyncio`).

## Streaming Responses

Use `StreamingResponse` with an async generator. Always handle `CancelledError` for client disconnects:

```python
import asyncio
from fastapi.responses import StreamingResponse

async def event_stream(service: EventService):
    try:
        async for event in service.subscribe():
            yield f"data: {event.model_dump_json()}\n\n"
    except asyncio.CancelledError:
        # Client disconnected — flush buffers, close cursors, etc.
        await service.unsubscribe()
        raise  # re-raise after cleanup

@router.get("/events", operation_id="stream_events", summary="Stream events (SSE)")
async def stream_events(
    service: Annotated[EventService, Depends(get_event_service)],
) -> StreamingResponse:
    return StreamingResponse(event_stream(service), media_type="text/event-stream")
```

## Rules

- NEVER create DB connections or heavy clients at module import time — use lifespan or `Depends`
- NEVER skip `response_model`, `operation_id`, or `summary` on any endpoint
- NEVER interpolate user input into SQL — use parameterized queries
- ALWAYS use `Annotated[T, Depends(...)]` for dependency injection
- ALWAYS handle `asyncio.CancelledError` in streaming generators — re-raise after cleanup
- ALWAYS close cursors and connections with `async with` context managers
- ALWAYS separate liveness (`/health`) from readiness (`/ready`) probes
