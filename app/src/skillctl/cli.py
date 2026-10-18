"""Command-line interface: the composition root wiring dependencies into typer commands."""

from dataclasses import dataclass, field
from importlib.metadata import version
from typing import Annotated

import httpx
import typer
from rich.console import Console

from skillctl import views
from skillctl.catalog import Catalog, CatalogRef
from skillctl.github import GitHubClient


def _default_github() -> GitHubClient:
    return GitHubClient(httpx.Client(timeout=30, follow_redirects=True))


@dataclass(frozen=True)
class Dependencies:
    """Collaborators the commands need; tests pass fakes, `main` passes real ones."""

    github: GitHubClient = field(default_factory=_default_github)
    console: Console = field(default_factory=Console)
    catalog_ref: CatalogRef = field(default_factory=CatalogRef)


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
    def available() -> None:
        """List skills installable from the catalog repository."""
        where = deps.catalog_ref
        skills = Catalog(deps.github, where).skills()
        deps.console.print(views.catalog_table(skills, f"{where.repo}@{where.ref}"))

    return app


def main() -> None:
    """Run `skillctl` with real dependencies."""
    create_app(Dependencies())()
