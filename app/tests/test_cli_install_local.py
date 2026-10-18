from collections.abc import Callable
from pathlib import Path

import pytest

from .support import FakeGitHub, Run, make_runner, skill_md

TDD = "skills/mattpocock/engineering/tdd"


@pytest.fixture
def repo(cwd: Path, github: FakeGitHub) -> Path:
    """Make the working directory a git repository and seed the catalog."""
    (cwd / ".git").mkdir()
    github.files = {f"{TDD}/SKILL.md": skill_md("tdd", "Test-driven development.")}
    return cwd


def test_install_local_writes_into_the_repository_github_skills(
    repo: Path, home: Path, run: Callable[..., Run]
) -> None:
    out = run("install", "tdd", "--scope", "local")

    assert out.result.exit_code == 0
    assert (repo / ".github" / "skills" / "tdd" / "SKILL.md").is_file()
    assert not (home / ".copilot").exists()


def test_install_local_from_a_subdirectory_targets_the_repository_root(
    repo: Path, github: FakeGitHub, home: Path
) -> None:
    nested = repo / "src" / "pkg"
    nested.mkdir(parents=True)

    out = make_runner(github, home, nested)("install", "tdd", "--scope", "local")

    assert out.result.exit_code == 0
    assert (repo / ".github" / "skills" / "tdd" / "SKILL.md").is_file()


def test_install_local_in_a_git_worktree_whose_git_entry_is_a_file(
    github: FakeGitHub, home: Path, cwd: Path
) -> None:
    (cwd / ".git").write_text("gitdir: /elsewhere/.git/worktrees/x\n")
    github.files = {f"{TDD}/SKILL.md": skill_md("tdd", "Test-driven development.")}

    out = make_runner(github, home, cwd)("install", "tdd", "--scope", "local")

    assert out.result.exit_code == 0
    assert (cwd / ".github" / "skills" / "tdd" / "SKILL.md").is_file()


def test_install_local_outside_a_repository_fails_and_writes_nothing(
    github: FakeGitHub, cwd: Path, run: Callable[..., Run]
) -> None:
    github.files = {f"{TDD}/SKILL.md": skill_md("tdd", "Test-driven development.")}

    out = run("install", "tdd", "--scope", "local")

    assert out.result.exit_code == 1
    assert "not inside a git repository" in out.text
    assert list(cwd.iterdir()) == []


def test_locally_installed_skill_is_listed_as_managed_in_the_local_scope(
    repo: Path, run: Callable[..., Run]
) -> None:
    run("install", "tdd", "--scope", "local")

    out = run("installed", "--json")

    assert [(r["name"], r["scope"], r["status"]) for r in out.json()] == [
        ("tdd", "local", "managed")
    ]
