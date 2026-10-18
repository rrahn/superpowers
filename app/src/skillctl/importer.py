"""Importing internally maintained skills from a local path into a collection."""

import shutil
from pathlib import Path

from skillctl.catalog import skill_name
from skillctl.errors import SkillctlError
from skillctl.fsops import exists, is_ignored, replacing
from skillctl.sources import LocalUpstream, SourcesFile, check_collection_name


class SkillImportError(SkillctlError):
    """A skill can't be imported."""


class LocalImporter:
    """Copies a skill from a local directory into the catalog and records where it came from."""

    def __init__(self, sources: SourcesFile, home: Path) -> None:
        self._sources = sources
        self._home = home

    def import_skill(self, source: Path, collection: str, *, force: bool = False) -> Path:
        """Import the skill at `source` into `skills/<collection>/<name>/`.

        Hidden files and `__pycache__` are skipped. Files are copied and provenance is recorded
        together: if either fails, the catalog and the sources file are left as they were.

        Args:
            source: Directory holding the skill's `SKILL.md`, outside the catalog repository.
            collection: Target collection; declared in the sources file when missing.
            force: Replace an existing catalog skill of the same name.

        Returns:
            The imported skill directory in the catalog.

        Raises:
            SkillImportError: `source` isn't a valid, self-contained skill outside the catalog,
                or the target exists without `force`.
            SourcesError: The collection name is invalid, or the sources file is invalid or
                can't be edited.
        """
        check_collection_name(collection)
        source = source.expanduser().resolve()
        self._validate(source)
        target = self._sources.root / "skills" / collection / source.name
        if exists(target) and not force:
            raise SkillImportError(
                f"{target.relative_to(self._sources.root)} already exists. "
                "Use --force to replace it."
            )

        def copy() -> None:
            with replacing(target) as staging:
                shutil.copytree(source, staging, symlinks=True, ignore=_ignored, dirs_exist_ok=True)

        self._sources.record_provenance(
            collection, source.name, LocalUpstream.of(source, self._home), before_write=copy
        )
        return target

    def _validate(self, source: Path) -> None:
        if source.is_relative_to(self._sources.root.resolve()):
            raise SkillImportError(f"{source} is already part of the catalog repository")
        skill_md = source / "SKILL.md"
        if skill_md.is_symlink() or not skill_md.is_file():
            raise SkillImportError(f"{source} has no SKILL.md file")
        name = skill_name(skill_md.read_text(encoding="utf-8"))
        if name != source.name:
            raise SkillImportError(
                f"SKILL.md name {name!r} does not match its directory {source.name!r}"
            )
        for link in (p for p in source.rglob("*") if p.is_symlink()):
            if not link.resolve().is_relative_to(source):
                raise SkillImportError(f"{link.relative_to(source)} points outside the skill")


def _ignored(_directory: str, names: list[str]) -> list[str]:
    return [n for n in names if is_ignored(n)]
