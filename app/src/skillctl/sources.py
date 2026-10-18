"""Upstream sources: where each collection, and each imported skill, comes from."""

import shutil
import tempfile
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal

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
    """A directory on this machine, e.g. a clone of a private repository.

    `~` is kept as written in the file and expanded against the user's home when read.
    """

    local: str

    @property
    def kind(self) -> Literal["local"]:
        """Discriminator shown to users."""
        return "local"

    def resolve(self, home: Path) -> Path:
        """The directory this upstream points at, with a leading `~` expanded to `home`."""
        if self.local == "~" or self.local.startswith("~/"):
            return home / self.local.removeprefix("~").lstrip("/")
        return Path(self.local)

    @classmethod
    def of(cls, directory: Path, home: Path) -> "LocalUpstream":
        """Point at `directory`, written relative to `~` when it lives under `home`."""
        if directory.is_relative_to(home):
            return cls(local=f"~/{directory.relative_to(home).as_posix()}")
        return cls(local=directory.as_posix())

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
    skills: dict[str, LocalUpstream] = Field(
        default_factory=dict,
        description="Provenance of individually imported skills, keyed by path in the collection.",
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
            data = tomllib.loads(self._read())
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
            raise SourcesError(f"{self.path} is not valid TOML: {error}") from error
        return self._validate(data)

    def add_github_upstream(
        self, github: GitHubClient, collection: str, upstream: GitHubUpstream, *, force: bool
    ) -> int:
        """Verify `upstream` on GitHub, then record it for `collection`.

        Conflicts are checked before any network call, and the file is written only after the
        upstream verified. Comments, ordering, and line endings of the file are kept.

        Args:
            github: Client used to verify the upstream.
            collection: Collection name; created when not declared yet.
            upstream: The upstream to record.
            force: Replace an upstream the collection already has.

        Returns:
            How many `SKILL.md` files live under the upstream path.

        Raises:
            SourcesError: The collection already has an upstream and `force` is False, the path
                doesn't exist upstream, or the file is invalid or can't be edited.
            GitHubError: The repository or ref doesn't exist, or GitHub is unreachable.
        """
        current = self.load().collections.get(collection)
        if current and current.upstream and not force:
            raise SourcesError(
                f"{collection} already has an upstream ({current.upstream}). "
                "Use --force to replace it."
            )
        found = _verify(github, upstream)
        self._edit(collection, lambda table: _set_upstream(table, upstream))
        return found

    def record_provenance(self, collection: str, skill: str, origin: LocalUpstream) -> None:
        """Record that `skill` in `collection` was imported from `origin`.

        Args:
            collection: Collection name; declared when missing.
            skill: Skill path inside the collection.
            origin: Where the skill was copied from.

        Raises:
            SourcesError: The file is invalid or can't be edited.
        """
        self._edit(collection, lambda table: _set_provenance(table, skill, origin))

    def _edit(self, collection: str, change: Callable[[Any], None]) -> None:
        document = tomlkit.parse(self._read())
        try:
            collections = document.setdefault("collections", tomlkit.table(is_super_table=True))
            change(collections.setdefault(collection, tomlkit.table()))
        except (ValueError, TypeError, AttributeError) as error:
            raise SourcesError(
                f"Cannot edit {self.path}: declare collections as [collections.<name>] tables"
            ) from error
        text = tomlkit.dumps(document)
        self._validate(tomllib.loads(text))
        self._write(text)

    def _read(self) -> str:
        try:
            with self.path.open(encoding="utf-8", newline="") as handle:
                return handle.read()
        except OSError as error:
            raise SourcesError(f"Cannot read {self.path}: {error.strerror}") from error

    def _write(self, text: str) -> None:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            dir=self.path.parent,
            prefix=".sources-",
            delete=False,
        ) as staged:
            staged.write(text)
        try:
            shutil.copymode(self.path, staged.name)
            Path(staged.name).replace(self.path.resolve())
        finally:
            Path(staged.name).unlink(missing_ok=True)

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


def _set_upstream(table: Any, upstream: GitHubUpstream) -> None:
    entry = tomlkit.inline_table()
    entry.update(upstream.model_dump())
    table["upstream"] = entry


def _set_provenance(table: Any, skill: str, origin: LocalUpstream) -> None:
    skills = table.setdefault("skills", tomlkit.table(is_super_table=True))
    entry = tomlkit.table()
    entry["local"] = origin.local
    skills[skill] = entry


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

    Args:
        repo: Repository as `owner/name`.
        ref: Branch, tag, or commit.
        path: Directory holding the skills; `.` or empty means the repository root.

    Returns:
        The upstream with a normalised path (`./skills/` becomes `skills`).

    Raises:
        SourcesError: `repo` isn't `owner/name`.
    """
    cleaned = PurePosixPath(path.strip()).as_posix()
    try:
        return GitHubUpstream(
            github=repo.strip(), ref=ref.strip(), path="" if cleaned == "." else cleaned
        )
    except ValidationError as error:
        raise SourcesError(f"GitHub repository must be owner/name, got {repo!r}") from error


def _verify(github: GitHubClient, upstream: GitHubUpstream) -> int:
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
