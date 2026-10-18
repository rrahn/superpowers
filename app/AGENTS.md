# skillctl — agent notes

Python CLI that manages Copilot skills from this repository. Read [GLOSSARY.md](GLOSSARY.md) first.

## Commands (run from `app/`)

- `just setup` — sync the env and install pre-commit hooks
- `just test` / `just lint` / `just typecheck` / `just check` (everything CI runs)
- `just snapshots` — regenerate syrupy snapshots after an intended UI change
- `just install` — install `skillctl` as a uv tool on this machine

Always use `uv run`; never bare `python`/`pytest`/`ruff`.

## Agent skills

### Issue tracker

Local markdown: spec in `docs/spec.md`, one ticket per file in `docs/tickets/NN-slug.md`.

### Domain docs

Single-context: `GLOSSARY.md` here and ADRs in `docs/adr/`.

## Standards

- Test at the agreed seams only (see spec "Testing Decisions"): the CLI via `create_app(deps)`,
  and `GitHubClient` via `httpx.MockTransport`. Don't mock our own classes.
- Domain logic stays out of `cli.py`; it wires dependencies and renders `views`.
- Google-style docstrings on public classes/functions; `X | None`, `list[str]`.
