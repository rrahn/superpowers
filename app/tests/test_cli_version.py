from typer.testing import CliRunner

from skillctl.cli import Dependencies, create_app


def test_version_prints_package_version() -> None:
    result = CliRunner().invoke(create_app(Dependencies()), ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == "skillctl 0.1.0"


def test_help_describes_the_tool() -> None:
    result = CliRunner().invoke(create_app(Dependencies()), ["--help"])

    assert result.exit_code == 0
    assert "Manage GitHub Copilot skills" in result.output
