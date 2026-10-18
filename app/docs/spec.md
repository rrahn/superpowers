# Spec: `skillctl` — manage Copilot skills from this repository

Status: ready-for-agent · Tickets: [tickets/](tickets/) · Vocabulary: [GLOSSARY.md](../GLOSSARY.md)

## Problem Statement

This repository curates skills from several upstream sources (ai2code, mattpocock, superpowers,
internal ones). Getting one into Copilot today means hand-symlinking or copying directories into
`~/.copilot/skills/` or a repo's `.github/skills/`. There's no way to see what's available on `main`,
what's installed where, which installations came from here, or whether the curated copies have
drifted from their upstream sources.

## Solution

A Python CLI, `skillctl`, in two epics:

- **Epic A — Installer.** See the catalog on `main`, see installations per scope with
  managed/unmanaged status, install a skill globally or locally.
- **Epic B — Curation.** Declare upstream sources in a sources file, check the catalog for upstream
  changes as a dry-run change set, import internally maintained skills from a local path, and sync
  change sets into the working tree.

## User Stories

### Epic A — Installer

1. As a skill user, I want to list every skill in the catalog with its collection and description, so that I can choose what to install.
2. As a skill user, I want to filter the catalog by collection or by a search term, so that a long list stays scannable.
3. As a skill user, I want the catalog to come from the catalog repository's `main` branch, so that I always see what's actually published.
4. As a skill user, I want to point `skillctl` at a different catalog repository or ref, so that I can test a branch or a fork.
5. As a skill user, I want `skillctl` to use my `GITHUB_TOKEN`/`GH_TOKEN` when set, so that I don't hit anonymous rate limits.
6. As a skill user, I want a clear error when GitHub is unreachable or rate-limits me, so that I know what to do next.
7. As a skill user, I want to list skills installed in the global scope, so that I know what every workspace sees.
8. As a skill user inside a git repository, I want to also see skills installed in the local scope, so that I know what this project adds.
9. As a skill user, I want each installation marked managed or unmanaged, so that I know which ones `skillctl` owns.
10. As a skill user, I want to see where a symlinked installation points, so that I recognise hand-made links.
11. As a skill user, I want to see whether an unmanaged installation's name exists in the catalog, so that I can spot candidates to manage.
12. As a skill user, I want to install a catalog skill into the global scope, so that it's available everywhere.
13. As a skill user inside a git repository, I want to install a catalog skill into the local scope (`.github/skills/`), so that the whole team gets it via the repo.
14. As a skill user, I want installing outside a git repository with local scope to fail clearly, so that I don't create stray directories.
15. As a skill user, I want install to refuse to overwrite an existing installation unless I pass `--force`, so that I never lose local edits.
16. As a skill user, I want a clear error with suggestions when the skill name isn't in the catalog, so that typos are cheap.
17. As a skill user, I want install to copy every file of the skill (references, scripts), so that the skill works offline.
18. As a skill user, I want installs to be atomic, so that a network failure never leaves a half-written skill.
19. As a skill user, I want output as readable rich tables, so that the terminal view is pleasant.
20. As a skill user, I want `--json` output on list commands, so that I can script around `skillctl`.

### Epic B — Curation

21. As a maintainer, I want to declare upstream sources (GitHub repo + path + ref, or local path) per collection in a sources file, so that provenance is explicit and versioned.
22. As a maintainer, I want to list configured upstream sources in a table, so that I can review them.
23. As a maintainer, I want to add a public GitHub upstream source interactively or with flags, so that onboarding a new collection is quick.
24. As a maintainer, I want adding a source to validate the repo/ref/path exists, so that typos fail early.
25. As a maintainer, I want to import a skill from a local path into a collection, so that it gets recorded provenance.
26. As a maintainer, I want to check every catalog skill with provenance against its upstream source, so that I see what changed upstream.
27. As a maintainer, I want the check to show, per skill, added / modified / deleted files and brand-new upstream skills, so that I know exactly what a sync would do.
28. As a maintainer, I want skills whose upstream disappeared shown as orphaned and never removed, so that curated skills aren't lost.
29. As a maintainer, I want unreachable upstreams (private repo, missing local path) shown as unavailable rather than failing the whole check, so that one bad source doesn't block the rest.
30. As a maintainer, I want to sync the change set into the working tree (add new skills, update files, delete files removed upstream), so that updating is one command.
31. As a maintainer, I want sync to ask for confirmation and support `--dry-run` and selecting skills, so that I stay in control.
32. As a maintainer, I want sync to leave changes uncommitted, so that I review them in a normal PR.

## Implementation Decisions

- **Package layout.** `app/` holds a uv project (`pyproject.toml`, `uv.lock`), `src/skillctl/`, `tests/`,
  `justfile`. Python ≥ 3.12. Dependencies: typer, rich, httpx, pydantic, pyyaml. Dev: pytest,
  syrupy, ruff, ty, pre-commit.
- **Commands** (typer):
  - `skillctl available [--collection C] [--search Q] [--json]` — catalog view.
  - `skillctl installed [--scope global|local] [--json]` — installations view (all scopes when omitted).
  - `skillctl install NAME [--scope global|local] [--force]`.
  - `skillctl sources list | add` — upstream sources (Epic B).
  - `skillctl upstream check | sync | import` — curation (Epic B).
  - Global options: `--repo OWNER/NAME`, `--ref REF` (env `SKILLCTL_REPO`, `SKILLCTL_REF`).
- **Modules** (deep modules behind small interfaces; patterns named where they earn their keep):
  - `Catalog` — `skills() -> list[CatalogSkill]`, `files(skill)`. Backed by a `GitHubClient`
    **adapter**, the only thing that talks HTTP. Its seam is real because the HTTP transport varies
    (real network vs. `httpx.MockTransport`); Epic B reuses `GitHubClient` for GitHub upstreams.
  - `Scope` — one install location (`name`, `root`, `lockfile`, `installations()`). Global and
    local differ only in their root, so they are one class, not a strategy hierarchy, until a
    second harness gives the variation a real seam. `Scopes` resolves the available scopes from
    home and cwd (repo root = nearest ancestor with `.git`).
  - `Lockfile` — load/record/entries; owned by a scope.
  - `Installer` — **facade** the CLI calls: resolves the skill in the catalog, stages files in a temp
    dir, atomically moves them into the scope, records the lockfile entry.
  - `views` — pure functions turning domain objects into rich renderables; the CLI only wires.
  - Epic B: `SourcesFile` (TOML, pydantic-validated), `UpstreamSource` adapters (`GitHubSource`,
    `LocalSource`) behind one interface, `ChangeSetPlanner` (pure: two file trees → change set),
    `Synchronizer` (applies a change set; **command** objects per file change so dry-run and apply
    share one plan).
- **Composition root.** `create_app(deps)` builds the typer app from a `Dependencies` object
  (catalog factory, home dir, cwd, console). `main()` wires real dependencies; tests wire fakes.
  No singletons, no module-level globals.
- **Skill discovery.** A catalog skill is any `skills/**/<name>/SKILL.md` whose frontmatter `name`
  equals `<name>`. Mismatches are skipped (e.g. the stray `skills/SKILL.md`).
- **Scopes.** See ADR-0001. Local scope root = nearest ancestor of cwd containing `.git` (dir or file) + `/.github/skills`.
- **Managed.** See ADR-0002.
- **Catalog transport.** See ADR-0003.
- **Sources file** (Epic B): `skills/sources.toml` at the catalog repository root; provenance per
  imported skill lives in the same file so a single review shows both.

## Testing Decisions

- Good tests exercise behaviour through the public interface and assert against literal, independently
  known values; no mocks of our own classes.
- **Seam 1 — the CLI** (primary). Tests invoke the typer app via `CliRunner` built with
  `create_app(deps)`, using a temp home dir, a temp git repo as cwd, and a catalog served from
  in-memory fixtures. Covers every user story.
- **Seam 2 — `GitHubClient`**. Tested with `httpx.MockTransport` returning recorded GitHub API JSON:
  request shape, auth header, error mapping (404, 403 rate limit, network error).
- **Snapshots.** CLI table output is snapshot-tested with syrupy as plain text *and* as SVG
  (rich's `export_svg`). SVG snapshots render in GitHub PR diffs so reviewers see the terminal UI change.
- Pre-commit runs ruff format/fix, ty, and pytest; CI runs the non-mutating equivalents via `just check`.
- `.python-version` pins 3.12, the lowest supported version, so local and CI test the floor.

## Out of Scope

- Harnesses other than Copilot (Claude, Codex locations) — ADR-0001.
- Uninstall, adopt-unmanaged, and update of installed skills (natural follow-ups once Epic B's change
  sets exist).
- Non-GitHub hosts for upstream sources.
- Committing or opening PRs from `sync`.

## Further Notes

- Interpretation of "remove old skill" in sync: files deleted upstream are deleted locally; a whole skill
  deleted upstream is reported **orphaned** and kept.
- Tracker: local markdown tickets in [tickets/](tickets/) so the plan is reviewed in the same PR as code.
