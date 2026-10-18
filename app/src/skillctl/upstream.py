"""Comparing catalog collections with their upstream sources."""

import os
import stat
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from hashlib import sha1
from pathlib import Path, PurePosixPath
from typing import Literal

from skillctl.errors import SkillctlError
from skillctl.fsops import is_ignored
from skillctl.github import GitHubClient, GitHubError
from skillctl.sources import Collection, GitHubUpstream, LocalUpstream, SourcesError, SourcesFile

FileTree = dict[str, str]
"""File path (relative to the skill) → git identity `"<mode> <blob sha>"`."""

SkillTrees = dict[str, FileTree]
"""Skill path (relative to the collection / upstream path) → its files."""

Status = Literal["unchanged", "changed", "new", "orphaned", "unavailable"]


@dataclass(frozen=True)
class SkillChange:
    """How one skill in a collection differs from its upstream."""

    skill: str
    status: Status
    added: tuple[str, ...] = field(default=())
    modified: tuple[str, ...] = field(default=())
    deleted: tuple[str, ...] = field(default=())
    reason: str | None = None


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

    Hidden files and directories and `__pycache__` are ignored on both sides of a comparison,
    and a `SKILL.md` at the root itself is not a skill.

    Args:
        files: File paths relative to a collection (or upstream path) with their identities.

    Returns:
        Skills keyed by their directory, each with its files relative to that directory.
    """
    visible = [(PurePosixPath(p), s) for p, s in files if _visible(p)]
    skills = {p.parent for p, _ in visible if p.name == "SKILL.md" and p.parent.parts}
    trees: SkillTrees = {str(skill): {} for skill in skills}
    for path, identity in visible:
        owner = next((d for d in path.parents if d in skills), None)
        if owner is not None:
            trees[str(owner)][path.relative_to(owner).as_posix()] = identity
    return trees


def _visible(path: str) -> bool:
    return not any(is_ignored(part) for part in PurePosixPath(path).parts)


def directory_files(directory: Path) -> list[tuple[str, str]]:
    """List files under a directory outside the catalog repository with their git identity.

    Args:
        directory: Any directory, e.g. the origin of an imported skill.

    Returns:
        `(path relative to directory, "<mode> <blob sha>")` pairs, symlinks not followed.
    """
    found = []
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink():
            found.append((relative, f"120000 {git_blob_sha(os.readlink(path).encode())}"))
        elif path.is_file():
            found.append((relative, f"{_mode(path)} {git_blob_sha(path.read_bytes())}"))
    return found


@dataclass(frozen=True)
class CollectionReport:
    """The outcome of checking one collection against its upstream."""

    collection: str
    status: Literal["checked", "unavailable", "no-upstream"]
    upstream: str | None = None
    commit: str | None = None
    reason: str | None = None
    skills: tuple[SkillChange, ...] = ()


class OriginMissingError(SkillctlError):
    """A local upstream directory doesn't exist on this machine."""


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
    """Compares catalog collections and imported skills with where they came from. Read-only."""

    def __init__(self, github: GitHubClient, sources: SourcesFile, home: Path) -> None:
        self._github = github
        self._sources = sources
        self._home = home
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
        return [self._check(name, collections[name]) for name in names]

    def _check(self, name: str, collection: Collection) -> CollectionReport:
        imported = tuple(
            self._compare_with_origin(name, skill, origin)
            for skill, origin in sorted(collection.skills.items())
        )
        upstream = collection.upstream
        if upstream is None:
            if not imported:
                return CollectionReport(name, "no-upstream")
            return CollectionReport(name, "checked", skills=imported)
        commit = None
        try:
            if isinstance(upstream, GitHubUpstream):
                commit = self._github.commit(upstream.github, upstream.ref)
                remote = self._github_skills(upstream, commit)
            else:
                remote = group_by_skill(directory_files(self._existing(upstream)))
        except (GitHubError, OriginMissingError) as error:
            return CollectionReport(
                name, "unavailable", str(upstream), reason=str(error), skills=imported
            )
        local = group_by_skill(self._tree.files(self._sources.root / "skills" / name))
        for skill in collection.skills:
            local.pop(skill, None)
            remote.pop(skill, None)
        changes = sorted((*plan(local=local, upstream=remote), *imported), key=lambda c: c.skill)
        return CollectionReport(name, "checked", str(upstream), commit, skills=tuple(changes))

    def _compare_with_origin(self, name: str, skill: str, origin: LocalUpstream) -> SkillChange:
        try:
            source = self._existing(origin)
        except OriginMissingError as error:
            return SkillChange(skill, "unavailable", reason=str(error))
        # Both sides raw: import and sync copy origin bytes verbatim, so git's eol filters
        # must not make a fresh copy look modified.
        here = directory_files(self._sources.root / "skills" / name / skill)
        there = directory_files(source)
        local = {skill: {p: i for p, i in here if _visible(p)}}
        upstream = {skill: {p: i for p, i in there if _visible(p)}}
        return plan(local=local, upstream=upstream)[0]

    def _existing(self, origin: LocalUpstream) -> Path:
        directory = origin.resolve(self._home)
        if not directory.is_dir():
            raise OriginMissingError(f"{origin} not found on this machine")
        return directory

    def _github_skills(self, upstream: GitHubUpstream, commit: str) -> SkillTrees:
        prefix = f"{upstream.path}/" if upstream.path else ""
        entries = self._github.tree(upstream.github, commit)
        return group_by_skill(
            (e.path.removeprefix(prefix), f"{e.mode} {e.sha}")
            for e in entries
            if e.type == "blob" and e.path.startswith(prefix)
        )
