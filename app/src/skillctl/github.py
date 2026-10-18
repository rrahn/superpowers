"""Adapter for the GitHub REST API and raw content host — the only module that speaks HTTP."""

from dataclasses import dataclass
from typing import Literal

import httpx

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"


@dataclass(frozen=True)
class TreeEntry:
    """One path in a git tree: a directory, a file, or a submodule."""

    path: str
    type: Literal["tree", "blob", "commit"]
    sha: str
    mode: str = "100644"

    @property
    def executable(self) -> bool:
        """Whether git records this file as executable."""
        return self.mode == "100755"

    @property
    def symlink(self) -> bool:
        """Whether git records this entry as a symbolic link."""
        return self.mode == "120000"


class GitHubClient:
    """Reads repository trees and file contents from GitHub."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def commit(self, repo: str, ref: str) -> str:
        """Resolve `ref` to the commit SHA it currently points at.

        Args:
            repo: Repository as `owner/name`.
            ref: Branch, tag, or commit.

        Returns:
            The full 40-character commit SHA.
        """
        response = self._http.get(
            f"{API}/repos/{repo}/commits/{ref}",
            headers={"Accept": "application/vnd.github.sha"},
        )
        response.raise_for_status()
        return response.text.strip()

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
            TreeEntry(path=e["path"], type=e["type"], sha=e["sha"], mode=e.get("mode", "100644"))
            for e in response.json()["tree"]
        ]

    def read_text(self, repo: str, ref: str, path: str) -> str:
        """Read one file.

        Args:
            repo: Repository as `owner/name`.
            ref: Branch, tag, or commit.
            path: File path relative to the repository root.

        Returns:
            The file's text content.
        """
        return self.read_bytes(repo, ref, path).decode()

    def read_bytes(self, repo: str, ref: str, path: str) -> bytes:
        """Read one file without decoding, for scripts and images as well as text.

        Args:
            repo: Repository as `owner/name`.
            ref: Branch, tag, or commit.
            path: File path relative to the repository root.

        Returns:
            The file's raw content.
        """
        response = self._http.get(f"{RAW}/{repo}/{ref}/{path}")
        response.raise_for_status()
        return response.content
