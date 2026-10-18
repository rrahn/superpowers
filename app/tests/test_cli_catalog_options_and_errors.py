from collections.abc import Callable

import pytest

from .support import FakeGitHub, Run, skill_md


def seed(github: FakeGitHub) -> None:
    github.files = {"skills/team/review/SKILL.md": skill_md("review", "Team review.")}


def test_repo_and_ref_options_select_another_catalog(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.repo, github.ref = "acme/skills", "dev"
    seed(github)

    out = run("--repo", "acme/skills", "--ref", "dev", "available", "--json")

    assert [s["name"] for s in out.json()] == ["review"]


def test_repo_and_ref_come_from_the_environment(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.repo, github.ref = "acme/skills", "dev"
    seed(github)

    out = run("install", "review", env={"SKILLCTL_REPO": "acme/skills", "SKILLCTL_REF": "dev"})

    assert out.result.exit_code == 0
    assert "Installed review" in out.text


def test_installed_checks_catalog_membership_against_the_selected_repo(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.repo = "acme/skills"
    seed(github)
    run("--repo", "acme/skills", "install", "review")

    out = run("--repo", "acme/skills", "installed", "--json")

    assert out.json()[0]["in_catalog"] is True


@pytest.mark.parametrize("command", [["available"], ["install", "review"]])
def test_rate_limit_suggests_setting_a_token(
    github: FakeGitHub, run: Callable[..., Run], command: list[str]
) -> None:
    github.rate_limited = True

    out = run(*command)

    assert out.result.exit_code == 1
    assert "rate limit" in out.text
    assert "GITHUB_TOKEN" in out.text


def test_unknown_repository_names_the_repo_and_ref(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    out = run("--repo", "nobody/nothing", "available")

    assert out.result.exit_code == 1
    assert "nobody/nothing@main not found" in out.text.replace("\n", "")


def test_network_failure_is_one_line_not_a_traceback(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.offline = True

    out = run("available")

    assert out.result.exit_code == 1
    assert "Could not reach GitHub" in out.text


def test_truncated_tree_is_reported_instead_of_listing_partially(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    seed(github)
    github.truncated = True

    out = run("available")

    assert out.result.exit_code == 1
    assert "too large" in out.text


def test_installed_warns_when_catalog_membership_is_unknown(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    github.truncated = True

    out = run("installed")

    assert out.result.exit_code == 0
    assert "Warning:" in out.text
    assert "too large" in out.text


def test_one_unreadable_skill_md_is_reported_with_its_path(
    github: FakeGitHub, run: Callable[..., Run]
) -> None:
    seed(github)
    github.unreadable = {"skills/team/review/SKILL.md"}

    out = run("available")

    assert out.result.exit_code == 1
    assert "skills/team/review/SKILL.md" in out.text.replace("\n", "")
