"""Installing catalog skills into a scope."""

import shutil
import tempfile
from pathlib import Path

import httpx

from skillctl.catalog import Catalog, CatalogSkill
from skillctl.scopes import Scope


class AlreadyInstalledError(Exception):
    """The scope already has an installation with that name."""


class DownloadError(Exception):
    """A file of the skill couldn't be downloaded; nothing was written."""


class Installer:
    """Facade over catalog and scope: one call installs a skill atomically and records it."""

    def __init__(self, catalog: Catalog) -> None:
        self._catalog = catalog

    def install(self, name: str, scope: Scope, *, force: bool = False) -> CatalogSkill:
        """Install the catalog skill `name` into `scope`.

        Files are staged in a hidden directory inside the scope and moved into place only after
        every download succeeded, so a failure never leaves a partial skill behind.

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
        """
        skill = self._catalog.find(name)
        target = scope.root / skill.name
        if _exists(target) and not force:
            raise AlreadyInstalledError(f"{skill.name} is already installed in {scope.root}")
        scope.lockfile.entries()  # fail on a malformed lockfile before touching any files
        scope.root.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{skill.name}-", dir=scope.root))
        try:
            self._download(skill, staging)
            _remove(target)
            staging.rename(target)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        where = self._catalog.where
        scope.lockfile.record(
            skill.name,
            {"repo": where.repo, "ref": where.ref, "path": skill.path, "tree_sha": skill.tree_sha},
        )
        return skill

    def _download(self, skill: CatalogSkill, into: Path) -> None:
        for relative in self._catalog.files(skill):
            try:
                content = self._catalog.read(skill, relative)
            except httpx.HTTPError as error:
                raise DownloadError(f"Could not download {skill.name}: {relative}") from error
            destination = into / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)


def _exists(path: Path) -> bool:
    return path.is_symlink() or path.exists()


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)
