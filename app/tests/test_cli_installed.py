import json
from collections.abc import Callable
from pathlib import Path

from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.image import SVGImageSnapshotExtension

from .support import FakeGitHub, Run, skill_md


def make_skill(scope_root: Path, name: str) -> Path:
    path = scope_root / name
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text(skill_md(name, f"The {name} skill."))
    return path


def lock(scope_root: Path, *names: str) -> None:
    entries = {
        n: {"repo": "rrahn/superpowers", "ref": "main", "path": f"skills/x/{n}"} for n in names
    }
    (scope_root / ".skillctl-lock.json").write_text(json.dumps({"version": 1, "skills": entries}))


def global_root(home: Path) -> Path:
    return home / ".copilot" / "skills"


def make_repo(cwd: Path) -> Path:
    (cwd / ".git").mkdir()
    return cwd / ".github" / "skills"


def catalog(github: FakeGitHub, *names: str) -> None:
    github.files = {f"skills/x/{n}/SKILL.md": skill_md(n, "d") for n in names}


def rows(out: Run) -> list[dict[str, object]]:
    return out.json()


def test_installed_marks_global_skills_managed_or_unmanaged(
    github: FakeGitHub, home: Path, run: Callable[..., Run]
) -> None:
    catalog(github, "tdd", "brainstorming")
    root = global_root(home)
    make_skill(root, "tdd")
    make_skill(root, "my-own")
    lock(root, "tdd")

    out = run("installed", "--json")

    assert rows(out) == [
        {
            "name": "my-own",
            "scope": "global",
            "status": "unmanaged",
            "in_catalog": False,
            "link": None,
        },
        {"name": "tdd", "scope": "global", "status": "managed", "in_catalog": True, "link": None},
    ]


def test_installed_shows_symlink_targets(
    github: FakeGitHub, home: Path, tmp_path: Path, run: Callable[..., Run]
) -> None:
    catalog(github, "brainstorming")
    target = make_skill(tmp_path / "clone" / "skills", "brainstorming")
    global_root(home).mkdir(parents=True)
    (global_root(home) / "brainstorming").symlink_to(target)

    out = run("installed", "--json")

    assert rows(out) == [
        {
            "name": "brainstorming",
            "scope": "global",
            "status": "unmanaged",
            "in_catalog": True,
            "link": str(target),
        },
    ]


def test_installed_resolves_relative_symlink_targets(home: Path, run: Callable[..., Run]) -> None:
    target = make_skill(home / "clone", "brainstorming")
    global_root(home).mkdir(parents=True)
    (global_root(home) / "brainstorming").symlink_to(Path("../../clone/brainstorming"))

    out = run("installed", "--json")

    assert out.json()[0]["link"] == str(target)


def test_installed_fails_clearly_on_a_malformed_lockfile(
    home: Path, run: Callable[..., Run]
) -> None:
    make_skill(global_root(home), "tdd")
    (global_root(home) / ".skillctl-lock.json").write_text("{not json")

    out = run("installed")

    assert out.result.exit_code == 1
    assert ".skillctl-lock.json is not a valid lockfile" in out.text.replace("\n", "")


def test_installed_inside_a_repository_also_lists_the_local_scope(
    github: FakeGitHub, home: Path, cwd: Path, run: Callable[..., Run]
) -> None:
    catalog(github, "tdd")
    make_skill(global_root(home), "tdd")
    local = make_repo(cwd)
    make_skill(local, "tdd")
    lock(local, "tdd")

    out = run("installed", "--json")

    assert [(r["scope"], r["status"]) for r in rows(out)] == [
        ("global", "unmanaged"),
        ("local", "managed"),
    ]


def test_installed_scope_option_limits_the_listing(
    github: FakeGitHub, home: Path, cwd: Path, run: Callable[..., Run]
) -> None:
    make_skill(global_root(home), "tdd")
    make_skill(make_repo(cwd), "grill-me")

    assert [r["name"] for r in rows(run("installed", "--scope", "local", "--json"))] == ["grill-me"]
    assert [r["name"] for r in rows(run("installed", "--scope", "global", "--json"))] == ["tdd"]


def test_installed_local_scope_outside_a_repository_fails(run: Callable[..., Run]) -> None:
    out = run("installed", "--scope", "local")

    assert out.result.exit_code == 1
    assert "not inside a git repository" in out.text


def test_installed_outside_a_repository_hints_at_the_local_scope(
    home: Path, run: Callable[..., Run]
) -> None:
    make_skill(global_root(home), "tdd")

    out = run("installed")

    assert out.result.exit_code == 0
    assert "Not inside a git repository" in out.text


def test_installed_reports_unknown_catalog_membership_when_github_is_unreachable(
    github: FakeGitHub, home: Path, run: Callable[..., Run]
) -> None:
    github.fail = True
    make_skill(global_root(home), "tdd")

    out = run("installed", "--json")

    assert rows(out)[0]["in_catalog"] is None


def test_installed_table(
    github: FakeGitHub,
    home: Path,
    cwd: Path,
    run: Callable[..., Run],
    snapshot: SnapshotAssertion,
) -> None:
    catalog(github, "tdd", "brainstorming", "grill-me")
    root = global_root(home)
    make_skill(root, "tdd")
    lock(root, "tdd")
    make_skill(root, "my-own")
    (root / "brainstorming").symlink_to(make_skill(home / "clone", "brainstorming"))
    local = make_repo(cwd)
    make_skill(local, "grill-me")
    lock(local, "grill-me")

    out = run("installed")

    assert out.text == snapshot
    assert out.svg("skillctl installed") == snapshot(extension_class=SVGImageSnapshotExtension)
