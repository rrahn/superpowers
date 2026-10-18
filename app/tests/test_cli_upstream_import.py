import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from .support import FakeGitHub, Run, skill_md

SOURCES = """\
version = 1

[collections.misc]
note = "Internally maintained."  # keep me
"""


def write(root: Path, files: dict[str, str]) -> None:
    for path, content in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(content.encode())


@pytest.fixture
def catalog_repo(cwd: Path) -> Path:
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "init", "-q", str(cwd)], check=True, env=clean_env)  # noqa: S603, S607
    write(
        cwd / "skills",
        {"sources.toml": SOURCES, "misc/handwritten/SKILL.md": skill_md("handwritten", "Ours.")},
    )
    return cwd


@pytest.fixture
def origin(home: Path) -> Path:
    """An internally maintained skill living in another checkout under the home directory."""
    skill = home / "dev" / "team-skills" / "caveman"
    write(
        skill,
        {
            "SKILL.md": skill_md("caveman", "Talk short."),
            "examples/grunt.md": "# grunt\n",
            ".DS_Store": "junk",
            "__pycache__/x.pyc": "bytecode",
        },
    )
    return skill


def sources_text(repo: Path) -> str:
    return (repo / "skills" / "sources.toml").read_text()


def misc_skills(run: Callable[..., Run]) -> dict[str, dict[str, object]]:
    report = {c["collection"]: c for c in run("upstream", "check", "--json").json()}
    return {s["skill"]: s for s in report["misc"]["skills"]}


def test_import_copies_the_skill_into_the_collection(
    catalog_repo: Path, origin: Path, run: Callable[..., Run]
) -> None:
    out = run("upstream", "import", str(origin), "--collection", "misc")

    assert out.result.exit_code == 0
    imported = catalog_repo / "skills" / "misc" / "caveman"
    files = sorted(p.relative_to(imported).as_posix() for p in imported.rglob("*") if p.is_file())
    assert files == ["SKILL.md", "examples/grunt.md"]


def test_import_records_provenance_with_home_kept_as_tilde(
    catalog_repo: Path, origin: Path, run: Callable[..., Run]
) -> None:
    run("upstream", "import", str(origin), "--collection", "misc")

    text = sources_text(catalog_repo)
    assert "[collections.misc.skills.caveman]" in text
    assert 'local = "~/dev/team-skills/caveman"' in text
    assert "# keep me" in text


def test_imported_skill_is_unchanged_until_its_origin_changes(
    catalog_repo: Path, origin: Path, run: Callable[..., Run]
) -> None:
    run("upstream", "import", str(origin), "--collection", "misc")
    assert misc_skills(run)["caveman"]["status"] == "unchanged"

    (origin / "SKILL.md").write_text(skill_md("caveman", "Talk even shorter."))
    (origin / "examples" / "roar.md").write_text("# roar\n")

    skill = misc_skills(run)["caveman"]
    assert (skill["status"], skill["added"], skill["modified"]) == (
        "changed",
        ["examples/roar.md"],
        ["SKILL.md"],
    )


def test_missing_origin_is_unavailable_and_the_skill_is_kept(
    catalog_repo: Path, origin: Path, run: Callable[..., Run]
) -> None:
    run("upstream", "import", str(origin), "--collection", "misc")
    for path in sorted(origin.rglob("*"), reverse=True):
        path.unlink() if path.is_file() else path.rmdir()
    origin.rmdir()

    skill = misc_skills(run)["caveman"]

    assert skill["status"] == "unavailable"
    assert "~/dev/team-skills/caveman" in str(skill["reason"])
    assert (catalog_repo / "skills" / "misc" / "caveman" / "SKILL.md").is_file()


def test_skills_without_provenance_are_not_reported(
    catalog_repo: Path, origin: Path, run: Callable[..., Run]
) -> None:
    run("upstream", "import", str(origin), "--collection", "misc")

    assert list(misc_skills(run)) == ["caveman"]


def test_import_rejects_a_skill_md_whose_name_does_not_match_its_directory(
    catalog_repo: Path, home: Path, run: Callable[..., Run]
) -> None:
    wrong = home / "wrong-dir"
    write(wrong, {"SKILL.md": skill_md("caveman", "Mismatch.")})

    out = run("upstream", "import", str(wrong), "--collection", "misc")

    assert out.result.exit_code == 1
    assert "name 'caveman' does not match" in out.text.replace("\n", "")
    assert not (catalog_repo / "skills" / "misc" / "wrong-dir").exists()


def test_import_refuses_to_overwrite_without_force(
    catalog_repo: Path, home: Path, run: Callable[..., Run]
) -> None:
    other = home / "elsewhere" / "handwritten"
    write(other, {"SKILL.md": skill_md("handwritten", "Theirs.")})

    refused = run("upstream", "import", str(other), "--collection", "misc")
    replaced = run("upstream", "import", str(other), "--collection", "misc", "--force")

    assert refused.result.exit_code == 1
    assert "already exists" in refused.text
    assert replaced.result.exit_code == 0
    imported = catalog_repo / "skills" / "misc" / "handwritten" / "SKILL.md"
    assert "Theirs." in imported.read_text()


def test_import_into_an_undeclared_collection_declares_it(
    catalog_repo: Path, origin: Path, run: Callable[..., Run]
) -> None:
    out = run("upstream", "import", str(origin), "--collection", "team")

    assert out.result.exit_code == 0
    rows = {r["collection"]: r for r in run("sources", "list", "--json").json()}
    assert rows["team"]["skills"] == 1


def test_import_works_offline(
    catalog_repo: Path, origin: Path, github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.offline = True

    out = run("upstream", "import", str(origin), "--collection", "misc")

    assert out.result.exit_code == 0
    assert github.requests == []
