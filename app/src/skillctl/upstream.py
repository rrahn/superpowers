"""Comparing catalog collections with their upstream sources."""

import os
import stat
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from hashlib import sha1
from pathlib import Path, PurePosixPath
from typing import Literal

from skillctl.github import GitHubClient, GitHubError
from skillctl.sources import GitHubUpstream, SourcesError, SourcesFile, Upstream

FileTree = dict[str, str]
"""File path (relative to the skill) → git identity `"<mode> <blob sha>"`."""

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
    """Group `(path, identity)` pairs under the deepest directory that holds a `SKILL.md`.

    Hidden files and directories are ignored on both sides of a comparison, and a `SKILL.md` at
    the root itself is not a skill.

    Args:
        files: File paths relative to a collection (or upstream path) with their identities.

    Returns:
        Skills keyed by their directory, each with its files relative to that directory.
    """
    visible = [
        (PurePosixPath(p), s)
        for p, s in files
        if not any(part.startswith(".") for part in PurePosixPath(p).parts)
    ]
    skills = {p.parent for p, _ in visible if p.name == "SKILL.md" and p.parent.parts}
    trees: SkillTrees = {str(skill): {} for skill in skills}
    for path, identity in visible:
        owner = next((d for d in path.parents if d in skills), None)
        if owner is not None:
            trees[str(owner)][path.relative_to(owner).as_posix()] = identity
    return trees


@dataclass(frozen=True)
class CollectionReport:
    """The outcome of checking one collection against its upstream."""

    collection: str
    status: Literal["checked", "unavailable", "skipped", "no-upstream"]
    upstream: str | None = None
    commit: str | None = None
    reason: str | None = None
    skills: tuple[SkillChange, ...] = ()


class WorkingTree:
    """Reads files of the catalog repository the way git sees them.

    Only tracked and untracked-but-not-ignored files count, and content is hashed through git's
    clean filters, so line-ending conversion and `.gitignore` don't show up as changes.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    def files(self, directory: Path) -> list[tuple[str, str]]:
        """List files under `directory` with their git identity.

        Args:
            directory: A directory inside the repository.

        Returns:
            `(path relative to directory, "<mode> <blob sha>")` pairs.

        Raises:
            SourcesError: git isn't available or the directory isn't in a git repository.
        """
        listed = self._git(
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            directory.relative_to(self._root).as_posix(),
        )
        paths = sorted({p for p in listed.split("\0") if p and os.path.lexists(self._root / p)})
        links = [p for p in paths if (self._root / p).is_symlink()]
        regular = [p for p in paths if p not in links]
        shas = self._git("hash-object", "--stdin-paths", stdin="\n".join(regular)).split()
        identities = {
            p: f"{_mode(self._root / p)} {sha}" for p, sha in zip(regular, shas, strict=True)
        }
        for p in links:
            identities[p] = f"120000 {git_blob_sha(os.readlink(self._root / p).encode())}"
        prefix = directory.relative_to(self._root).as_posix() + "/"
        return [(p.removeprefix(prefix), identities[p]) for p in paths]

    def _git(self, *args: str, stdin: str | None = None) -> str:
        # GIT_DIR & co. leak in from git hooks and would redirect git to another repository.
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        try:
            return subprocess.run(  # noqa: S603
                ["git", "-C", str(self._root), *args],  # noqa: S607
                input=stdin,
                capture_output=True,
                text=True,
                check=True,
                env=env,
            ).stdout
        except (OSError, subprocess.CalledProcessError) as error:
            raise SourcesError(f"git failed in {self._root}: {error}") from error


def _mode(path: Path) -> str:
    return "100755" if path.stat().st_mode & stat.S_IXUSR else "100644"


class UpstreamChecker:
    """Compares catalog collections in a working tree with their GitHub upstreams. Read-only."""

    def __init__(self, github: GitHubClient, sources: SourcesFile) -> None:
        self._github = github
        self._sources = sources
        self._tree = WorkingTree(sources.root)

    def check(self, only: str | None = None) -> list[CollectionReport]:
        """Check every collection, or just `only`.

        Args:
            only: A single collection to check.

        Returns:
            One report per collection, sorted by name; unreachable upstreams are reported, not
            raised.

        Raises:
            SourcesError: The sources file is invalid, `only` isn't declared in it, or git
                can't read the working tree.
        """
        collections = self._sources.load().collections
        if only is not None and only not in collections:
            raise SourcesError(f"No collection '{only}' in {self._sources.path}")
        names = [only] if only else sorted(collections)
        return [self._check(name, collections[name].upstream) for name in names]

    def _check(self, name: str, upstream: Upstream | None) -> CollectionReport:
        if upstream is None:
            return CollectionReport(name, "no-upstream")
        if not isinstance(upstream, GitHubUpstream):
            return CollectionReport(
                name, "skipped", str(upstream), reason="local upstreams are not compared yet"
            )
        try:
            commit = self._github.commit(upstream.github, upstream.ref)
            remote = self._remote(upstream, commit)
        except GitHubError as error:
            return CollectionReport(name, "unavailable", str(upstream), reason=str(error))
        local = group_by_skill(self._tree.files(self._sources.root / "skills" / name))
        changes = tuple(plan(local=local, upstream=remote))
        return CollectionReport(name, "checked", str(upstream), commit, skills=changes)

    def _remote(self, upstream: GitHubUpstream, commit: str) -> SkillTrees:
        prefix = f"{upstream.path}/" if upstream.path else ""
        entries = self._github.tree(upstream.github, commit)
        return group_by_skill(
            (e.path.removeprefix(prefix), f"{e.mode} {e.sha}")
            for e in entries
            if e.type == "blob" and e.path.startswith(prefix)
        )
