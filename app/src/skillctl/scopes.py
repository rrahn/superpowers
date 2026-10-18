"""Scopes: where Copilot reads installed skills from, and what is installed there."""

import json
import tempfile
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

from skillctl.errors import SkillctlError

LOCKFILE = ".skillctl-lock.json"


class ScopeName(StrEnum):
    """The install locations Copilot reads (ADR-0001)."""

    GLOBAL = "global"
    LOCAL = "local"


@dataclass(frozen=True)
class Installation:
    """A skill directory present in a scope."""

    name: str
    scope: ScopeName
    managed: bool
    link: Path | None


class LockfileError(SkillctlError):
    """A lockfile exists but can't be read."""


@dataclass(frozen=True)
class LockEntry:
    """Where a managed installation came from (ADR-0002)."""

    repo: str
    ref: str
    commit: str
    path: str
    tree_sha: str


@dataclass(frozen=True)
class Lockfile:
    """`.skillctl-lock.json`: the managed installations of one scope (ADR-0002)."""

    path: Path

    def entries(self) -> dict[str, dict[str, object]]:
        """Read the recorded installations.

        Returns:
            Entries keyed by skill name; empty when the lockfile doesn't exist.

        Raises:
            LockfileError: The file isn't a JSON object with a `skills` object.
        """
        if not self.path.is_file():
            return {}
        try:
            skills = json.loads(self.path.read_text()).get("skills", {})
        except (ValueError, AttributeError) as error:
            raise LockfileError(f"{self.path} is not a valid lockfile") from error
        if not isinstance(skills, dict):
            raise LockfileError(f"{self.path} is not a valid lockfile")
        return skills

    def record(self, name: str, entry: LockEntry) -> None:
        """Add or replace the entry for `name`, writing the file atomically.

        Args:
            name: Skill name.
            entry: Where the installation came from.

        Raises:
            LockfileError: The existing lockfile is malformed.
        """
        skills = {**self.entries(), name: asdict(entry)}
        content = json.dumps({"version": 1, "skills": skills}, indent=2, sort_keys=True)
        with tempfile.NamedTemporaryFile(
            "w", dir=self.path.parent, prefix=".lock-", delete=False
        ) as staged:
            staged.write(content)
        Path(staged.name).chmod(0o644)
        Path(staged.name).replace(self.path)


@dataclass(frozen=True)
class Scope:
    """One install location with its lockfile."""

    name: ScopeName
    root: Path

    @property
    def lockfile(self) -> Lockfile:
        """The lockfile recording this scope's managed installations."""
        return Lockfile(self.root / LOCKFILE)

    def installations(self) -> list[Installation]:
        """List skill directories in this scope.

        Returns:
            Every entry holding a `SKILL.md`, plus symlinks (even dangling), sorted by name.

        Raises:
            LockfileError: The scope's lockfile is malformed.
        """
        if not self.root.is_dir():
            return []
        managed = self.lockfile.entries().keys()
        found = [
            Installation(
                name=entry.name,
                scope=self.name,
                managed=entry.name in managed,
                link=entry.resolve() if entry.is_symlink() else None,
            )
            for entry in self.root.iterdir()
            if not entry.name.startswith(".")
            and (entry.is_symlink() or (entry / "SKILL.md").is_file())
        ]
        return sorted(found, key=lambda i: i.name)


class NotInRepositoryError(SkillctlError):
    """The local scope was requested outside a git repository."""


@dataclass(frozen=True)
class Scopes:
    """Resolves the scopes available from a home directory and a working directory."""

    home: Path
    cwd: Path

    @property
    def global_scope(self) -> Scope:
        """The scope every workspace sees: `~/.copilot/skills`."""
        return Scope(ScopeName.GLOBAL, self.home / ".copilot" / "skills")

    @property
    def local_scope(self) -> Scope | None:
        """The repository scope `<repo>/.github/skills`, or None outside a git repository."""
        repo = _repository_root(self.cwd)
        return Scope(ScopeName.LOCAL, repo / ".github" / "skills") if repo else None

    def select(self, name: ScopeName | None) -> list[Scope]:
        """Pick scopes to act on.

        Args:
            name: One scope, or None for every available scope.

        Returns:
            The selected scopes, global first.

        Raises:
            NotInRepositoryError: The local scope was asked for outside a git repository.
        """
        local = self.local_scope
        if name is ScopeName.LOCAL and local is None:
            raise NotInRepositoryError(
                f"{self.cwd} is not inside a git repository. Use --scope global or run inside one."
            )
        candidates = [self.global_scope, local]
        return [s for s in candidates if s and (name is None or s.name is name)]

    def get(self, name: ScopeName) -> Scope:
        """Resolve exactly one scope.

        Args:
            name: The scope to resolve.

        Returns:
            The scope.

        Raises:
            NotInRepositoryError: `name` is local and cwd isn't inside a git repository.
        """
        (scope,) = self.select(name)
        return scope


def _repository_root(start: Path) -> Path | None:
    return next((d for d in (start, *start.parents) if (d / ".git").exists()), None)
