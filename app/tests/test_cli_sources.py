from collections.abc import Callable
from pathlib import Path

import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.image import SVGImageSnapshotExtension

from .support import Run, skill_md

SOURCES = """\
version = 1

[collections.mattpocock]
upstream = { github = "mattpocock/skills", ref = "main", path = "skills" }

[collections.superpowers]
upstream = { github = "obra/superpowers", path = "skills" }

[collections.nextflow]
upstream = { local = "~/src/nextflow-skills" }
note = "Private upstream."

[collections.misc]
note = "Internally maintained."
"""


@pytest.fixture
def catalog_repo(cwd: Path) -> Path:
    """A checkout of the catalog repository with a sources file and a few skills."""
    (cwd / ".git").mkdir()
    for path in ["mattpocock/engineering/tdd", "mattpocock/productivity/grill-me", "misc/caveman"]:
        skill = cwd / "skills" / path
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(skill_md(skill.name, "d"))
    (cwd / "skills" / "sources.toml").write_text(SOURCES)
    return cwd


def test_sources_list_shows_every_collection_with_its_upstream(
    catalog_repo: Path, run: Callable[..., Run]
) -> None:
    out = run("sources", "list", "--json")

    assert out.result.exit_code == 0
    assert out.json() == [
        {
            "collection": "mattpocock",
            "kind": "github",
            "upstream": "mattpocock/skills@main:skills",
            "skills": 2,
            "note": None,
        },
        {
            "collection": "misc",
            "kind": "none",
            "upstream": None,
            "skills": 1,
            "note": "Internally maintained.",
        },
        {
            "collection": "nextflow",
            "kind": "local",
            "upstream": "~/src/nextflow-skills",
            "skills": 0,
            "note": "Private upstream.",
        },
        {
            "collection": "superpowers",
            "kind": "github",
            "upstream": "obra/superpowers@main:skills",
            "skills": 0,
            "note": None,
        },
    ]


def test_sources_list_works_from_a_subdirectory(catalog_repo: Path, github, home: Path) -> None:
    from .support import make_runner

    out = make_runner(github, home, catalog_repo / "skills" / "misc")("sources", "list", "--json")

    assert [s["collection"] for s in out.json()] == [
        "mattpocock",
        "misc",
        "nextflow",
        "superpowers",
    ]


def test_sources_list_table(
    catalog_repo: Path, run: Callable[..., Run], snapshot: SnapshotAssertion
) -> None:
    out = run("sources", "list")

    assert out.text == snapshot
    assert out.svg("skillctl sources list") == snapshot(extension_class=SVGImageSnapshotExtension)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("[collections.x]\nupstream = { github = 'not a repo' }\n", "collections.x.upstream"),
        ("[collections.x]\nupstream = { svn = 'a/b' }\n", "collections.x.upstream"),
        ("[collections.x]\nnotes = 'typo'\n", "collections.x.notes"),
        ("[collections\n", "not valid TOML"),
    ],
)
def test_invalid_sources_file_names_the_bad_key(
    cwd: Path, run: Callable[..., Run], content: str, message: str
) -> None:
    (cwd / ".git").mkdir()
    (cwd / "skills").mkdir()
    (cwd / "skills" / "sources.toml").write_text(content)

    out = run("sources", "list")

    assert out.result.exit_code == 1
    assert message in out.text.replace("\n", "")


def test_sources_list_outside_the_catalog_repository_fails(
    cwd: Path, run: Callable[..., Run]
) -> None:
    (cwd / ".git").mkdir()

    out = run("sources", "list")

    assert out.result.exit_code == 1
    assert "skills/sources.toml" in out.text
