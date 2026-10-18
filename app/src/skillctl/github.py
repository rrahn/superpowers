"""Adapter for the GitHub REST API and raw content host — the only module that speaks HTTP."""

from dataclasses import dataclass

import httpx

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"


@dataclass(frozen=True)
class TreeEntry:
    """One path in a git tree: a directory (`tree`) or a file (`blob`)."""

    path: str
    type: str
    sha: str


class GitHubClient:
    """Reads repository trees and file contents from GitHub."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def tree(self, repo: str, ref: str) -> list[TreeEntry]:
        """List every path in `repo` at `ref`.

        Args:
            repo: Repository as `owner/name`.
            ref: Branch, tag, or commit.

        Returns:
            All directory and file entries, recursively.
        """
        response = self._http.get(
            f"{API}/repos/{repo}/git/trees/{ref}",
            params={"recursive": "1"},
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        return [
            TreeEntry(path=e["path"], type=e["type"], sha=e["sha"]) for e in response.json()["tree"]
        ]

    def read_text(self, repo: str, ref: str, path: str) -> str:
        """Return the text content of `path` in `repo` at `ref`."""
        response = self._http.get(f"{RAW}/{repo}/{ref}/{path}")
        response.raise_for_status()
        return response.text
