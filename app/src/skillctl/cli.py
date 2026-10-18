"""Command-line interface: the composition root wiring dependencies into typer commands."""

from dataclasses import dataclass
from importlib.metadata import version
from typing import Annotated

import typer


@dataclass(frozen=True)
class Dependencies:
    """Collaborators the commands need; tests pass fakes, `main` passes real ones."""


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

    return app


def main() -> None:
    """Run `skillctl` with real dependencies."""
    create_app(Dependencies())()
