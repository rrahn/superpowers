"""The catalog: skills installable from the catalog repository."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import PurePosixPath

import yaml

from skillctl.github import GitHubClient, TreeEntry

SKILLS_ROOT = "skills"
SKILL_FILE = "SKILL.md"


@dataclass(frozen=True)
class CatalogSkill:
    """A skill published in the catalog repository."""

    name: str
    collection: str
    description: str
    path: str


@dataclass(frozen=True)
class CatalogRef:
    """Which repository and ref the catalog is read from."""

    repo: str = "rrahn/superpowers"
    ref: str = "main"


@dataclass(frozen=True)
class CatalogQuery:
    """Narrows the catalog by collection and a case-insensitive search term."""

    collection: str | None = None
    search: str | None = None

    def matches(self, skill: CatalogSkill) -> bool:
        """Check `skill` against every filter that is set.

        Args:
            skill: The catalog skill to test.

        Returns:
            True if the skill is in the collection (when set) and its name or description
            contains the search term (when set).
        """
        if self.collection and skill.collection != self.collection:
            return False
        needle = (self.search or "").casefold()
        return needle in skill.name.casefold() or needle in skill.description.casefold()


class Catalog:
    """Discovers skills in the catalog repository through GitHub."""

    def __init__(self, github: GitHubClient, where: CatalogRef) -> None:
        self._github = github
        self._where = where

    def skills(self, query: CatalogQuery | None = None) -> list[CatalogSkill]:
        """List catalog skills.

        Args:
            query: Optional filters; all skills when omitted.

        Returns:
            Matching skills sorted by collection, then name.
        """
        query = query or CatalogQuery()
        entries = self._github.tree(self._where.repo, self._where.ref)
        candidates = [e for e in entries if _is_skill_file(e)]
        with ThreadPoolExecutor(max_workers=16) as pool:
            texts = pool.map(self._read, (e.path for e in candidates))
            found = [_parse(e.path, text) for e, text in zip(candidates, texts, strict=True)]
        return sorted(
            (s for s in found if s and query.matches(s)), key=lambda s: (s.collection, s.name)
        )

    def _read(self, path: str) -> str:
        return self._github.read_text(self._where.repo, self._where.ref, path)


def _is_skill_file(entry: TreeEntry) -> bool:
    parts = PurePosixPath(entry.path).parts
    return (
        entry.type == "blob"
        and len(parts) >= 3
        and parts[0] == SKILLS_ROOT
        and parts[-1] == SKILL_FILE
    )


def _parse(path: str, text: str) -> CatalogSkill | None:
    directory = PurePosixPath(path).parent
    meta = _frontmatter(text)
    if meta.get("name") != directory.name:
        return None
    return CatalogSkill(
        name=directory.name,
        collection=directory.parts[1],
        description=" ".join(str(meta.get("description", "")).split()),
        path=str(directory),
    )


def _frontmatter(text: str) -> dict[str, object]:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    closing = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if closing is None:
        return {}
    try:
        meta = yaml.safe_load("\n".join(lines[1:closing]))
    except yaml.YAMLError:
        return {}
    return meta if isinstance(meta, dict) else {}
