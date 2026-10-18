# Glossary

Domain language for `skillctl`. Use these terms in code, tests, tickets, and PRs.

## Installing skills (consumer side)

**Skill**: a directory containing a `SKILL.md` whose frontmatter `name` matches the directory name.
_Avoid_: plugin, prompt.

**Catalog**: the set of skills installable from the **catalog repository** at the configured ref
(default `rrahn/superpowers@main`; `main` is the source of truth, other refs are for testing).
_Avoid_: registry, store.

**Collection**: the first path segment under `skills/` in the catalog repository
(`ai2code`, `mattpocock`, `misc`, `nextflow`, `superpowers`). Groups skills by where they came from.

**Scope**: where a skill is installed for Copilot.
- **Global scope**: `~/.copilot/skills/` — available in every workspace.
- **Local scope**: `<repo root>/.github/skills/` — available only inside that repository.
_Avoid_: level, location.

**Installation**: a skill directory present in a scope.

**Managed**: an installation recorded in the scope's **lockfile**, i.e. installed by `skillctl` from the catalog.
**Unmanaged**: an installation `skillctl` did not install (hand-copied, symlinked, or from elsewhere).
_Avoid_: foreign, external, custom.

**Lockfile**: `.skillctl-lock.json` in the scope directory. Records, per managed skill, the catalog
repository, ref, commit, path, and tree hash it was installed from.

## Curating the collection (maintainer side)

**Upstream source**: where a collection's skills originally come from — a public GitHub repository
(e.g. `mattpocock/skills`) or a local path (internally maintained skills).
_Avoid_: origin (overloaded with the git remote), provider.

**Sources file**: the TOML file in the catalog repository declaring every upstream source.

**Provenance**: the record of which upstream source a single skill in the catalog was copied from,
written by `upstream import` as `[collections.<c>.skills.<skill>] local = "…"`. It overrides the
collection's upstream for that skill.

**Change set**: the difference between a skill in the catalog and its upstream source, as file-level
changes: **added**, **modified**, **deleted**. A skill whose upstream no longer exists is
**orphaned**; orphaned skills are never removed automatically. A skill whose upstream can't be
reached (private repository, missing local path) is **unavailable**; nothing is compared or changed.

**Sync**: materialising a change set into the catalog repository working tree. Only **pending**
skills (changed or new) are written; orphaned and unavailable skills are never touched.
