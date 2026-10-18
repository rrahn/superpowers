"""Comparing catalog collections with their upstream sources."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from hashlib import sha1
from pathlib import PurePosixPath
from typing import Literal

from skillctl.github import GitHubClient, GitHubError
from skillctl.sources import GitHubUpstream, SourcesError, SourcesFile, Upstream

FileTree = dict[str, str]
"""File path (relative to the skill) → git blob SHA."""

SkillTrees = dict[str, FileTree]
"""Skill path (relative to the collection / upstream path) → its files."""

Status = Literal["unchanged", "changed", "new", "orphaned"]


@dataclass(frozen=True)
class SkillChange:
    """How one skill in a collection differs from its upstream."""

    skill: str
    status: Status
    added: tuple[str, ...] = field(default=())
    modified: tuple[str, ...] = field(default=())
    deleted: tuple[str, ...] = field(default=())


def plan(*, local: SkillTrees, upstream: SkillTrees) -> list[SkillChange]:
    """Compute the change set that would bring `local` in line with `upstream`.

    Skills missing upstream are orphaned and never scheduled for deletion.

    Args:
        local: Skills in the catalog working tree.
        upstream: Skills in the upstream source.

    Returns:
        One change per skill on either side, sorted by skill path.
    """
    return [_compare(s, local.get(s), upstream.get(s)) for s in sorted(local.keys() | upstream)]


def _compare(skill: str, local: FileTree | None, upstream: FileTree | None) -> SkillChange:
    if upstream is None:
        return SkillChange(skill, "orphaned")
    if local is None:
        return SkillChange(skill, "new", added=tuple(sorted(upstream)))
    added = tuple(sorted(upstream.keys() - local.keys()))
    deleted = tuple(sorted(local.keys() - upstream.keys()))
    modified = tuple(sorted(p for p in local.keys() & upstream.keys() if local[p] != upstream[p]))
    status: Status = "changed" if added or deleted or modified else "unchanged"
    return SkillChange(skill, status, added, modified, deleted)


def git_blob_sha(content: bytes) -> str:
    """Hash file content the way git does, so local files compare with GitHub tree entries."""
    return sha1(b"blob %d\0" % len(content) + content, usedforsecurity=False).hexdigest()


def group_by_skill(files: Iterable[tuple[str, str]]) -> SkillTrees:
    """Group `(path, sha)` pairs under the deepest directory that holds a `SKILL.md`.

    Hidden files and directories are ignored on both sides of a comparison, and a `SKILL.md` at
    the root itself is not a skill.

    Args:
        files: File paths relative to a collection (or upstream path) with their blob SHAs.

    Returns:
        Skills keyed by their directory, each with its files relative to that directory.
    """
    visible = [
        (p, s) for p, s in files if not any(part.startswith(".") for part in PurePosixPath(p).parts)
    ]
    skills = {
        str(PurePosixPath(p).parent)
        for p, _ in visible
        if PurePosixPath(p).name == "SKILL.md" and "/" in p
    }
    trees: SkillTrees = {skill: {} for skill in skills}
    for path, sha in visible:
        owner = max((s for s in skills if path.startswith(f"{s}/")), key=len, default=None)
        if owner is not None:
            trees[owner][path.removeprefix(f"{owner}/")] = sha
    return trees


@dataclass(frozen=True)
class CollectionReport:
    """The outcome of checking one collection against its upstream."""

    collection: str
    status: Literal["checked", "unavailable", "no upstream"]
    upstream: str | None = None
    reason: str | None = None
    skills: tuple[SkillChange, ...] = ()


class UpstreamChecker:
    """Compares catalog collections in a working tree with their GitHub upstreams. Read-only."""

    def __init__(self, github: GitHubClient, sources: SourcesFile) -> None:
        self._github = github
        self._sources = sources

    def check(self, only: str | None = None) -> list[CollectionReport]:
        """Check every collection, or just `only`.

        Args:
            only: A single collection to check.

        Returns:
            One report per collection, sorted by name; unreachable upstreams are reported, not
            raised.

        Raises:
            SourcesError: The sources file is invalid or `only` isn't declared in it.
        """
        collections = self._sources.load().collections
        if only is not None and only not in collections:
            raise SourcesError(f"No collection '{only}' in {self._sources.path}")
        names = [only] if only else sorted(collections)
        return [self._check(name, collections[name].upstream) for name in names]

    def _check(self, name: str, upstream: Upstream | None) -> CollectionReport:
        if upstream is None:
            return CollectionReport(name, "no upstream")
        if not isinstance(upstream, GitHubUpstream):
            return CollectionReport(
                name, "unavailable", str(upstream), "local upstreams are not compared yet"
            )
        try:
            remote = self._remote(upstream)
        except GitHubError as error:
            return CollectionReport(name, "unavailable", str(upstream), str(error))
        local = group_by_skill(self._local_files(name))
        return CollectionReport(
            name, "checked", str(upstream), skills=tuple(plan(local=local, upstream=remote))
        )

    def _remote(self, upstream: GitHubUpstream) -> SkillTrees:
        commit = self._github.commit(upstream.github, upstream.ref)
        prefix = f"{upstream.path}/" if upstream.path else ""
        entries = self._github.tree(upstream.github, commit)
        return group_by_skill(
            (e.path.removeprefix(prefix), e.sha)
            for e in entries
            if e.type == "blob" and e.path.startswith(prefix)
        )

    def _local_files(self, collection: str) -> Iterator[tuple[str, str]]:
        root = self._sources.root / "skills" / collection
        for path in sorted(root.rglob("*")):
            if path.is_file():
                yield path.relative_to(root).as_posix(), git_blob_sha(path.read_bytes())
