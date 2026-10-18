"""Importing internally maintained skills from a local path into a collection."""

import shutil
from pathlib import Path

from skillctl.catalog import skill_name
from skillctl.errors import SkillctlError
from skillctl.fsops import exists, replacing
from skillctl.sources import LocalUpstream, SourcesFile

IGNORED = shutil.ignore_patterns(".*", "__pycache__")


class SkillImportError(SkillctlError):
    """A skill can't be imported."""


class LocalImporter:
    """Copies a skill from a local directory into the catalog and records where it came from."""

    def __init__(self, sources: SourcesFile, home: Path) -> None:
        self._sources = sources
        self._home = home

    def import_skill(self, source: Path, collection: str, *, force: bool = False) -> Path:
        """Import the skill at `source` into `skills/<collection>/<name>/`.

        Hidden files and `__pycache__` are skipped. Provenance is recorded in the sources file
        with `~` for paths under the home directory.

        Args:
            source: Directory holding the skill's `SKILL.md`.
            collection: Target collection; declared in the sources file when missing.
            force: Replace an existing catalog skill of the same name.

        Returns:
            The imported skill directory in the catalog.

        Raises:
            SkillImportError: `source` isn't a valid skill or the target exists without `force`.
            SourcesError: The sources file is invalid or can't be edited.
        """
        source = source.expanduser().resolve()
        self._validate(source)
        self._sources.load()
        target = self._sources.root / "skills" / collection / source.name
        if exists(target) and not force:
            raise SkillImportError(
                f"{target.relative_to(self._sources.root)} already exists. "
                "Use --force to replace it."
            )
        with replacing(target) as staging:
            shutil.copytree(source, staging, symlinks=True, ignore=IGNORED, dirs_exist_ok=True)
        self._sources.record_provenance(
            collection, source.name, LocalUpstream.of(source, self._home)
        )
        return target

    @staticmethod
    def _validate(source: Path) -> None:
        skill_md = source / "SKILL.md"
        if not skill_md.is_file():
            raise SkillImportError(f"{source} has no SKILL.md")
        name = skill_name(skill_md.read_text(encoding="utf-8"))
        if name != source.name:
            raise SkillImportError(
                f"SKILL.md name {name!r} does not match its directory {source.name!r}"
            )
