"""Scopes: where Copilot reads installed skills from, and what is installed there."""

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

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


@dataclass(frozen=True)
class Scope:
    """One install location with its lockfile."""

    name: ScopeName
    root: Path

    def installations(self) -> list[Installation]:
        """List skill directories in this scope.

        Returns:
            Every entry holding a `SKILL.md`, plus symlinks (even dangling), sorted by name.
        """
        if not self.root.is_dir():
            return []
        managed = self._locked_names()
        found = [
            Installation(
                name=entry.name,
                scope=self.name,
                managed=entry.name in managed,
                link=entry.readlink() if entry.is_symlink() else None,
            )
            for entry in self.root.iterdir()
            if not entry.name.startswith(".")
            and (entry.is_symlink() or (entry / "SKILL.md").is_file())
        ]
        return sorted(found, key=lambda i: i.name)

    def _locked_names(self) -> set[str]:
        lockfile = self.root / LOCKFILE
        if not lockfile.is_file():
            return set()
        return set(json.loads(lockfile.read_text()).get("skills", {}))


class NotInRepositoryError(Exception):
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
            raise NotInRepositoryError(f"{self.cwd} is not inside a git repository")
        candidates = [self.global_scope, local]
        return [s for s in candidates if s and (name is None or s.name is name)]


def _repository_root(start: Path) -> Path | None:
    return next((d for d in (start, *start.parents) if (d / ".git").exists()), None)
