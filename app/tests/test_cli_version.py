from typer.testing import CliRunner

from skillctl.cli import Dependencies, create_app

from .support import FakeGitHub


def deps() -> Dependencies:
    return Dependencies(github=FakeGitHub().client())


def test_version_prints_package_version() -> None:
    result = CliRunner().invoke(create_app(deps()), ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == "skillctl 0.1.0"


def test_help_describes_the_tool() -> None:
    result = CliRunner().invoke(create_app(deps()), ["--help"])

    assert result.exit_code == 0
    assert "Manage GitHub Copilot skills" in result.output
