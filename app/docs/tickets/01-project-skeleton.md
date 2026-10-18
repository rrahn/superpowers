# 01: Project skeleton and quality gates

**What to build:** `uv run skillctl --version` prints the version from a uv project in `app/`. `just` recipes for setup, test, lint, format, typecheck, check, and install (as a uv tool). Pre-commit runs ruff format, ruff check, ty, and pytest on `app/` changes. GitHub Actions runs `just check` on PRs touching `app/`.

**Blocked by:** None (can start immediately)

**Status:** done

- [ ] `skillctl --version` and `skillctl --help` work via `uv run` and after `just install`
- [ ] Tests exercise the CLI seam through `create_app(deps)`
- [ ] `just check` is green locally and in CI; actions pinned to commit SHAs
- [ ] Pre-commit hooks installed without breaking commits in worktrees that lack the config
- [ ] Spec, glossary, ADRs, and tickets committed under `app/`
