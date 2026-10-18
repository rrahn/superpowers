"""Upstream sources: where each collection in the catalog repository comes from."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from skillctl.errors import SkillctlError
from skillctl.scopes import repository_root

SOURCES_FILE = Path("skills") / "sources.toml"


class SourcesError(SkillctlError):
    """The sources file is missing or invalid."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class GitHubUpstream(_Strict):
    """A public GitHub repository, read at `ref`, with skills under `path`."""

    github: Annotated[str, Field(pattern=r"^[\w.-]+/[\w.-]+$", description="owner/name")]
    ref: str = "main"
    path: str = ""

    @property
    def kind(self) -> Literal["github"]:
        """Discriminator shown to users."""
        return "github"

    def __str__(self) -> str:
        return f"{self.github}@{self.ref}:{self.path}" if self.path else f"{self.github}@{self.ref}"


class LocalUpstream(_Strict):
    """A directory on this machine, e.g. a clone of a private repository."""

    local: str

    @property
    def kind(self) -> Literal["local"]:
        """Discriminator shown to users."""
        return "local"

    def __str__(self) -> str:
        return self.local


Upstream = GitHubUpstream | LocalUpstream


class Collection(_Strict):
    """One `skills/<collection>/` directory and where its skills come from."""

    upstream: Upstream | None = None
    note: str | None = None
    skills: dict[str, Upstream] = Field(
        default_factory=dict, description="Per-skill provenance overriding the collection's."
    )


class Sources(_Strict):
    """The parsed sources file."""

    version: Literal[1] = 1
    collections: dict[str, Collection] = Field(default_factory=dict)


class SourcesFile:
    """`skills/sources.toml` in a checkout of the catalog repository."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.path = root / SOURCES_FILE

    @classmethod
    def find(cls, cwd: Path) -> "SourcesFile":
        """Locate the sources file of the repository containing `cwd`.

        Args:
            cwd: Any directory inside the catalog repository.

        Returns:
            The sources file.

        Raises:
            SourcesError: `cwd` isn't inside a repository with `skills/sources.toml`.
        """
        root = repository_root(cwd)
        if root is None or not (root / SOURCES_FILE).is_file():
            raise SourcesError(
                f"No {SOURCES_FILE.as_posix()} found from {cwd}; "
                "run inside a checkout of the catalog repository."
            )
        return cls(root)

    def load(self) -> Sources:
        """Parse and validate the file.

        Returns:
            The validated sources.

        Raises:
            SourcesError: The file isn't valid TOML or doesn't match the schema; the message
                names the offending key.
        """
        try:
            data = tomllib.loads(self.path.read_text())
        except tomllib.TOMLDecodeError as error:
            raise SourcesError(f"{self.path} is not valid TOML: {error}") from error
        try:
            return Sources.model_validate(data)
        except ValidationError as error:
            first = error.errors()[0]
            key = ".".join(str(p) for p in first["loc"] if not _is_union_branch(p))
            raise SourcesError(f"{self.path}: invalid key {key}: {first['msg']}") from error

    def skill_count(self, collection: str) -> int:
        """Count `SKILL.md` files under `skills/<collection>/` in the working tree."""
        return sum(1 for _ in (self.root / "skills" / collection).rglob("SKILL.md"))

    def overview(self) -> list["CollectionOverview"]:
        """Summarise every declared collection.

        Returns:
            One row per collection, sorted by name.

        Raises:
            SourcesError: The file is invalid.
        """
        return [
            CollectionOverview(
                collection=name,
                kind=collection.upstream.kind if collection.upstream else "none",
                upstream=str(collection.upstream) if collection.upstream else None,
                skills=self.skill_count(name),
                note=collection.note,
            )
            for name, collection in sorted(self.load().collections.items())
        ]


@dataclass(frozen=True)
class CollectionOverview:
    """One row of `skillctl sources list`."""

    collection: str
    kind: Literal["github", "local", "none"]
    upstream: str | None
    skills: int
    note: str | None


def _is_union_branch(part: object) -> bool:
    return part in {"GitHubUpstream", "LocalUpstream"}
