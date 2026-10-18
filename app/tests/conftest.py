import io
from collections.abc import Callable
from pathlib import Path

import pytest
from rich.console import Console
from typer.testing import CliRunner

from skillctl.cli import Dependencies, create_app

from .support import FakeGitHub, Run


@pytest.fixture
def github() -> FakeGitHub:
    return FakeGitHub()


@pytest.fixture
def home(tmp_path: Path) -> Path:
    path = tmp_path / "home"
    path.mkdir()
    return path


@pytest.fixture
def cwd(tmp_path: Path) -> Path:
    """Working directory; not a git repository unless a test makes it one."""
    path = tmp_path / "work"
    path.mkdir()
    return path


@pytest.fixture
def run(github: FakeGitHub, home: Path, cwd: Path) -> Callable[..., Run]:
    """Invoke the CLI against the fake GitHub, recording output on a fixed-width console."""

    def _run(*args: str) -> Run:
        console = Console(
            file=io.StringIO(),
            width=100,
            record=True,
            force_terminal=True,
            color_system="truecolor",
        )
        deps = Dependencies(github=github.client(), console=console, home=home, cwd=cwd)
        result = CliRunner().invoke(create_app(deps), list(args))
        if result.exception and not isinstance(result.exception, SystemExit):
            raise result.exception
        return Run(result, console)

    return _run
