"""Command-line interface: the composition root wiring dependencies into typer commands."""

from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import httpx
import typer
from rich.console import Console

from skillctl import views
from skillctl.catalog import Catalog, CatalogQuery, CatalogRef
from skillctl.github import GitHubClient
from skillctl.scopes import LockfileError, NotInRepositoryError, ScopeName, Scopes


def _default_github() -> GitHubClient:
    return GitHubClient(httpx.Client(timeout=30, follow_redirects=True))


@dataclass(frozen=True)
class Dependencies:
    """Collaborators the commands need; tests pass fakes, `main` passes real ones."""

    github: GitHubClient = field(default_factory=_default_github)
    console: Console = field(default_factory=Console)
    catalog_ref: CatalogRef = field(default_factory=CatalogRef)
    home: Path = field(default_factory=Path.home)
    cwd: Path = field(default_factory=Path.cwd)


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"skillctl {version('skillctl')}")
        raise typer.Exit


def create_app(deps: Dependencies) -> typer.Typer:
    """Build the `skillctl` typer application around the given dependencies.

    Args:
        deps: Collaborators used by the commands.

    Returns:
        The configured typer application.
    """
    app = typer.Typer(
        name="skillctl",
        help="Manage GitHub Copilot skills curated in the superpowers repository.",
        no_args_is_help=True,
    )

    @app.callback()
    def root(
        _version: Annotated[
            bool,
            typer.Option(
                "--version", callback=_print_version, is_eager=True, help="Show the version."
            ),
        ] = False,
    ) -> None:
        """Manage GitHub Copilot skills curated in the superpowers repository."""

    @app.command()
    def available(
        collection: Annotated[
            str | None, typer.Option("--collection", "-c", help="Only this collection.")
        ] = None,
        search: Annotated[
            str | None, typer.Option("--search", "-s", help="Match name or description.")
        ] = None,
        as_json: Annotated[bool, typer.Option("--json", help="Print JSON.")] = False,
    ) -> None:
        """List skills installable from the catalog repository."""
        where = deps.catalog_ref
        skills = Catalog(deps.github, where).skills(CatalogQuery(collection, search))
        if as_json:
            deps.console.print_json(data=views.catalog_json(skills))
        else:
            deps.console.print(views.catalog_table(skills, f"{where.repo}@{where.ref}"))

    @app.command()
    def installed(
        scope: Annotated[
            ScopeName | None, typer.Option("--scope", help="Only this scope (default: all).")
        ] = None,
        as_json: Annotated[bool, typer.Option("--json", help="Print JSON.")] = False,
    ) -> None:
        """List skills installed globally and, inside a repository, locally."""
        scopes = Scopes(deps.home, deps.cwd)
        try:
            selected = scopes.select(scope)
            found = [i for s in selected for i in s.installations()]
        except (NotInRepositoryError, LockfileError) as error:
            deps.console.print(f"[red]Error:[/] {error}")
            raise typer.Exit(1) from error
        try:
            catalog_names: set[str] | None = Catalog(deps.github, deps.catalog_ref).names()
        except httpx.HTTPError:
            catalog_names = None
        if as_json:
            deps.console.print_json(data=views.installed_json(found, catalog_names))
            return
        deps.console.print(views.installed_table(found, catalog_names, deps.home))
        if scope is None and scopes.local_scope is None:
            deps.console.print(
                "[dim]Not inside a git repository: local scope (.github/skills) not shown.[/]"
            )

    return app


def main() -> None:
    """Run `skillctl` with real dependencies."""
    create_app(Dependencies())()
