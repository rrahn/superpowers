"""The catalog: skills installable from the catalog repository."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from difflib import get_close_matches
from functools import cached_property
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
    tree_sha: str


@dataclass(frozen=True)
class SkillFile:
    """One file inside a catalog skill, as git records it."""

    path: str
    executable: bool
    symlink: bool


class SkillNotFoundError(Exception):
    """No catalog skill has the requested name."""

    def __init__(self, name: str, suggestions: list[str]) -> None:
        super().__init__(f"No skill named '{name}' in the catalog")
        self.name = name
        self.suggestions = suggestions


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
    """Discovers and reads skills in the catalog repository through GitHub.

    One instance resolves the ref to a commit once and reads the tree and every file at that
    commit, so a branch moving mid-command can't mix files from two commits.
    """

    def __init__(self, github: GitHubClient, where: CatalogRef) -> None:
        self._github = github
        self._where = where

    @property
    def where(self) -> CatalogRef:
        """The repository and ref this catalog reads."""
        return self._where

    @cached_property
    def commit(self) -> str:
        """The commit the ref pointed at when this catalog first read it."""
        return self._github.commit(self._where.repo, self._where.ref)

    @cached_property
    def _entries(self) -> list[TreeEntry]:
        return self._github.tree(self._where.repo, self.commit)

    @cached_property
    def _tree_shas(self) -> dict[str, str]:
        return {e.path: e.sha for e in self._entries if e.type == "tree"}

    def skills(self, query: CatalogQuery | None = None) -> list[CatalogSkill]:
        """List catalog skills.

        Args:
            query: Optional filters; all skills when omitted.

        Returns:
            Matching skills sorted by collection, then name.
        """
        query = query or CatalogQuery()
        candidates = [e for e in self._entries if _is_skill_file(e)]
        with ThreadPoolExecutor(max_workers=16) as pool:
            texts = pool.map(self._read, (e.path for e in candidates))
            found = [self._parse(e.path, text) for e, text in zip(candidates, texts, strict=True)]
        return sorted(
            (s for s in found if s and query.matches(s)), key=lambda s: (s.collection, s.name)
        )

    def find(self, name: str) -> CatalogSkill:
        """Look up one skill by name, reading only its `SKILL.md`.

        Args:
            name: The skill name.

        Returns:
            The matching skill.

        Raises:
            SkillNotFoundError: No valid skill has that name; carries close matches.
        """
        for entry in self._entries:
            if _is_skill_file(entry) and PurePosixPath(entry.path).parent.name == name:
                skill = self._parse(entry.path, self._read(entry.path))
                if skill:
                    return skill
        raise SkillNotFoundError(name, get_close_matches(name, sorted(self.names()), n=3))

    def files(self, skill: CatalogSkill) -> list[SkillFile]:
        """List every file of a skill.

        Args:
            skill: A skill from this catalog.

        Returns:
            Its files with paths relative to the skill directory, sorted by path.
        """
        prefix = f"{skill.path}/"
        return sorted(
            (
                SkillFile(e.path.removeprefix(prefix), e.executable, e.symlink)
                for e in self._entries
                if e.type == "blob" and e.path.startswith(prefix)
            ),
            key=lambda f: f.path,
        )

    def read(self, skill: CatalogSkill, file: SkillFile) -> bytes:
        """Download one file of a skill.

        Args:
            skill: A skill from this catalog.
            file: One of `files(skill)`.

        Returns:
            The file's raw content at the pinned commit.
        """
        return self._github.read_bytes(self._where.repo, self.commit, f"{skill.path}/{file.path}")

    def _read(self, path: str) -> str:
        return self._github.read_text(self._where.repo, self.commit, path)

    def names(self) -> set[str]:
        """Cheaply list skill names from the tree alone, without reading any `SKILL.md`.

        Returns:
            Directory names of every `SKILL.md` under `skills/`.
        """
        return {PurePosixPath(e.path).parent.name for e in self._entries if _is_skill_file(e)}

    def _parse(self, path: str, text: str) -> CatalogSkill | None:
        directory = PurePosixPath(path).parent
        meta = _frontmatter(text)
        if meta.get("name") != directory.name:
            return None
        return CatalogSkill(
            name=directory.name,
            collection=directory.parts[1],
            description=" ".join(str(meta.get("description", "")).split()),
            path=str(directory),
            tree_sha=self._tree_shas.get(str(directory), ""),
        )


def _is_skill_file(entry: TreeEntry) -> bool:
    parts = PurePosixPath(entry.path).parts
    return (
        entry.type == "blob"
        and len(parts) >= 3
        and parts[0] == SKILLS_ROOT
        and parts[-1] == SKILL_FILE
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
