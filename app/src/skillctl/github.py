"""Adapter for the GitHub REST API and raw content host — the only module that speaks HTTP."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

import httpx

from skillctl.errors import SkillctlError

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
AUTH_HINT = "set GITHUB_TOKEN (or GH_TOKEN)"


class GitHubError(SkillctlError):
    """GitHub could not be reached or refused a request."""


class TreeTooLargeError(GitHubError):
    """The trees API truncated the listing, so the catalog would be incomplete."""


def token_from_env(env: Mapping[str, str]) -> str | None:
    """Pick the GitHub token from the environment.

    Args:
        env: Environment variables.

    Returns:
        `GITHUB_TOKEN`, else `GH_TOKEN`, else None; empty values count as unset.
    """
    return env.get("GITHUB_TOKEN") or env.get("GH_TOKEN") or None


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
    """Reads repository trees and file contents from GitHub.

    Every failure surfaces as a `GitHubError` with a user-facing message; httpx never leaks.
    """

    def __init__(self, http: httpx.Client, token: str | None = None) -> None:
        self._http = http
        self._auth = {"Authorization": f"Bearer {token}"} if token else {}
        self._has_token = bool(token)

    def commit(self, repo: str, ref: str) -> str:
        """Resolve `ref` to the commit SHA it currently points at.

        Args:
            repo: Repository as `owner/name`.
            ref: Branch, tag, or commit.

        Returns:
            The full 40-character commit SHA.

        Raises:
            GitHubError: The repository or ref doesn't exist, or GitHub refused the request.
        """
        response = self._get(
            f"{API}/repos/{repo}/commits/{ref}",
            f"{repo}@{ref}",
            headers={"Accept": "application/vnd.github.sha"},
        )
        return response.text.strip()

    def tree(self, repo: str, ref: str) -> list[TreeEntry]:
        """List every path in `repo` at `ref`.

        Args:
            repo: Repository as `owner/name`.
            ref: Branch, tag, or commit.

        Returns:
            All directory and file entries, recursively.

        Raises:
            TreeTooLargeError: GitHub truncated the listing.
            GitHubError: GitHub refused the request.
        """
        response = self._get(
            f"{API}/repos/{repo}/git/trees/{ref}",
            f"{repo}@{ref}",
            params={"recursive": "1"},
            headers={"Accept": "application/vnd.github+json"},
        )
        body = response.json() if _is_json(response) else None
        if not isinstance(body, dict) or not isinstance(body.get("tree"), list):
            raise GitHubError(f"Unexpected response from GitHub for the tree of {repo}@{ref}")
        if body.get("truncated"):
            raise TreeTooLargeError(
                f"{repo} is too large for the GitHub trees API; the listing was truncated"
            )
        try:
            return [
                TreeEntry(e["path"], e["type"], e["sha"], e.get("mode", "100644"))
                for e in body["tree"]
            ]
        except (KeyError, TypeError, AttributeError) as error:
            raise GitHubError(
                f"Unexpected response from GitHub for the tree of {repo}@{ref}"
            ) from error

    def read_text(self, repo: str, ref: str, path: str) -> str:
        """Read one file.

        Args:
            repo: Repository as `owner/name`.
            ref: Branch, tag, or commit.
            path: File path relative to the repository root.

        Returns:
            The file's text content.

        Raises:
            GitHubError: The file doesn't exist or GitHub refused the request.
        """
        return self.read_bytes(repo, ref, path).decode(errors="replace")

    def read_bytes(self, repo: str, ref: str, path: str) -> bytes:
        """Read one file without decoding, for scripts and images as well as text.

        Args:
            repo: Repository as `owner/name`.
            ref: Branch, tag, or commit.
            path: File path relative to the repository root.

        Returns:
            The file's raw content.

        Raises:
            GitHubError: The file doesn't exist or GitHub refused the request.
        """
        return self._get(f"{RAW}/{repo}/{ref}/{path}", f"{path} in {repo}@{ref}").content

    def _get(
        self,
        url: str,
        what: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        try:
            response = self._http.get(url, params=params, headers={**(headers or {}), **self._auth})
        except httpx.HTTPError as error:
            raise GitHubError(f"Could not reach GitHub ({type(error).__name__}: {error})") from None
        if response.is_success:
            return response
        raise GitHubError(_explain(response, what, has_token=self._has_token))


def _is_json(response: httpx.Response) -> bool:
    try:
        response.json()
    except ValueError:
        return False
    return True


def _explain(response: httpx.Response, what: str, *, has_token: bool) -> str:
    status = response.status_code
    if status in (403, 429) and response.headers.get("x-ratelimit-remaining") == "0":
        return f"GitHub API rate limit exceeded; {AUTH_HINT} to raise it."
    if status == 401:
        return "GitHub rejected the token (HTTP 401). Check GITHUB_TOKEN / GH_TOKEN."
    if status in (404, 422):
        hint = "Check the token can read it" if has_token else f"If it is private, {AUTH_HINT}"
        return f"{what} not found. {hint}."
    if status >= 500:
        return f"Could not reach GitHub (HTTP {status} for {what}). Try again later."
    return f"GitHub refused the request for {what} (HTTP {status})."
