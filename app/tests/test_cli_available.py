from collections.abc import Callable

from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.image import SVGImageSnapshotExtension

from .support import FakeGitHub, Run, skill_md


def seed(github: FakeGitHub) -> None:
    github.files = {
        "README.md": "# superpowers\n",
        "skills/mattpocock/engineering/tdd/SKILL.md": skill_md("tdd", "Test-driven development."),
        "skills/mattpocock/engineering/tdd/tests.md": "# Good and bad tests\n",
        "skills/superpowers/brainstorming/SKILL.md": skill_md(
            "brainstorming", "Turn ideas into designs."
        ),
        "skills/SKILL.md": skill_md("python-uv", "Stray file whose directory is not its name."),
    }


def test_available_lists_catalog_skills_with_collection_and_description(
    github: FakeGitHub, run: Callable[..., Run], snapshot: SnapshotAssertion
) -> None:
    seed(github)

    out = run("available")

    assert out.result.exit_code == 0
    assert out.text == snapshot
    assert out.svg("skillctl available") == snapshot(extension_class=SVGImageSnapshotExtension)


def test_available_skips_skill_md_whose_name_does_not_match_its_directory(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    seed(github)

    out = run("available")

    assert "brainstorming" in out.text
    assert "python-uv" not in out.text


def names(out: Run) -> list[str]:
    return [row["name"] for row in out.json()]


def test_available_filters_by_collection(github: FakeGitHub, run: Callable[..., Run]) -> None:
    seed(github)

    out = run("available", "--collection", "superpowers", "--json")

    assert names(out) == ["brainstorming"]


def test_available_search_matches_name_or_description_case_insensitively(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    seed(github)

    assert names(run("available", "--search", "TDD", "--json")) == ["tdd"]
    assert names(run("available", "--search", "ideas", "--json")) == ["brainstorming"]


def test_available_combines_collection_and_search(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    seed(github)

    out = run("available", "--collection", "superpowers", "--search", "tdd", "--json")

    assert names(out) == []


def test_available_reads_descriptions_containing_dashes_and_folded_lines(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.files = {
        "skills/misc/caveman/SKILL.md": (
            "---\nname: caveman\ndescription: >\n  Talk short --- like caveman.\n"
            "  Save tokens.\n---\n\nBody with --- rule.\n"
        )
    }

    out = run("available", "--json")

    assert out.json()[0]["description"] == "Talk short --- like caveman. Save tokens."


def test_available_json_lists_skill_objects(github: FakeGitHub, run: Callable[..., Run]) -> None:
    seed(github)

    out = run("available", "--json")

    assert out.json() == [
        {
            "name": "tdd",
            "collection": "mattpocock",
            "description": "Test-driven development.",
            "path": "skills/mattpocock/engineering/tdd",
        },
        {
            "name": "brainstorming",
            "collection": "superpowers",
            "description": "Turn ideas into designs.",
            "path": "skills/superpowers/brainstorming",
        },
    ]
