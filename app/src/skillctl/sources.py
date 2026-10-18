"""Upstream sources: where each collection in the catalog repository comes from."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

import tomlkit
from pydantic import BaseModel, ConfigDict, Discriminator, Field, Tag, ValidationError

from skillctl.catalog import skill_name
from skillctl.errors import SkillctlError
from skillctl.github import GitHubClient
from skillctl.scopes import repository_root

SOURCES_FILE = Path("skills") / "sources.toml"
_TAGS = {"github": "GitHub", "local": "Local"}


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


def _upstream_tag(value: object) -> str | None:
    keys = value.keys() if isinstance(value, dict) else vars(value).keys()
    return next((tag for key, tag in _TAGS.items() if key in keys), None)


Upstream = Annotated[
    Annotated[GitHubUpstream, Tag(_TAGS["github"])] | Annotated[LocalUpstream, Tag(_TAGS["local"])],
    Discriminator(
        _upstream_tag,
        custom_error_type="invalid_upstream",
        custom_error_message='expected github = "owner/name" or local = "path"',
    ),
]


class Collection(_Strict):
    """One `skills/<collection>/` directory and where its skills come from."""

    upstream: Upstream | None = None
    note: str | None = None


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
            data = tomllib.loads(self._read())
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
            raise SourcesError(f"{self.path} is not valid TOML: {error}") from error
        return self._validate(data)

    def set_upstream(self, collection: str, upstream: "GitHubUpstream", *, force: bool) -> None:
        """Record `upstream` for `collection`, keeping comments and every other entry.

        Args:
            collection: Collection name; created when not declared yet.
            upstream: The upstream to record.
            force: Replace an upstream the collection already has.

        Raises:
            SourcesError: The collection already has an upstream and `force` is False, or the
                file is invalid.
        """
        current = self.load().collections.get(collection)
        if current and current.upstream and not force:
            raise SourcesError(
                f"{collection} already has an upstream ({current.upstream}). "
                "Use --force to replace it."
            )
        document = tomlkit.parse(self._read())
        collections = document.setdefault("collections", tomlkit.table(is_super_table=True))
        table = collections.setdefault(collection, tomlkit.table())
        entry = tomlkit.inline_table()
        entry.update(upstream.model_dump(exclude_defaults=False))
        table["upstream"] = entry
        self._validate(document.unwrap())
        staged = self.path.with_name(f".{self.path.name}.tmp")
        staged.write_text(tomlkit.dumps(document), encoding="utf-8")
        staged.replace(self.path)

    def _read(self) -> str:
        try:
            return self.path.read_text(encoding="utf-8")
        except OSError as error:
            raise SourcesError(f"Cannot read {self.path}: {error.strerror}") from error

    def _validate(self, data: object) -> Sources:
        try:
            return Sources.model_validate(data)
        except ValidationError as error:
            first = error.errors()[0]
            key = ".".join(str(p) for p in first["loc"] if p not in _TAGS.values())
            raise SourcesError(f"{self.path}: invalid key {key}: {first['msg']}") from error

    def skill_count(self, collection: str) -> int:
        """Count skills under `skills/<collection>/` whose `SKILL.md` name matches its folder."""
        return sum(
            1
            for skill_md in (self.root / "skills" / collection).rglob("SKILL.md")
            if skill_name(skill_md.read_text(encoding="utf-8")) == skill_md.parent.name
        )

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


def github_upstream(repo: str, ref: str, path: str) -> GitHubUpstream:
    """Build a GitHub upstream from user input.

    Raises:
        SourcesError: `repo` isn't `owner/name`.
    """
    try:
        return GitHubUpstream(github=repo, ref=ref, path=path.strip("/"))
    except ValidationError as error:
        raise SourcesError(f"GitHub repository must be owner/name, got {repo!r}") from error


def verify(github: GitHubClient, upstream: GitHubUpstream) -> int:
    """Check that the upstream's repository, ref, and path exist on GitHub.

    Args:
        github: Client used to read the upstream.
        upstream: The upstream to check.

    Returns:
        How many `SKILL.md` files live under the upstream path.

    Raises:
        GitHubError: The repository or ref doesn't exist, or GitHub is unreachable.
        SourcesError: The path isn't a directory in the repository.
    """
    commit = github.commit(upstream.github, upstream.ref)
    entries = github.tree(upstream.github, commit)
    path = upstream.path
    if path and not any(e.type == "tree" and e.path == path for e in entries):
        raise SourcesError(f"{upstream.github}@{upstream.ref} has no directory {path}")
    prefix = f"{path}/" if path else ""
    return sum(
        1
        for e in entries
        if e.type == "blob" and e.path.startswith(prefix) and e.path.endswith("/SKILL.md")
    )
