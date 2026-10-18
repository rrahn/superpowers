import httpx

from skillctl.github import GitHubClient, TreeEntry


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
