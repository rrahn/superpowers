from collections.abc import Callable
from pathlib import Path

import pytest

from .support import FakeGitHub, Run, git_init, skill_md, write_files

SOURCES = """\
version = 1

[collections.mattpocock]
upstream = { github = "mattpocock/skills", ref = "main", path = "skills" }

[collections.misc]
note = "Internally maintained."

[collections.misc.skills.caveman]
local = "~/dev/caveman"
"""

TDD = skill_md("tdd", "Test-driven development.")


@pytest.fixture
def catalog_repo(cwd: Path, home: Path, github: FakeGitHub) -> Path:
    """mattpocock has drifted from GitHub; misc/caveman has drifted from its local origin."""
    git_init(cwd)
    write_files(
        cwd / "skills",
        {
            "sources.toml": SOURCES,
            "mattpocock/engineering/tdd/SKILL.md": TDD,
            "mattpocock/engineering/tdd/tests.md": "# old tests\n",
            "mattpocock/engineering/tdd/legacy.md": "# legacy\n",
            "mattpocock/engineering/grill-me/SKILL.md": skill_md("grill-me", "Grill."),
            "mattpocock/misc/local-only/SKILL.md": skill_md("local-only", "Ours."),
            "misc/caveman/SKILL.md": skill_md("caveman", "Talk short."),
        },
    )
    write_files(
        home / "dev" / "caveman",
        {"SKILL.md": skill_md("caveman", "Talk shorter."), "grunt.md": b"# grunt\r\n"},
    )
    github.repo = "mattpocock/skills"
    github.files = {
        "skills/engineering/tdd/SKILL.md": TDD,
        "skills/engineering/tdd/tests.md": "# new tests\n",
        "skills/engineering/tdd/mocking.md": "# mocking\n",
        "skills/engineering/grill-me/SKILL.md": skill_md("grill-me", "Grill."),
        "skills/engineering/triage/SKILL.md": skill_md("triage", "Triage."),
        "skills/engineering/triage/run.sh": "#!/bin/sh\n",
    }
    github.executables = {"skills/engineering/triage/run.sh"}
    return cwd


def tree(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git/" not in p.as_posix()
    }


def statuses(run: Callable[..., Run]) -> dict[str, str]:
    return {
        f"{c['collection']}/{s['skill']}": s["status"]
        for c in run("upstream", "check", "--json").json()
        for s in c["skills"]
    }


def test_sync_applies_every_change_and_leaves_nothing_to_sync(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    out = run("upstream", "sync", "--yes")

    assert out.result.exit_code == 0
    skills = catalog_repo / "skills"
    tdd = skills / "mattpocock" / "engineering" / "tdd"
    assert sorted(p.name for p in tdd.iterdir()) == ["SKILL.md", "mocking.md", "tests.md"]
    assert (tdd / "tests.md").read_text() == "# new tests\n"
    assert (skills / "mattpocock" / "engineering" / "triage" / "SKILL.md").is_file()
    assert statuses(run) == {
        "mattpocock/engineering/grill-me": "unchanged",
        "mattpocock/engineering/tdd": "unchanged",
        "mattpocock/engineering/triage": "unchanged",
        "mattpocock/misc/local-only": "orphaned",
        "misc/caveman": "unchanged",
    }


def test_orphaned_skills_are_kept(catalog_repo: Path, run: Callable[..., Run]) -> None:
    run("upstream", "sync", "--yes")

    assert (catalog_repo / "skills" / "mattpocock" / "misc" / "local-only" / "SKILL.md").is_file()


def test_imported_skills_sync_byte_for_byte_from_their_origin(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    run("upstream", "sync", "misc", "--yes")

    caveman = catalog_repo / "skills" / "misc" / "caveman"
    assert (caveman / "grunt.md").read_bytes() == b"# grunt\r\n"
    assert "Talk shorter." in (caveman / "SKILL.md").read_text()


def test_executable_bits_come_from_upstream(catalog_repo: Path, run: Callable[..., Run]) -> None:
    run("upstream", "sync", "--yes")

    script = catalog_repo / "skills" / "mattpocock" / "engineering" / "triage" / "run.sh"
    assert script.stat().st_mode & 0o111


def test_dry_run_shows_the_plan_and_writes_nothing(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    before = tree(catalog_repo)

    dry = run("upstream", "sync", "--dry-run")

    assert dry.result.exit_code == 0
    assert tree(catalog_repo) == before
    assert "Dry run: nothing written." in dry.text


def test_dry_run_and_apply_print_the_same_plan(catalog_repo: Path, run: Callable[..., Run]) -> None:
    dry = run("upstream", "sync", "--dry-run").text
    applied = run("upstream", "sync", "--yes").text

    plan = dry.split("Dry run")[0]
    assert applied.startswith(plan)


def test_declining_the_confirmation_writes_nothing(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    before = tree(catalog_repo)

    out = run("upstream", "sync", input="n\n")

    assert out.result.exit_code == 1
    assert tree(catalog_repo) == before


def test_sync_can_be_limited_to_named_skills(catalog_repo: Path, run: Callable[..., Run]) -> None:
    run("upstream", "sync", "mattpocock", "engineering/triage", "--yes")

    after = statuses(run)
    assert after["mattpocock/engineering/triage"] == "unchanged"
    assert after["mattpocock/engineering/tdd"] == "changed"


def test_unknown_skill_name_fails_before_writing(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    before = tree(catalog_repo)

    out = run("upstream", "sync", "mattpocock", "engineering/nope", "--yes")

    assert out.result.exit_code == 1
    assert "engineering/nope" in out.text
    assert tree(catalog_repo) == before


def test_a_failed_download_leaves_that_skill_untouched(
    catalog_repo: Path, github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.unreadable = {"skills/engineering/tdd/mocking.md"}
    tdd = catalog_repo / "skills" / "mattpocock" / "engineering" / "tdd"
    before = tree(tdd)

    out = run("upstream", "sync", "mattpocock", "--yes")

    assert out.result.exit_code == 1
    assert tree(tdd) == before


def test_nothing_to_sync_says_so(catalog_repo: Path, run: Callable[..., Run]) -> None:
    run("upstream", "sync", "--yes")

    out = run("upstream", "sync", "--yes")

    assert out.result.exit_code == 0
    assert "Already in sync" in out.text


def test_sync_tells_the_user_to_review_and_commit(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    out = run("upstream", "sync", "--yes")

    assert "git diff" in out.text
