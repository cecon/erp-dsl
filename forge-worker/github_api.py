"""GitHub REST API helper for Forge Worker."""
from __future__ import annotations

import httpx


class GitHubAPI:
    """Thin wrapper around GitHub REST API v3."""

    _BASE = "https://api.github.com"

    def __init__(self, token: str, repo: str) -> None:
        self.token = token
        self.repo = repo  # "org/repo"
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def create_pull_request(
        self,
        head: str,
        base: str,
        title: str,
        body: str,
    ) -> str:
        """Open a PR and return its HTML URL."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._BASE}/repos/{self.repo}/pulls",
                headers=self._headers,
                json={
                    "title": title,
                    "body": body,
                    "head": head,
                    "base": base,
                    "draft": False,
                },
            )
            if resp.status_code == 422:
                # PR already exists OR no diff between branches
                data = resp.json()
                err_str = str(data.get("errors", ""))
                if "already exists" in err_str:
                    existing = await self._find_pr(head, base)
                    return existing or "PR já existe"
                if "No commits between" in err_str or not data.get("errors"):
                    # Branch was pushed but had no code changes
                    return f"Sem alterações para PR (branch {head} idêntica a {base})"
                resp.raise_for_status()
            else:
                resp.raise_for_status()
            return resp.json()["html_url"]

    async def _find_pr(self, head: str, base: str) -> str | None:
        """Find an existing PR for the given head branch."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self._BASE}/repos/{self.repo}/pulls",
                headers=self._headers,
                params={"head": f"{self.repo.split('/')[0]}:{head}", "base": base, "state": "open"},
            )
            resp.raise_for_status()
            prs = resp.json()
            return prs[0]["html_url"] if prs else None

    async def get_default_branch(self) -> str:
        """Return the default branch name."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self._BASE}/repos/{self.repo}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json().get("default_branch", "main")
