---
name: python-debug
description: >
  Python-specific debugging playbook — traceback analysis, common exception patterns,
  import system debugging, async/await pitfalls, test isolation techniques, mocking
  gotchas, and performance profiling. Complements debugging-methodology (language-agnostic)
  and python-uv (tooling). Load when: investigating Python exceptions, test failures that
  aren't obvious from the error message, import errors, async bugs, or performance issues.
  Trigger phrases: "traceback", "exception", "test fails", "ImportError", "async bug",
  "slow", "memory leak", "flaky test", "mock not working".
markers:
  - pyproject.toml
  - uv.lock
globs:
  - "**/*.py"
alwaysApply: false
tier: 3
user-invocable: true
---

# Python Debugging Playbook

Python-specific debugging patterns and playbooks. Use alongside `debugging-methodology` (for the scientific method) and `python-uv` (for tooling conventions).

---

## 1. Traceback Reading Protocol

Reading a Python traceback:

1. Start at the **BOTTOM** — that's the actual exception (type + message)
2. Work **UP** — each frame shows the call chain
3. Find the **BOUNDARY** — where does your code hand off to library code?
4. The bug is usually at the boundary or in the last frame of YOUR code

### Common Exception Patterns

| Exception | What It Really Means | First Diagnostic Step |
|-----------|---------------------|----------------------|
| `AttributeError: 'NoneType' has no attribute 'x'` | Something returned `None` unexpectedly | Check the function one frame up — missing return? failed lookup? |
| `TypeError: func() got an unexpected keyword argument 'x'` | API changed or wrong function signature | Check dependency version: `uv run pip show <pkg>` |
| `KeyError: 'x'` | Dict doesn't have expected key | Check data shape at runtime — print/log the dict |
| `RecursionError` | Infinite recursion | Check base case, look for circular references |
| `StopIteration` | Generator exhausted unexpectedly | Usually caught by `for` loop hiding it; check generator logic |
| `TypeError: unsupported operand type(s)` | Wrong type in expression | Print/log `type()` of operands |
| `ValueError: invalid literal for int()` | String-to-number conversion of bad input | Check input data, add validation |
| `FileNotFoundError` | Wrong working directory or relative path | Check `os.getcwd()`, use `pathlib.Path(__file__).parent` |
| `PermissionError` | File owned by different user/process | Check `ls -la`, file locks |
| `ConnectionRefusedError` | Service not running or wrong port | Check service status, port binding |
| `JSONDecodeError` | Response isn't JSON (HTML error page, empty body) | Print/log raw `response.text` before parsing |
| `pydantic.ValidationError` | Input doesn't match schema | Read error details — shows exact field and constraint |

---

## 2. Import System Debugging

Inspect import resolution from the shell:

```bash
# Trace what Python loads (and from where) for a given import
python -v -c "import mymodule" 2>&1 | grep mymodule

# Find files that shadow the module name on PYTHONPATH
find . -name "mymodule.py" -not -path "./.venv/*"
```

Inspect inside the Python process (REPL or test fixture):

```python
# Confirm which file Python actually loaded
import mymodule; print(mymodule.__file__)

# Check sys.path order (first match wins)
import sys; print('\n'.join(sys.path))
```

### Common Import Failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` | Package not installed or wrong venv | `uv run pip show <pkg>` |
| `ImportError: cannot import name X from Y` | Circular import or name removed in newer version | Check import chain / check version changelog |
| `AttributeError` on import | Partial initialization from circular import | Restructure imports or use lazy import |
| Import works in REPL but not in tests | `sys.path` difference | Check conftest.py; use `uv run pytest` not bare `pytest` |
| Import works locally but not in CI | Missing dependency or extras | Check `[project.optional-dependencies]` in pyproject.toml |

### Circular Import Resolution

```python
# Pattern: move the import inside the function that needs it
def process_data():
    from myapp.models import DataModel  # lazy import breaks cycle
    return DataModel(...)

# Pattern: use TYPE_CHECKING for type annotations only
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myapp.models import DataModel

def process_data(model: DataModel) -> None: ...  # works at type-check time, no runtime import
```

---

## 3. Test Debugging Patterns

### Isolation Commands

```bash
# Run single test with maximum verbosity
uv run pytest -x --tb=long -vv -k "test_name"

# Show locals in traceback
uv run pytest --tb=long --showlocals

# Stop on first failure, drop into debugger
uv run pytest -x --pdb

# Check for test pollution — run in isolation vs. full suite
uv run pytest tests/test_file.py::TestClass::test_name -x
uv run pytest tests/ -x  # does it fail when preceded by other tests?

# Check fixture resolution
uv run pytest --fixtures | grep fixture_name

# Show test execution order (useful for pollution debugging)
uv run pytest -v --collect-only

# Run with random order to find hidden dependencies
uv run pytest -p randomly --randomly-seed=12345
```

### Mock Gotchas

- **Patch where it's USED, not where it's DEFINED**:
  ```python
  # WRONG — patches the original module, but your code already imported it
  @patch('requests.get')

  # RIGHT — patches the reference in your module
  @patch('myapp.module.requests.get')
  ```

- **Mock return value chain** for chained calls:
  ```python
  mock_client.return_value.query.return_value.fetchall.return_value = [...]
  ```

- **AsyncMock for async** — use `AsyncMock` not `Mock` for coroutines:
  ```python
  from unittest.mock import AsyncMock, patch

  @patch('myapp.service.fetch_data', new_callable=AsyncMock)
  async def test_async_thing(mock_fetch):
      mock_fetch.return_value = {"key": "value"}
      result = await my_async_function()
  ```

- **spec=True** — always use to catch API drift in mocks:
  ```python
  mock = Mock(spec=RealClass)  # AttributeError if you access non-existent attrs
  ```

- **Context manager mocks**:
  ```python
  mock_open = MagicMock()
  mock_open.__enter__ = Mock(return_value=mock_file)
  mock_open.__exit__ = Mock(return_value=False)
  ```

- **Property mocks** — attach to the TYPE not the instance:
  ```python
  with patch.object(type(instance), 'my_property', new_callable=PropertyMock, return_value=42):
      assert instance.my_property == 42
  ```

### Flaky Test Patterns

| Pattern | Cause | Fix |
|---------|-------|-----|
| Passes alone, fails in suite | Test pollution (shared state) | Use fresh fixtures, check class-scoped state |
| Fails intermittently | Race condition or time-dependent | Add proper waits, freeze time |
| Fails on CI only | Environment difference | Check Python version, OS, env vars |
| Fails after midnight | Date/time dependency | Use `freezegun` or `time_machine` |
| Fails on first run only | Missing setup / migration | Check fixture ordering, conftest setup |
| Order-dependent | Global state mutation | Reset state in teardown, use `tmp_path` |

---

## 4. Async/Await Pitfalls

### Missing Await

```python
# BUG: returns coroutine object, not result
result = async_function()

# CORRECT
result = await async_function()

# Detecting unawaited coroutines at dev time
import warnings
warnings.filterwarnings("error", category=RuntimeWarning, message="coroutine.*was never awaited")
```

### Blocking the Event Loop

```python
# WRONG — blocks the entire event loop
result = blocking_function()

# RIGHT — offload to thread pool
result = await asyncio.to_thread(blocking_function)

# For older Python (< 3.9)
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, blocking_function)
```

### Task Cancellation

```python
# Task cancellation MUST be re-raised
try:
    await long_operation()
except asyncio.CancelledError:
    # cleanup here (close connections, flush buffers)
    raise  # MUST re-raise — do not swallow

# Fire-and-forget tasks must store a reference
task = asyncio.create_task(background_work())
# Store `task` somewhere! Otherwise it may be GC'd before completion
background_tasks.add(task)
task.add_done_callback(background_tasks.discard)
```

### Common Async Bugs

| Bug | Symptom | Fix |
|-----|---------|-----|
| Fire-and-forget tasks | Task silently disappears, no result/error | Store reference, add done callback |
| Shared mutable state | Intermittent wrong values | Use `asyncio.Lock()` |
| Mixing sync and async | Event loop hangs, timeout errors | Use `asyncio.to_thread()` for sync code |
| Unobserved exception in task | "Task exception was never retrieved" warning | `await` the task or add done callback |
| Creating event loop inside async | "This event loop is already running" | Use `await` directly, not `asyncio.run()` |

---

## 5. Performance Profiling

### CPU Profiling

```bash
# Quick CPU profile — sorted by cumulative time
uv run python -m cProfile -s cumulative script.py 2>&1 | head -30

# Line-level profiling (needs line_profiler installed)
uv run kernprof -l -v script.py

# Profile a specific function interactively
uv run python -c "
import cProfile, pstats
from myapp.module import slow_function

prof = cProfile.Profile()
prof.runcall(slow_function, arg1, arg2)
stats = pstats.Stats(prof).sort_stats('cumulative')
stats.print_stats(20)
"
```

### Memory Profiling

```bash
# tracemalloc — find where memory is allocated
uv run python -c "
import tracemalloc
tracemalloc.start()
# ... run suspect code ...
snapshot = tracemalloc.take_snapshot()
for stat in snapshot.statistics('lineno')[:10]:
    print(stat)
"

# Object count growth detection
uv run python -c "
import gc, sys
gc.collect()
before = len(gc.get_objects())
# ... suspect operation ...
gc.collect()
after = len(gc.get_objects())
print(f'Object count delta: {after - before}')
"

# Find reference cycles preventing GC
uv run python -c "
import gc
gc.set_debug(gc.DEBUG_SAVEALL)
gc.collect()
print(f'Uncollectable cycles: {len(gc.garbage)}')
for obj in gc.garbage[:5]:
    print(type(obj), repr(obj)[:100])
"
```

### Common Performance Issues

| Pattern | Symptom | Fix |
|---------|---------|-----|
| N+1 queries | O(n) DB calls in loop | Batch query, prefetch, join |
| Quadratic string concat | `s += chunk` in loop | Use `''.join(parts)` or `io.StringIO` |
| List search in loop | `if x in big_list` | Convert to set: `if x in big_set` |
| Repeated regex compilation | `re.match(pattern, ...)` in loop | `compiled = re.compile(pattern)` outside loop |
| Unnecessary copies | `list(big_list)` everywhere | Use iterators/generators |
| Blocking in async | Sync I/O in `async def` | Use `asyncio.to_thread()` or async library |
| Eager loading of large datasets | OOM on startup | Use generators, lazy loading, pagination |
| Dict/list comprehension waste | Building then discarding | Use generator expression with `any()`/`sum()` |

---

## 6. Debugging Commands Quick Reference

```bash
# Full environment diagnostic
uv run python -c "import sys; print(f'Python: {sys.version}\nPath: {sys.executable}\nPlatform: {sys.platform}')"

# Check installed package version
uv run pip show <package> | grep -E "^(Name|Version|Location)"

# Run with all warnings as errors (catches hidden issues)
uv run python -W error script.py

# Run with faulthandler (catches segfaults, hangs — prints traceback on crash)
uv run python -X faulthandler script.py

# Trace all function calls (very verbose — scope to your module)
uv run python -m trace --trace script.py 2>&1 | grep "your_module"

# Check for common mistakes with pylint/ruff
uv run ruff check --select=E,W,F --statistics .

# Dump object at breakpoint for inspection
import pdb; pdb.set_trace()  # or: breakpoint()
```

---

## 7. When to Load Adjacent Skills

| Situation | Also Load |
|-----------|-----------|
| Bug fix attempt already failed once | `debugging-methodology` (scientific method) |
| Need to run tests or linters | `python-uv` (tooling conventions) |
| Debugging a FastAPI endpoint | `fastapi-patterns` |
| Test involves Docker containers | `docker-containers` |
| Debugging database migrations | `database-migrations` |
| Performance issue in async web app | `fastapi-patterns` + this skill's §4 and §5 |
