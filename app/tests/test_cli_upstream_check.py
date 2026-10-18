from collections.abc import Callable
from pathlib import Path

import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.image import SVGImageSnapshotExtension

from .support import FakeGitHub, Run, skill_md

SOURCES = """\
version = 1

[collections.mattpocock]
upstream = { github = "mattpocock/skills", ref = "main", path = "skills" }

[collections.gone]
upstream = { github = "someone/deleted-repo", path = "skills" }

[collections.misc]
note = "Internally maintained."
"""

TDD = skill_md("tdd", "Test-driven development.")


def write(root: Path, files: dict[str, str]) -> None:
    for path, content in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(content)


@pytest.fixture
def catalog_repo(cwd: Path, github: FakeGitHub) -> Path:
    """This repo's mattpocock collection has drifted from its upstream in every way."""
    (cwd / ".git").mkdir()
    write(
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
    github.repo = "mattpocock/skills"
    github.files = {
        "skills/engineering/tdd/SKILL.md": TDD,
        "skills/engineering/tdd/tests.md": "# new tests\n",
        "skills/engineering/tdd/mocking.md": "# mocking\n",
        "skills/engineering/grill-me/SKILL.md": skill_md("grill-me", "Grill."),
        "skills/engineering/triage/SKILL.md": skill_md("triage", "Triage."),
        "README.md": "# skills\n",
    }
    return cwd


def by_skill(out: Run) -> dict[str, dict[str, object]]:
    report = {c["collection"]: c for c in out.json()}
    return {s["skill"]: s for s in report["mattpocock"]["skills"]}


def test_check_reports_file_level_changes(catalog_repo: Path, run: Callable[..., Run]) -> None:
    out = run("upstream", "check", "--json")

    assert out.result.exit_code == 0
    assert by_skill(out)["engineering/tdd"] == {
        "skill": "engineering/tdd",
        "status": "changed",
        "added": ["mocking.md"],
        "modified": ["tests.md"],
        "deleted": ["legacy.md"],
    }


def test_check_reports_new_upstream_skills(catalog_repo: Path, run: Callable[..., Run]) -> None:
    skill = by_skill(run("upstream", "check", "--json"))["engineering/triage"]

    assert (skill["status"], skill["added"]) == ("new", ["SKILL.md"])


def test_check_flags_orphaned_skills(catalog_repo: Path, run: Callable[..., Run]) -> None:
    skill = by_skill(run("upstream", "check", "--json"))["misc/local-only"]

    assert skill["status"] == "orphaned"


def test_unchanged_skills_are_reported_as_unchanged(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    skill = by_skill(run("upstream", "check", "--json"))["engineering/grill-me"]

    assert skill["status"] == "unchanged"


def test_an_unreachable_upstream_does_not_abort_the_check(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    out = run("upstream", "check", "--json")

    report = {c["collection"]: c for c in out.json()}
    assert out.result.exit_code == 0
    assert report["gone"]["status"] == "unavailable"
    assert "someone/deleted-repo@main not found" in report["gone"]["reason"]
    assert report["mattpocock"]["status"] == "checked"


def test_collections_without_upstream_are_skipped(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    report = {c["collection"]: c for c in run("upstream", "check", "--json").json()}

    assert report["misc"]["status"] == "no upstream"


def test_check_can_be_limited_to_one_collection(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    out = run("upstream", "check", "mattpocock", "--json")

    assert [c["collection"] for c in out.json()] == ["mattpocock"]


def test_check_unknown_collection_fails(catalog_repo: Path, run: Callable[..., Run]) -> None:
    out = run("upstream", "check", "nope")

    assert out.result.exit_code == 1
    assert "No collection 'nope'" in out.text


def test_check_never_writes_to_the_working_tree(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    before = sorted(p.as_posix() for p in (catalog_repo / "skills").rglob("*"))

    run("upstream", "check")

    assert sorted(p.as_posix() for p in (catalog_repo / "skills").rglob("*")) == before


def test_check_report(
    catalog_repo: Path, run: Callable[..., Run], snapshot: SnapshotAssertion
) -> None:
    out = run("upstream", "check")

    assert out.text == snapshot
    assert out.svg("skillctl upstream check") == snapshot(extension_class=SVGImageSnapshotExtension)
