from collections.abc import Callable
from pathlib import Path

import pytest

from .support import FakeGitHub, Run, skill_md

SOURCES = """\
# Upstream sources, kept by hand and by skillctl.
version = 1

[collections.mattpocock]
upstream = { github = "mattpocock/skills", ref = "main", path = "skills" }

[collections.ai2code]
note = "Origin not recorded yet."  # fill in later
"""
ACME = ["--github", "acme/skills", "--ref", "dev", "--path", "skills"]


@pytest.fixture
def catalog_repo(cwd: Path) -> Path:
    (cwd / ".git").mkdir()
    (cwd / "skills").mkdir()
    (cwd / "skills" / "sources.toml").write_text(SOURCES, encoding="utf-8")
    return cwd


@pytest.fixture
def acme(github: FakeGitHub) -> FakeGitHub:
    """A public upstream with two skills under `skills/`."""
    github.repo, github.ref = "acme/skills", "dev"
    github.files = {
        "skills/review/SKILL.md": skill_md("review", "Review."),
        "skills/deploy/SKILL.md": skill_md("deploy", "Deploy."),
        "README.md": "# acme\n",
    }
    return github


def sources_text(repo: Path) -> str:
    return (repo / "skills" / "sources.toml").read_text(encoding="utf-8")


def upstreams(run: Callable[..., Run]) -> dict[str, str | None]:
    return {r["collection"]: r["upstream"] for r in run("sources", "list", "--json").json()}


def test_add_with_flags_records_the_upstream(
    catalog_repo: Path, acme: FakeGitHub, run: Callable[..., Run]
) -> None:
    out = run("sources", "add", "acme", *ACME)

    assert out.result.exit_code == 0
    assert "2 skills" in out.text
    assert upstreams(run)["acme"] == "acme/skills@dev:skills"


def test_add_keeps_comments_and_existing_entries(
    catalog_repo: Path, acme: FakeGitHub, run: Callable[..., Run]
) -> None:
    run("sources", "add", "acme", *ACME)

    text = sources_text(catalog_repo)
    assert text.startswith(SOURCES)
    assert "# fill in later" in text


def test_add_prompts_for_missing_values(
    catalog_repo: Path, acme: FakeGitHub, run: Callable[..., Run]
) -> None:
    out = run("sources", "add", "acme", input="acme/skills\ndev\nskills\n")

    assert out.result.exit_code == 0
    assert upstreams(run)["acme"] == "acme/skills@dev:skills"


def test_add_prompt_accepts_dot_for_the_repository_root(
    catalog_repo: Path, github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.repo = "acme/flat"
    github.files = {"review/SKILL.md": skill_md("review", "Review.")}

    out = run("sources", "add", "acme", input="acme/flat\nmain\n.\n")

    assert out.result.exit_code == 0
    assert "1 skill " in out.text
    assert upstreams(run)["acme"] == "acme/flat@main"


@pytest.mark.parametrize("typed", ["./skills/", " skills ", "skills//"])
def test_add_normalises_the_path(
    catalog_repo: Path, acme: FakeGitHub, run: Callable[..., Run], typed: str
) -> None:
    run("sources", "add", "acme", "--github", "acme/skills", "--ref", "dev", "--path", typed)

    assert upstreams(run)["acme"] == "acme/skills@dev:skills"


def test_add_keeps_windows_line_endings(
    catalog_repo: Path, acme: FakeGitHub, run: Callable[..., Run]
) -> None:
    crlf = SOURCES.replace("\n", "\r\n")
    (catalog_repo / "skills" / "sources.toml").write_bytes(crlf.encode())

    run("sources", "add", "acme", *ACME)

    assert (catalog_repo / "skills" / "sources.toml").read_bytes().startswith(crlf.encode())


def test_add_reports_an_unsupported_file_layout_instead_of_crashing(
    catalog_repo: Path, acme: FakeGitHub, run: Callable[..., Run]
) -> None:
    layout = 'version = 1\ncollections = { misc = { note = "x" } }\n'
    (catalog_repo / "skills" / "sources.toml").write_text(layout)

    out = run("sources", "add", "acme", *ACME)

    assert out.result.exit_code == 1
    assert "Cannot edit" in out.text
    assert (catalog_repo / "skills" / "sources.toml").read_text() == layout


def test_add_to_a_collection_without_upstream_keeps_its_note(
    catalog_repo: Path, github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.repo = "ai2code/skills"
    github.files = {"SKILL.md": "x", "x/SKILL.md": skill_md("x", "X.")}

    args = ["--github", "ai2code/skills", "--ref", "main", "--path", ""]

    out = run("sources", "add", "ai2code", *args)

    assert out.result.exit_code == 0
    rows = {r["collection"]: r for r in run("sources", "list", "--json").json()}
    assert rows["ai2code"]["upstream"] == "ai2code/skills@main"
    assert rows["ai2code"]["note"] == "Origin not recorded yet."


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--github", "acme/nope", "--ref", "dev", "--path", "skills"], "acme/nope@dev not found"),
        (["--github", "acme/skills", "--ref", "dev", "--path", "nowhere"], "no directory nowhere"),
        (["--github", "not-a-repo", "--ref", "dev", "--path", ""], "owner/name"),
    ],
)
def test_add_validates_before_writing_anything(
    catalog_repo: Path, acme: FakeGitHub, run: Callable[..., Run], args: list[str], message: str
) -> None:
    out = run("sources", "add", "acme", *args)

    assert out.result.exit_code == 1
    assert message in out.text.replace("\n", "")
    assert sources_text(catalog_repo) == SOURCES


def test_add_refuses_to_replace_an_upstream_without_force(
    catalog_repo: Path, github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.repo = "mattpocock/skills"
    github.files = {"skills/tdd/SKILL.md": skill_md("tdd", "T.")}
    args = ["--github", "mattpocock/skills", "--ref", "main", "--path", "skills"]

    refused = run("sources", "add", "mattpocock", *args)
    replaced = run("sources", "add", "mattpocock", *args, "--force")

    assert refused.result.exit_code == 1
    assert "already has an upstream" in refused.text
    assert replaced.result.exit_code == 0
    assert sources_text(catalog_repo).count("[collections.mattpocock]") == 1


def test_existing_upstream_is_refused_before_contacting_github(
    catalog_repo: Path, github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.offline = True
    args = ["--github", "mattpocock/skills", "--ref", "main", "--path", "skills"]

    out = run("sources", "add", "mattpocock", *args)

    assert "already has an upstream" in out.text
    assert github.requests == []
