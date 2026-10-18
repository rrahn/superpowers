# 02: Browse the catalog

**What to build:** `skillctl available` lists every catalog skill on the default catalog (`rrahn/superpowers@main`) as a rich table (name, collection, description), with `--collection`, `--search`, and `--json`. Skills come from one recursive git-trees call plus each `SKILL.md` frontmatter.

**Blocked by:** 01

**Status:** done

- [x] Only directories whose `SKILL.md` frontmatter name matches the directory name are listed
- [x] Filters by collection and case-insensitive search over name and description
- [x] `--json` emits a stable list of objects
- [x] Text and SVG snapshot of the table
- [x] `GitHubClient` tested at its seam with `httpx.MockTransport`
