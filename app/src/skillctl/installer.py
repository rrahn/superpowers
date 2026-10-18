"""Installing catalog skills into a scope."""

import shutil
import tempfile
from pathlib import Path

import httpx

from skillctl.catalog import Catalog, CatalogSkill
from skillctl.scopes import LockEntry, Scope


class AlreadyInstalledError(Exception):
    """The scope already has an installation with that name."""


class DownloadError(Exception):
    """A file of the skill couldn't be downloaded or written; nothing was changed."""


class Installer:
    """Facade over catalog and scope: one call installs a skill atomically and records it."""

    def __init__(self, catalog: Catalog) -> None:
        self._catalog = catalog

    def install(self, name: str, scope: Scope, *, force: bool = False) -> CatalogSkill:
        """Install the catalog skill `name` into `scope`.

        Files are staged in a hidden directory inside the scope. Only after every download
        succeeded does the staged directory replace the target, and an existing installation is
        moved aside first so it can be restored if the swap fails.

        Args:
            name: Catalog skill name.
            scope: Where to install.
            force: Replace an existing installation (a symlink is removed, not its target).

        Returns:
            The installed catalog skill.

        Raises:
            SkillNotFoundError: The catalog has no such skill.
            AlreadyInstalledError: `name` exists in the scope and `force` is False.
            DownloadError: A file couldn't be downloaded.
            LockfileError: The scope's lockfile is malformed.
            httpx.HTTPError: GitHub couldn't be reached.
        """
        skill = self._catalog.find(name)
        target = scope.root / skill.name
        if _exists(target) and not force:
            raise AlreadyInstalledError(f"{skill.name} is already installed in {scope.root}")
        scope.lockfile.entries()  # fail on a malformed lockfile before touching any files
        scope.root.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{skill.name}-", dir=scope.root))
        try:
            staging.chmod(0o755)
            self._download(skill, staging)
            _swap_into_place(staging, target)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        where = self._catalog.where
        scope.lockfile.record(
            skill.name,
            LockEntry(where.repo, where.ref, self._catalog.commit, skill.path, skill.tree_sha),
        )
        return skill

    def _download(self, skill: CatalogSkill, into: Path) -> None:
        for file in self._catalog.files(skill):
            destination = (into / file.path).resolve()
            if file.symlink or not destination.is_relative_to(into.resolve()):
                raise DownloadError(f"Refusing to install {skill.name}: unsafe entry {file.path}")
            try:
                content = self._catalog.read(skill, file)
            except httpx.HTTPError as error:
                raise DownloadError(f"Could not download {skill.name}: {file.path}") from error
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            destination.chmod(0o755 if file.executable else 0o644)


def _swap_into_place(staging: Path, target: Path) -> None:
    backup = target.with_name(f".{target.name}.previous")
    _remove(backup)
    had_previous = _exists(target)
    if had_previous:
        target.rename(backup)
    try:
        staging.rename(target)
    except OSError:
        if had_previous:
            backup.rename(target)
        raise
    _remove(backup)


def _exists(path: Path) -> bool:
    return path.is_symlink() or path.exists()


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)
