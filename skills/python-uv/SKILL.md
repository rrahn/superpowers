---
name: python-uv
description: >
  Python project tooling with uv, ruff, ty, pytest, and pre-commit — project discovery,
  validation commands, coding standards, report templates, and property-based testing with
  Hypothesis. Load when: the project has pyproject.toml or uv.lock, you are writing or
  reviewing Python code, running tests or linters, type-checking with ty, or delegating
  validation to @errand-runner. Prevents common AI agent habits: running bare python/pip/
  pytest without uv run, using Optional[X] or List[str] instead of modern X | None /
  list[str] syntax, ignoring ruff errors, or hardcoding paths instead of using pathlib.
  Marker files: pyproject.toml, uv.lock, .python-version, setup.py, setup.cfg.
markers:
  - pyproject.toml
  - uv.lock
  - .python-version
  - setup.py
  - setup.cfg
globs:
  - "**/*.py"
  - "**/pyproject.toml"
alwaysApply: false
tier: 1
---
# Python/uv Project Tooling

Load this skill when working in a Python project managed by `uv`. It provides project discovery, validation commands, coding standards, report templates, and property-based testing guidance.

## Project Discovery

Before writing or validating code, determine the project's source root:

1. Read `pyproject.toml` (or `setup.py`, `setup.cfg`) to find the package directory structure.
   - Look for `[tool.hatch.build.targets.wheel]`, `[tool.setuptools.packages.find]`, or `packages = [...]`.
   - Common patterns: `src/{package}/` (src layout), `{package}/` (flat layout), `app/` / `lib/` (framework-specific).
2. Use the discovered path as `{source_root}` in ALL lint, format, type-check, and test commands.
3. If `pyproject.toml` is missing or ambiguous, delegate to `@codebase-analyzer`.

**Example:** If `pyproject.toml` shows `packages = ["src/myapp"]`, then `{source_root}` = `src/myapp/`.

Store the discovered root in your working notes:
> **Source root: `[discovered path]`**

## Validation Commands

Run these commands using the discovered `{source_root}`:

```bash
# Lint
uv run ruff check {source_root}

# Format
uv run ruff format --check {source_root}

# Auto-fix lint
uv run ruff check --fix {source_root}

# Auto-fix format
uv run ruff format {source_root}

# Type check
uv run ty check {source_root}

# Tests
uv run pytest
```

**Always use `uv run`** — never run bare `python`, `pytest`, `ruff`, or `ty`.

## Package Management

```bash
uv add <package>              # Add a dependency
uv add --dev <package>        # Add a dev dependency
uv remove <package>           # Remove a dependency
uv sync                       # Install all deps from lockfile
uv lock                       # Update lockfile without installing
uv init                       # Scaffold a new project with pyproject.toml
```

**Lockfile rules:**
- Always commit BOTH `pyproject.toml` and `uv.lock` together
- NEVER edit `uv.lock` manually — it is machine-generated
- Run `uv sync` after pulling changes that modified `uv.lock`

**Virtual environments:**
- `uv` auto-creates `.venv/` on first run — do NOT create or activate it manually
- `uv run` handles the virtualenv transparently — no `source .venv/bin/activate` needed
- Do NOT add `.venv/` to version control

## Errand Runner Delegation

When delegating validation to `@errand-runner`:

```
@errand-runner
Run these commands and return structured results:
1. uv run ruff check {source_root}
2. uv run ruff format --check {source_root}
3. uv run pytest -v
4. uv run ty check {source_root}

Note: {source_root} is the project's source directory.
If unsure, first run: cat pyproject.toml
```

## Report Template Labels

Use these labels in validation report sections:

```
- **Lint (ruff check)**: PASS | FAIL ([error count])
- **Format (ruff format)**: PASS | FAIL ([error count])
- **Tests (pytest)**: PASS (X passed) | FAIL (X/Y passed, [failures])
- **Type check (ty)**: PASS | FAIL | SKIPPED
```

## Coding Standards

- **Type hints**: Use modern union syntax (`X | None`, not `Optional[X]`), lowercase generics (`list[str]`, not `List[str]`)
- **Line length**: 100 characters (check `pyproject.toml [tool.ruff]` for project override)
- **Data models**: Use Pydantic `BaseModel` with `Field(...)` descriptions for validated data; `@dataclass` for simple containers
- **Error handling**: Custom exception hierarchies, specific types, never bare `except`
- **Async**: Prefer `async/await` for I/O-bound operations; `asyncio.create_subprocess_exec` for subprocesses
- **Idiomatic Python**: List comprehensions, context managers, generators, dataclasses
- **Version detection**: Check `pyproject.toml` (requires-python), `.python-version`, or `setup.py`
- **Module placement**: New modules go in `{source_root}` (as discovered during project discovery)
- **Docstrings**: Google-style for all public functions and classes
- **Formatting**: Use ruff for linting and formatting

## Ruff Configuration

Ruff rules are configured in `pyproject.toml` under `[tool.ruff.lint]`:

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]   # enable rule sets
ignore = ["E501"]                       # suppress specific rules
per-file-ignores = {"tests/*" = ["S101"]}  # per-path overrides
```

**Common rule prefixes:**

| Prefix | Source | What it catches |
|--------|--------|-----------------|
| `E` | pycodestyle | Style errors (whitespace, indentation) |
| `W` | pycodestyle | Style warnings |
| `F` | Pyflakes | Unused imports, undefined names |
| `I` | isort | Import sorting |
| `UP` | pyupgrade | Deprecated syntax (`Optional`, `Union`, old-style strings) |
| `B` | flake8-bugbear | Common bugs and design problems |
| `S` | flake8-bandit | Security issues |
| `N` | pep8-naming | Naming conventions |

Always check the project's `pyproject.toml` for the active rule set before suppressing warnings.

## ty Configuration

`ty` is configured in `pyproject.toml` under `[tool.ty]`:

```toml
[tool.ty]
python-version = "3.12"        # target Python version
extend-exclude = ["migrations/", "generated/"]  # skip directories
```

If `ty` reports errors in generated or vendored code, add those paths to `extend-exclude` rather than suppressing individual diagnostics.

## Prohibitions

- Do NOT run Python commands without `uv run`
- Do NOT use `shell=True` in subprocess calls
- Do NOT hardcode paths — use `Path` from pathlib
- Do NOT use `Optional[X]` — use `X | None`
- Do NOT use `List[str]` — use `list[str]`
- Do NOT ignore ruff errors
- Do NOT leave `print()` or debug statements
- Do NOT edit `uv.lock` manually — always use `uv add`, `uv remove`, or `uv lock`
- Do NOT create or activate virtual environments manually — `uv run` handles this
- Do NOT run `pip install` — use `uv add` to manage dependencies

## Output Truncation Rules

When processing large command output from Python tools:

1. **pytest**: Report the summary line (e.g., `12 passed, 3 failed in 4.2s`), then list ONLY failed tests with error messages
2. **ruff**: Report total error count, then list each unique error code with count and one example location
3. **ty/mypy/pyright**: Report total error count, then list each unique error type with count and one example

## Property-Based Testing with Hypothesis

### Writing PBT Tasks (for spec writers)

When writing task sub-items that involve property-based tests:

```markdown
- [ ] Write property-based tests for [component]
  - **Property 1: [Name]** — *For any* [input class], [invariant]
  - Use Hypothesis `@given` with [strategy description]
  - **Validates: Requirement X.Y via Property 1**
```

### Reviewing PBT (for judges)

When reviewing property-based tests, verify:

1. A corresponding `@given` / Hypothesis test exists for each property listed in `design.md` § Correctness Properties
2. The Hypothesis strategies/generators match the input domain described by the property's quantifier
3. The test asserts the actual invariant from the property, not a weaker condition
4. Shrunk counterexamples (if any in test output) are traced back to the logic flaw

**PBT Issue Severity:**

| Severity | Issue |
|----------|-------|
| CRITICAL | Missing PBT for a Correctness Property that has a corresponding task sub-item |
| CRITICAL | PBT asserts a different invariant than the Correctness Property specifies |
| MODERATE | Strategy does not cover the full input domain described by the property quantifier |
| MODERATE | Test uses `@example` only without `@given` — example-based test disguised as PBT |

**PBT Assessment Template:**

```markdown
### PBT Assessment
| Property | Source | Test Location | Strategy Correct? | Invariant Correct? | Notes |
|----------|--------|---------------|-------------------|--------------------|-------|
| Property 1: [Name] | Correctness Properties | [file:line] | YES/NO | YES/NO | [details] |
```

**Counterexample Analysis (if PBT failures in test output):**
- **Property N**: Hypothesis found counterexample `[shrunk input]` — violates `[invariant]`
- **Fix guidance**: [Description of the logic flaw]

## Pre-commit Integration

If the project uses pre-commit:

```bash
# Install hooks
uv run pre-commit install

# Run on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff --all-files
```

Pre-commit hooks typically run ruff and formatting on commit. Validation via `uv run ruff` and `uv run ruff format` is still the primary method during development — pre-commit is a safety net.
