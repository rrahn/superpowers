"""Test support: a fake GitHub behind httpx.MockTransport and a CLI runner wired to it."""

import io
import json
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from hashlib import sha1
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console
from typer.testing import CliRunner, Result

from skillctl.cli import Dependencies, create_app
from skillctl.github import GitHubClient
from skillctl.upstream import git_blob_sha


@dataclass
class FakeGitHub:
    """Serves one repository: `ref` resolves to `commit`; trees and files exist only at `commit`."""

    files: dict[str, str] = field(default_factory=dict)
    repo: str = "rrahn/superpowers"
    ref: str = "main"
    commit: str = "c0ffee0000000000000000000000000000000000"
    requests: list[httpx.Request] = field(default_factory=list)
    fail: bool = False
    rate_limited: bool = False
    offline: bool = False
    truncated: bool = False
    unreadable: set[str] = field(default_factory=set)
    executables: set[str] = field(default_factory=set)
    symlinks: set[str] = field(default_factory=set)

    def _tree(self) -> dict[str, object]:
        dirs = {p.rsplit("/", i)[0] for p in self.files for i in range(1, p.count("/") + 1)}
        entries = [
            {"path": d, "type": "tree", "sha": _sha(d), "mode": "040000"} for d in sorted(dirs)
        ]
        entries += [
            {
                "path": p,
                "type": "blob",
                "sha": git_blob_sha(c.encode()),
                "mode": "120000"
                if p in self.symlinks
                else "100755"
                if p in self.executables
                else "100644",
            }
            for p, c in self.files.items()
        ]
        return {"sha": _sha("root"), "tree": entries, "truncated": self.truncated}

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.offline:
            raise httpx.ConnectError("nodename nor servname provided", request=request)
        if self.rate_limited:
            return httpx.Response(
                403,
                headers={"x-ratelimit-remaining": "0"},
                json={"message": "API rate limit exceeded"},
            )
        if self.fail:
            return httpx.Response(503, json={"message": "Service Unavailable"})
        url = request.url
        api = f"/repos/{self.repo}"
        if url.host == "api.github.com" and url.path == f"{api}/commits/{self.ref}":
            return httpx.Response(200, text=self.commit)
        if url.host == "api.github.com" and url.path == f"{api}/git/trees/{self.commit}":
            return httpx.Response(200, json=self._tree())
        prefix = f"/{self.repo}/{self.commit}/"
        if url.host == "raw.githubusercontent.com" and url.path.startswith(prefix):
            path = url.path.removeprefix(prefix)
            if path in self.files and path not in self.unreadable:
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


def make_runner(github: FakeGitHub, home: Path, cwd: Path) -> Callable[..., Run]:
    """Build a CLI invoker against the fake GitHub, recording output on a fixed-width console."""

    def _run(*args: str, env: dict[str, str] | None = None, input: str | None = None) -> Run:
        console = Console(
            file=io.StringIO(),
            width=100,
            record=True,
            force_terminal=True,
            color_system="truecolor",
        )
        deps = Dependencies(github=github.client(), console=console, home=home, cwd=cwd)
        hermetic = {"SKILLCTL_REPO": None, "SKILLCTL_REF": None}
        result = CliRunner().invoke(
            create_app(deps), list(args), env={**hermetic, **(env or {})}, input=input
        )
        if result.exception and not isinstance(result.exception, SystemExit):
            raise result.exception
        return Run(result, console)

    return _run


def write_files(root: Path, files: dict[str, str | bytes]) -> None:
    """Create `files` (relative path → content) under `root`."""
    for path, content in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(content if isinstance(content, bytes) else content.encode())


def git_init(path: Path) -> None:
    """Make `path` a real git repository, immune to GIT_* variables set by git hooks."""
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "init", "-q", str(path)], check=True, env=clean_env)  # noqa: S603, S607
