from collections.abc import Callable
from pathlib import Path

import pytest

from .support import FakeGitHub, Run, make_runner


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
    """Invoke the CLI against the fake GitHub from `cwd`."""
    return make_runner(github, home, cwd)
