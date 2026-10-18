import io
from collections.abc import Callable

import pytest
from rich.console import Console
from typer.testing import CliRunner

from skillctl.cli import Dependencies, create_app

from .support import FakeGitHub, Run


@pytest.fixture
def github() -> FakeGitHub:
    return FakeGitHub()


@pytest.fixture
def run(github: FakeGitHub) -> Callable[..., Run]:
    """Invoke the CLI against the fake GitHub, recording output on a fixed-width console."""

    def _run(*args: str) -> Run:
        console = Console(
            file=io.StringIO(),
            width=100,
            record=True,
            force_terminal=True,
            color_system="truecolor",
        )
        deps = Dependencies(github=github.client(), console=console)
        result = CliRunner().invoke(create_app(deps), list(args))
        if result.exception and not isinstance(result.exception, SystemExit):
            raise result.exception
        return Run(result, console)

    return _run
