# 0003: Read the catalog through the GitHub REST API

**Status:** accepted

`skillctl` must work from any directory, with or without a clone of the catalog repository.
It reads the catalog via the GitHub REST API: one recursive git-trees call lists every `SKILL.md`
and its tree hash; file contents come from `raw.githubusercontent.com`.

Unauthenticated calls are rate-limited (60/hour), so `GITHUB_TOKEN` / `GH_TOKEN` is sent when set.
All HTTP goes through one `GitHubClient` adapter; tests replace the transport, not our own classes.

Each command resolves the ref to a commit once (`/commits/{ref}`) and reads the tree and every
file at that commit, so a branch moving mid-install can't mix two commits. The commit is recorded
in the lockfile.

Considered: shelling out to `git clone --depth 1`. Rejected for listing (slow, needs git) but may
return for bulk sync of upstream sources.
