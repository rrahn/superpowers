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
