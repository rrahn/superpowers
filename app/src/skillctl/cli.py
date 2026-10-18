"""Command-line interface: the composition root wiring dependencies into typer commands."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import httpx
import typer
from rich.console import Console

from skillctl import views
from skillctl.catalog import Catalog, CatalogQuery, CatalogRef
from skillctl.errors import SkillctlError
from skillctl.github import GitHubClient, GitHubError, token_from_env
from skillctl.installer import Installer
from skillctl.scopes import ScopeName, Scopes
from skillctl.sources import SOURCES_FILE, SourcesFile, github_upstream, verify


@dataclass(frozen=True)
class Dependencies:
    """Collaborators the commands need; tests pass fakes, `main` passes real ones."""

    github: GitHubClient
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

    @contextmanager
    def reported() -> Generator[None]:
        """Turn any expected failure into a one-line message and exit code 1."""
        try:
            yield
        except SkillctlError as error:
            deps.console.print(f"[red]Error:[/] {error}")
            raise typer.Exit(1) from error

    def catalog(ctx: typer.Context) -> Catalog:
        return Catalog(deps.github, where(ctx))

    def where(ctx: typer.Context) -> CatalogRef:
        return ctx.obj

    @app.callback()
    def root(
        ctx: typer.Context,
        repo: Annotated[
            str,
            typer.Option(envvar="SKILLCTL_REPO", help="Catalog repository as owner/name."),
        ] = deps.catalog_ref.repo,
        ref: Annotated[
            str,
            typer.Option(envvar="SKILLCTL_REF", help="Branch, tag, or commit of the catalog."),
        ] = deps.catalog_ref.ref,
        _version: Annotated[
            bool,
            typer.Option(
                "--version", callback=_print_version, is_eager=True, help="Show the version."
            ),
        ] = False,
    ) -> None:
        """Manage GitHub Copilot skills curated in the superpowers repository."""
        ctx.obj = CatalogRef(repo, ref)

    @app.command()
    def available(
        ctx: typer.Context,
        collection: Annotated[
            str | None, typer.Option("--collection", "-c", help="Only this collection.")
        ] = None,
        search: Annotated[
            str | None, typer.Option("--search", "-s", help="Match name or description.")
        ] = None,
        as_json: Annotated[bool, typer.Option("--json", help="Print JSON.")] = False,
    ) -> None:
        """List skills installable from the catalog repository."""
        with reported():
            skills = catalog(ctx).skills(CatalogQuery(collection, search))
        if as_json:
            deps.console.print_json(data=views.catalog_json(skills))
        else:
            source = where(ctx)
            deps.console.print(views.catalog_table(skills, f"{source.repo}@{source.ref}"))

    @app.command()
    def installed(
        ctx: typer.Context,
        scope: Annotated[
            ScopeName | None, typer.Option("--scope", help="Only this scope (default: all).")
        ] = None,
        as_json: Annotated[bool, typer.Option("--json", help="Print JSON.")] = False,
    ) -> None:
        """List skills installed globally and, inside a repository, locally."""
        scopes = Scopes(deps.home, deps.cwd)
        with reported():
            found = [i for s in scopes.select(scope) for i in s.installations()]
        try:
            catalog_names: set[str] | None = catalog(ctx).names()
        except GitHubError as error:
            catalog_names = None
            if not as_json:
                deps.console.print(f"[yellow]Warning:[/] catalog membership unknown: {error}")
        if as_json:
            deps.console.print_json(data=views.installed_json(found, catalog_names))
            return
        deps.console.print(views.installed_table(found, catalog_names, deps.home))
        if scope is None and scopes.local_scope is None:
            deps.console.print(
                "[dim]Not inside a git repository: local scope (.github/skills) not shown.[/]"
            )

    @app.command()
    def install(
        ctx: typer.Context,
        name: Annotated[str, typer.Argument(help="Catalog skill name.")],
        force: Annotated[
            bool, typer.Option("--force", "-f", help="Replace an existing installation.")
        ] = False,
        scope_name: Annotated[
            ScopeName,
            typer.Option(
                "--scope", help="global: ~/.copilot/skills; local: <repo>/.github/skills."
            ),
        ] = ScopeName.GLOBAL,
    ) -> None:
        """Install a catalog skill globally or into the current repository."""
        with reported():
            scope = Scopes(deps.home, deps.cwd).get(scope_name)
            skill = Installer(catalog(ctx)).install(name, scope, force=force)
        deps.console.print(
            f"[green]Installed[/] [bold]{skill.name}[/] from {skill.path} into {scope.root}"
        )

    sources_app = typer.Typer(
        help="Upstream sources of the catalog's collections (run inside the catalog repo).",
        no_args_is_help=True,
    )
    app.add_typer(sources_app, name="sources")

    @sources_app.command("list")
    def sources_list(
        as_json: Annotated[bool, typer.Option("--json", help="Print JSON.")] = False,
    ) -> None:
        """List every collection and the upstream it is curated from."""
        with reported():
            file = SourcesFile.find(deps.cwd)
            rows = file.overview()
        if as_json:
            deps.console.print_json(data=views.sources_json(rows))
        else:
            deps.console.print(views.sources_table(rows, SOURCES_FILE.as_posix()))

    @sources_app.command("add")
    def sources_add(
        collection: Annotated[str, typer.Argument(help="Collection under skills/.")],
        repo: Annotated[
            str | None, typer.Option("--github", help="Public repository as owner/name.")
        ] = None,
        ref: Annotated[str | None, typer.Option(help="Branch, tag, or commit.")] = None,
        path: Annotated[
            str | None, typer.Option(help="Directory holding the skills ('' for the root).")
        ] = None,
        force: Annotated[
            bool, typer.Option("--force", "-f", help="Replace an existing upstream.")
        ] = False,
    ) -> None:
        """Add a public GitHub upstream for a collection; prompts for anything not given."""
        with reported():
            file = SourcesFile.find(deps.cwd)
            upstream = github_upstream(
                repo if repo is not None else typer.prompt("GitHub repository (owner/name)"),
                ref if ref is not None else typer.prompt("Ref", default="main"),
                path if path is not None else typer.prompt("Path to skills", default="skills"),
            )
            with deps.console.status(f"Checking {upstream} on GitHub…"):
                found = verify(deps.github, upstream)
            file.set_upstream(collection, upstream, force=force)
        deps.console.print(
            f"[green]Added[/] {collection} ← {upstream} "
            f"({found} skill{'s' if found != 1 else ''} upstream)"
        )

    return app


def main() -> None:
    """Run `skillctl` with real dependencies, closing the HTTP client on exit."""
    with httpx.Client(timeout=30, follow_redirects=True) as http:
        github = GitHubClient(http, token=token_from_env(os.environ))
        create_app(Dependencies(github=github))()
