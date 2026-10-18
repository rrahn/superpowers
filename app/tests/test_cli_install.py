import json
import os
from collections.abc import Callable
from pathlib import Path

from .support import FakeGitHub, Run, skill_md

TDD = "skills/mattpocock/engineering/tdd"


def seed(github: FakeGitHub) -> None:
    github.files = {
        f"{TDD}/SKILL.md": skill_md("tdd", "Test-driven development."),
        f"{TDD}/tests.md": "# Good and bad tests\n",
        f"{TDD}/examples/red-green.md": "# Red, then green\n",
        "skills/superpowers/brainstorming/SKILL.md": skill_md("brainstorming", "Ideas."),
    }


def global_root(home: Path) -> Path:
    return home / ".copilot" / "skills"


def files_under(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): p.read_text() for p in root.rglob("*") if p.is_file()}


def test_install_copies_every_file_of_the_skill_into_the_global_scope(
    github: FakeGitHub, home: Path, run: Callable[..., Run]
) -> None:
    seed(github)

    out = run("install", "tdd")

    assert out.result.exit_code == 0
    assert files_under(global_root(home) / "tdd") == {
        "SKILL.md": skill_md("tdd", "Test-driven development."),
        "tests.md": "# Good and bad tests\n",
        "examples/red-green.md": "# Red, then green\n",
    }
    assert "Installed tdd" in out.text


def test_installed_skill_is_listed_as_managed(github: FakeGitHub, run: Callable[..., Run]) -> None:
    seed(github)
    run("install", "tdd")

    out = run("installed", "--json")

    assert [(r["name"], r["status"]) for r in out.json()] == [("tdd", "managed")]


def test_install_records_where_the_skill_came_from(
    github: FakeGitHub, home: Path, run: Callable[..., Run]
) -> None:
    seed(github)

    run("install", "tdd")

    lock = json.loads((global_root(home) / ".skillctl-lock.json").read_text())
    entry = lock["skills"]["tdd"]
    assert (entry["repo"], entry["ref"], entry["path"]) == ("rrahn/superpowers", "main", TDD)
    assert entry["commit"] == github.commit
    assert entry["tree_sha"]


def test_install_keeps_executable_scripts_executable(
    github: FakeGitHub, home: Path, run: Callable[..., Run]
) -> None:
    seed(github)
    github.files[f"{TDD}/scripts/check.sh"] = "#!/bin/sh\necho ok\n"
    github.executables = {f"{TDD}/scripts/check.sh"}

    run("install", "tdd")

    installed = global_root(home) / "tdd"
    assert os.access(installed / "scripts" / "check.sh", os.X_OK)
    assert not os.access(installed / "tests.md", os.X_OK)


def test_install_reports_an_unreachable_github_without_a_traceback(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.fail = True

    out = run("install", "tdd")

    assert out.result.exit_code == 1
    assert "Could not reach GitHub" in out.text


def test_failed_download_with_force_keeps_the_existing_installation(
    github: FakeGitHub, home: Path, run: Callable[..., Run]
) -> None:
    seed(github)
    existing = global_root(home) / "tdd"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("keep me")
    github.unreadable = {f"{TDD}/tests.md"}

    out = run("install", "tdd", "--force")

    assert out.result.exit_code == 1
    assert files_under(existing) == {"SKILL.md": "keep me"}


def test_install_refuses_to_overwrite_without_force(
    github: FakeGitHub, home: Path, run: Callable[..., Run]
) -> None:
    seed(github)
    existing = global_root(home) / "tdd"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("my local edits")

    out = run("install", "tdd")

    assert out.result.exit_code == 1
    assert "already installed" in out.text
    assert (existing / "SKILL.md").read_text() == "my local edits"


def test_install_with_force_replaces_the_existing_installation(
    github: FakeGitHub, home: Path, run: Callable[..., Run]
) -> None:
    seed(github)
    existing = global_root(home) / "tdd"
    existing.mkdir(parents=True)
    (existing / "stale.md").write_text("old")

    out = run("install", "tdd", "--force")

    assert out.result.exit_code == 0
    assert sorted(files_under(existing)) == ["SKILL.md", "examples/red-green.md", "tests.md"]


def test_install_with_force_replaces_a_symlink_without_touching_its_target(
    github: FakeGitHub, home: Path, run: Callable[..., Run]
) -> None:
    seed(github)
    target = home / "clone" / "tdd"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("clone copy")
    global_root(home).mkdir(parents=True)
    (global_root(home) / "tdd").symlink_to(target)

    run("install", "tdd", "--force")

    assert not (global_root(home) / "tdd").is_symlink()
    assert (target / "SKILL.md").read_text() == "clone copy"


def test_install_unknown_skill_suggests_close_matches(
    github: FakeGitHub, home: Path, run: Callable[..., Run]
) -> None:
    seed(github)

    out = run("install", "brainstorm")

    assert out.result.exit_code == 1
    assert "No skill named 'brainstorm'" in out.text
    assert "Did you mean: brainstorming?" in out.text
    assert not global_root(home).exists()


def test_failed_download_leaves_nothing_behind(
    github: FakeGitHub, home: Path, run: Callable[..., Run]
) -> None:
    seed(github)
    github.unreadable = {f"{TDD}/examples/red-green.md"}

    out = run("install", "tdd")

    assert out.result.exit_code == 1
    assert "Could not download tdd" in out.text
    leftovers = list(global_root(home).iterdir()) if global_root(home).exists() else []
    assert leftovers == []
