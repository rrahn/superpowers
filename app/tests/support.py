"""Test doubles at system boundaries: a fake GitHub served through httpx.MockTransport."""

import json
from dataclasses import dataclass, field
from hashlib import sha1
from typing import Any

import httpx
from rich.console import Console
from typer.testing import Result

from skillctl.github import GitHubClient


@dataclass
class FakeGitHub:
    """Serves one repository's files through the GitHub trees API and raw endpoints."""

    files: dict[str, str] = field(default_factory=dict)
    repo: str = "rrahn/superpowers"
    ref: str = "main"
    requests: list[httpx.Request] = field(default_factory=list)

    def _tree(self) -> dict[str, object]:
        dirs = {p.rsplit("/", i)[0] for p in self.files for i in range(1, p.count("/") + 1)}
        entries = [{"path": d, "type": "tree", "sha": _sha(d)} for d in sorted(dirs)]
        entries += [{"path": p, "type": "blob", "sha": _sha(c)} for p, c in self.files.items()]
        return {"sha": "commit-sha", "tree": entries, "truncated": False}

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        url = request.url
        if url.host == "api.github.com" and url.path == f"/repos/{self.repo}/git/trees/{self.ref}":
            return httpx.Response(200, json=self._tree())
        prefix = f"/{self.repo}/{self.ref}/"
        if url.host == "raw.githubusercontent.com" and url.path.startswith(prefix):
            path = url.path.removeprefix(prefix)
            if path in self.files:
                return httpx.Response(200, text=self.files[path])
        return httpx.Response(404, json={"message": "Not Found"})

    def client(self) -> GitHubClient:
        return GitHubClient(httpx.Client(transport=httpx.MockTransport(self.handler)))


def _sha(text: str) -> str:
    return sha1(text.encode(), usedforsecurity=False).hexdigest()


def skill_md(name: str, description: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n"


@dataclass
class Run:
    """Outcome of one CLI invocation plus everything it printed."""

    result: Result
    console: Console

    @property
    def text(self) -> str:
        return self.console.export_text(clear=False)

    def svg(self, title: str) -> str:
        return self.console.export_svg(title=title, clear=False)

    def json(self) -> Any:
        return json.loads(self.text)
