"""Applying an upstream check's change set to the catalog working tree."""

import os
import shutil
from dataclasses import replace
from pathlib import Path

from skillctl.errors import SkillctlError
from skillctl.fsops import replacing
from skillctl.github import GitHubClient, GitHubError
from skillctl.sources import SourcesFile
from skillctl.upstream import CollectionReport, GitHubOrigin, LocalOrigin, SkillChange

PENDING = ("changed", "new")


class SyncError(SkillctlError):
    """A change set can't be planned or applied; the affected skill is left untouched."""


def plan_sync(reports: list[CollectionReport], skills: list[str]) -> list[CollectionReport]:
    """Narrow check reports to the skills a sync would write.

    Orphaned, unavailable, and unchanged skills are never part of the plan.

    Args:
        reports: Output of `UpstreamChecker.check`.
        skills: Skill paths to limit the plan to; all pending skills when empty.

    Returns:
        Reports holding only pending skills; collections without any are dropped.

    Raises:
        SyncError: A named skill isn't in any report, or has nothing to sync.
    """
    status = {c.skill: c.status for r in reports for c in r.skills}
    unknown = sorted(set(skills) - status.keys())
    if unknown:
        raise SyncError(f"No such skill in the checked collections: {', '.join(unknown)}")
    idle = sorted(s for s in skills if status[s] not in PENDING)
    if idle:
        raise SyncError("; ".join(f"{s} is {status[s]}, nothing to sync" for s in idle))
    planned = []
    for report in reports:
        pending = tuple(
            c
            for c in report.skills
            if c.status in PENDING and c.origin and (not skills or c.skill in skills)
        )
        if pending:
            planned.append(replace(report, skills=pending))
    return planned


class Synchronizer:
    """Writes a planned change set into `skills/`, one skill directory at a time."""

    def __init__(self, github: GitHubClient, sources: SourcesFile) -> None:
        self._github = github
        self._root = sources.root / "skills"

    def apply(self, plan: list[CollectionReport]) -> int:
        """Apply every skill change in `plan`.

        Each skill is rebuilt in a staging directory from its current content plus the change
        set and swapped in atomically, so a failure leaves that skill exactly as it was. Files
        the change set doesn't mention (including hidden ones) are kept.

        Args:
            plan: Output of `plan_sync`.

        Returns:
            How many skills were written.

        Raises:
            SyncError: A file couldn't be fetched or is unsafe to write; the message says how
                many skills were already written.
        """
        written = 0
        for report in plan:
            for change in report.skills:
                try:
                    self._apply(self._root / report.collection / change.skill, change)
                except (SyncError, OSError) as error:
                    raise SyncError(
                        f"{error} ({written} skill(s) synced before the failure)"
                    ) from error
                written += 1
        return written

    def _apply(self, target: Path, change: SkillChange) -> None:
        with replacing(target) as staging:
            if target.is_dir() and not target.is_symlink():
                shutil.copytree(target, staging, symlinks=True, dirs_exist_ok=True)
            for relative in change.deleted:
                _inside(staging, relative).unlink(missing_ok=True)
                _prune_empty_parents(staging, staging / relative)
            for relative in (*change.added, *change.modified):
                self._write(_inside(staging, relative), change, relative)

    def _write(self, destination: Path, change: SkillChange, relative: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.unlink(missing_ok=True)
        origin = change.origin
        if isinstance(origin, LocalOrigin):
            source = origin.directory / relative
            if source.is_symlink():
                link = os.readlink(source)
                if not (source.parent / link).resolve().is_relative_to(origin.directory.resolve()):
                    raise SyncError(f"{change.skill}: {relative} points outside the skill")
                os.symlink(link, destination)
            else:
                shutil.copyfile(source, destination)
                destination.chmod(0o755 if os.access(source, os.X_OK) else 0o644)
        elif isinstance(origin, GitHubOrigin):
            mode = origin.files.get(relative, "100644").split()[0]
            if mode == "120000":
                raise SyncError(f"{change.skill}: symlink {relative} upstream is not supported")
            try:
                content = self._github.read_bytes(
                    origin.repo, origin.commit, f"{origin.directory}/{relative}"
                )
            except GitHubError as error:
                raise SyncError(f"{change.skill} left unchanged: {error}") from error
            destination.write_bytes(content)
            destination.chmod(0o755 if mode == "100755" else 0o644)


def _inside(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise SyncError(f"Refusing to write outside the skill: {relative}")
    return root / relative


def _prune_empty_parents(root: Path, removed: Path) -> None:
    for parent in removed.parents:
        if parent == root or not parent.is_dir() or any(parent.iterdir()):
            return
        parent.rmdir()
