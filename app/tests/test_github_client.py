import httpx
import pytest

from skillctl.github import GitHubClient, GitHubError, TreeEntry, token_from_env


def client_returning(response: httpx.Response, seen: list[httpx.Request]) -> GitHubClient:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return response

    return GitHubClient(httpx.Client(transport=httpx.MockTransport(handler)))


def test_tree_requests_the_recursive_git_tree_of_the_ref() -> None:
    seen: list[httpx.Request] = []
    body = {"tree": [{"path": "skills", "type": "tree", "sha": "abc", "mode": "040000"}]}
    client = client_returning(httpx.Response(200, json=body), seen)

    entries = client.tree("rrahn/superpowers", "main")

    assert entries == [TreeEntry(path="skills", type="tree", sha="abc", mode="040000")]
    assert str(seen[0].url) == (
        "https://api.github.com/repos/rrahn/superpowers/git/trees/main?recursive=1"
    )
    assert seen[0].headers["accept"] == "application/vnd.github+json"


def test_commit_resolves_a_ref_to_its_sha() -> None:
    seen: list[httpx.Request] = []
    client = client_returning(httpx.Response(200, text="b0292e7" + "0" * 33), seen)

    assert client.commit("rrahn/superpowers", "main") == "b0292e7" + "0" * 33
    assert str(seen[0].url) == "https://api.github.com/repos/rrahn/superpowers/commits/main"
    assert seen[0].headers["accept"] == "application/vnd.github.sha"


def test_read_text_fetches_from_the_raw_content_host() -> None:
    seen: list[httpx.Request] = []
    client = client_returning(httpx.Response(200, text="---\nname: tdd\n---\n"), seen)

    text = client.read_text("rrahn/superpowers", "main", "skills/x/tdd/SKILL.md")

    assert text == "---\nname: tdd\n---\n"
    assert str(seen[0].url) == (
        "https://raw.githubusercontent.com/rrahn/superpowers/main/skills/x/tdd/SKILL.md"
    )


def test_token_is_sent_as_bearer_auth_to_api_and_raw_hosts() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, text="abc")

    client = GitHubClient(httpx.Client(transport=httpx.MockTransport(handler)), token="s3cret")
    client.commit("o/r", "main")
    client.read_text("o/r", "main", "f")

    assert [r.headers["authorization"] for r in seen] == ["Bearer s3cret", "Bearer s3cret"]


def test_errors_never_include_the_token() -> None:
    client = GitHubClient(
        httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(401))),
        token="s3cret",
    )

    with pytest.raises(GitHubError) as error:
        client.commit("o/r", "main")

    assert "s3cret" not in str(error.value)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="<html>not json</html>"),
        httpx.Response(200, json=["a list"]),
        httpx.Response(200, json={"no": "tree"}),
    ],
)
def test_tree_reports_unexpected_responses(response: httpx.Response) -> None:
    client = client_returning(response, [])

    with pytest.raises(GitHubError, match="Unexpected response"):
        client.tree("o/r", "main")


def test_redirects_to_another_host_do_not_carry_the_token() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.host == "raw.githubusercontent.com":
            return httpx.Response(302, headers={"location": "https://elsewhere.example/f"})
        return httpx.Response(200, text="ok")

    http = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    GitHubClient(http, token="s3cret").read_text("o/r", "main", "f")

    assert seen[-1].url.host == "elsewhere.example"
    assert "authorization" not in seen[-1].headers


def test_network_errors_never_include_the_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    client = GitHubClient(httpx.Client(transport=httpx.MockTransport(handler)), token="s3cret")

    with pytest.raises(GitHubError) as error:
        client.commit("o/r", "main")

    assert "s3cret" not in str(error.value)


def test_not_found_with_a_token_does_not_suggest_setting_one() -> None:
    client = GitHubClient(
        httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(404))),
        token="s3cret",
    )

    with pytest.raises(GitHubError) as error:
        client.commit("o/r", "main")

    assert "set GITHUB_TOKEN" not in str(error.value)


@pytest.mark.parametrize(
    ("env", "token"),
    [
        ({"GITHUB_TOKEN": "a", "GH_TOKEN": "b"}, "a"),
        ({"GH_TOKEN": "b"}, "b"),
        ({"GITHUB_TOKEN": ""}, None),
        ({}, None),
    ],
)
def test_token_from_env_prefers_github_token(env: dict[str, str], token: str | None) -> None:
    assert token_from_env(env) == token
