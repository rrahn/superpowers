---
name: database-migrations
description: >
  PostgreSQL database management with SQLAlchemy + Alembic — migrations, async engine
  pooling, eager loading, naming conventions, and test fixtures. Load when: (1) the project
  has an alembic/ directory, alembic.ini, or migrations/ folder, (2) you are writing or
  reviewing Alembic migration files (alembic revision, upgrade, downgrade), (3) you are
  configuring SQLAlchemy async engines (create_async_engine, AsyncSession, connection pools),
  (4) you see errors like PoolTimeout, N+1 queries, naive datetime warnings, connection
  leaks, or asyncio.CancelledError in database streaming code, (5) you are writing pytest
  fixtures for async database sessions, or (6) you need zero-downtime DDL patterns
  (expand/migrate/contract, CREATE INDEX CONCURRENTLY). Marker files: alembic.ini, alembic/,
  migrations/, models.py with SQLAlchemy imports.
markers:
  - alembic.ini
  - alembic/
  - migrations/
globs:
  - "**/alembic/**/*.py"
  - "**/models.py"
  - "**/models/**/*.py"
alwaysApply: false
tier: 3
---
# Database & Migration Practices

Standards for PostgreSQL databases using SQLAlchemy + Alembic.

---

## 1. Alembic Migration Best Practices

- **Always review auto-generated migrations** — autogenerate misses data-only changes, computed columns, and custom types
- **One logical change per migration** — keep migrations atomic and focused
- **Test both directions** — verify `upgrade` and `downgrade` paths before merging
- **Never edit an applied migration** — create a new migration to fix issues
- **Document complex migrations** — add comments for non-obvious operations
- **Break large migrations** — split long-running DDL into smaller steps

```bash
alembic revision --autogenerate -m "Add users table"
alembic revision -m "Backfill display names"   # data-only
alembic upgrade head && alembic downgrade -1   # test both paths
```

---

## 1a. Multi-Head Migration Conflicts

When two developers branch from the same Alembic head, merging both creates **multiple heads** — Alembic refuses to run `upgrade head` and CI breaks.

```bash
# Detect: more than one line = conflict
uv run alembic heads
# → abc123 (head)
# → def456 (head)

# Resolve: create a merge migration
uv run alembic merge -m "merge heads abc123 def456" abc123 def456

# Verify single head, then upgrade
uv run alembic heads        # should show exactly one
uv run alembic upgrade head
```

**CI gate:** add `alembic heads | wc -l` to your pipeline and fail if the count exceeds 1. Catch conflicts before they reach production.

---

## 1b. Async `env.py` Configuration

Alembic's migration runner is synchronous. Bridge it to an async engine with `run_sync()`:

```python
# alembic/env.py — online migration block
import asyncio
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,  # no pooling for short-lived migration runs
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())
```

Key: `pool.NullPool` is mandatory — async engines must not be reused across `asyncio.run()` calls.

---

## 2. Zero-Downtime Migration Pattern

Never drop or rename in a single deployment. Use three separate deploys:

| Phase | Action | App compatibility |
|-------|--------|-------------------|
| 1 — Expand | Add new column / table | Old + new code work |
| 2 — Migrate | Backfill data | Old + new code work |
| 3 — Contract | Drop old column / table | Only new code deployed |

---

## 3. Non-Locking Index Creation

```sql
-- CONCURRENTLY avoids an exclusive table lock (takes longer, safe for production)
CREATE INDEX CONCURRENTLY ix_orders_user_id ON orders (user_id);
```

In Alembic migrations, use `op.execute("CREATE INDEX CONCURRENTLY ...")` or `op.create_index(..., postgresql_concurrently=True)`.

---

## 4. SQLAlchemy Async Engine Configuration

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    pool_size=10,        # persistent connections kept open
    max_overflow=20,     # extra connections allowed beyond pool_size
    pool_timeout=30,     # seconds to wait before raising PoolTimeout
    pool_recycle=3600,   # recycle connections after 1 h (avoids stale sockets)
    pool_pre_ping=True,  # test connection health before use
    echo=False,          # set True in dev for SQL logging
)

# Always use context managers — never manually close
async with AsyncSession(engine) as session:
    async with session.begin():
        result = await session.execute(stmt)
```

---

## 5. N+1 Avoidance with Eager Loading

```python
from sqlalchemy.orm import selectinload, joinedload

# selectinload — separate IN query; safe for large collections
stmt = select(Order).options(selectinload(Order.items))

# joinedload — single JOIN; best for to-one relationships
stmt = select(Order).options(joinedload(Order.customer))

result = await session.execute(stmt)
orders = result.scalars().unique().all()
```

Rule: if a route renders a relationship, load it eagerly in the query.

---

## 6. Naming Conventions

| Object | Convention | Example |
|--------|-----------|---------|
| Tables | `snake_case`, plural nouns | `user_accounts` |
| Columns | `snake_case` | `created_at`, `user_id` |
| Primary key | `id` | — |
| Foreign key | `<table_singular>_id` | `order_id` |
| Index | `ix_<table>_<column(s)>` | `ix_orders_user_id` |
| Unique constraint | `uq_<table>_<column(s)>` | `uq_users_email` |
| Check constraint | `ck_<table>_<rule>` | `ck_products_price_positive` |

---

## 7. Column Type Rules

- **Timestamps** — always `TIMESTAMP WITH TIME ZONE`; never store naive datetimes
- **JSON** — use `JSONB` (indexed, binary); avoid `JSON`
- **Booleans** — use `BOOLEAN`; never `INTEGER` (0/1)
- **IDs** — `INTEGER` or `BIGINT`; use `BIGINT` for tables expected to grow large
- **Strings** — `VARCHAR(n)` when length is known; `TEXT` for unbounded



---

## 8. ETL Best Practices

ETL batch pattern: chunk source rows → validate → `INSERT … ON CONFLICT DO UPDATE` → commit per chunk.

```python
import asyncpg
from itertools import islice

UPSERT = """
    INSERT INTO target (id, name, value)
    VALUES ($1, $2, $3)
    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, value = EXCLUDED.value
"""

async def chunked_upsert(pool: asyncpg.Pool, rows, *, chunk_size: int = 1000):
    it = iter(rows)
    while chunk := list(islice(it, chunk_size)):
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(UPSERT, [(r["id"], r["name"], r["value"]) for r in chunk])
        logger.info("upserted %d rows", len(chunk))
```

Each chunk gets its own transaction — a failure mid-ETL loses only the current chunk, not the entire batch.



---

## 9. Lazy Connection Pattern

Never create engine instances or connection pools at module import time.

```python
# BAD — engine created on import, fails if DB is unreachable at startup
engine = create_async_engine(os.getenv("DATABASE_URL"))

# GOOD — create on first access
_engine: AsyncEngine | None = None

def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(os.getenv("DATABASE_URL"), ...)
    return _engine
```

In FastAPI, initialise pools inside the `lifespan` context, not at module level.

---

## 10. Pytest DB Fixture Pattern

```python
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("postgresql+asyncpg://...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()   # isolate tests — undo all writes

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

- Each test gets a clean session; rollback replaces slow teardown/recreate
- Never share state between tests; mark slow ones `@pytest.mark.integration`

---

## 11. asyncio.CancelledError in Streaming Generators

`CancelledError` is not a regular exception — it must be re-raised, not swallowed.

```python
async def stream_rows(pool, stmt):
    task = None
    try:
        task = asyncio.create_task(run_count_query(pool, stmt))
        async with pool.connection() as conn:
            async with conn.cursor(name=f'cur_{uuid4().hex}') as cur:
                async for row in cur.stream(stmt):
                    yield serialize(row)
    except asyncio.CancelledError:
        if task:
            task.cancel()          # cancel child tasks
        raise                      # always re-raise CancelledError
    except Exception as exc:
        logger.error("stream error", exc_info=exc)
        yield encode_error(exc)    # surface partial data + error to client
    finally:
        if task and not task.done():
            task.cancel()
```

---

## Common Pitfalls

- **Hardcoded connection strings** — never put credentials in `alembic.ini`; override in `env.py`:
  ```python
  # alembic/env.py — top of file, before run_migrations_*
  import os
  config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
  ```
- **N+1 queries** — load relationships eagerly in the query, not in a loop
- **Missing timezone** — naive datetimes cause subtle ordering and comparison bugs
- **Large transactions** — hold locks; break into smaller commits
- **SQL injection** — always use parameterized queries / `bindparam()`; never f-string SQL
- **Connection leaks** — always use `async with` context managers for sessions and connections
- **Blocking calls in async** — use `run_in_executor` if you must call a sync driver
