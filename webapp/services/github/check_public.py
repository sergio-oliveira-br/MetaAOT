# webapp/services/github/check_public.py
import os
import requests

from typing import Dict

GITHUB_API = "https://api.github.com"

class GitHubAPIError(Exception):
    pass

def _github_headers() -> Dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

def is_github_repository_public(owner: str, repo: str) -> bool:
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    resp = requests.get(url, headers=_github_headers(), timeout=10)
    if resp.status_code == 404:
        return False

    if resp.status_code != 200:
        raise GitHubAPIError(f"GitHub API error {resp.status_code}: {resp.text}")
    data = resp.json()
    # 'private' is booleano; False => public
    return not bool(data.get("private", False))
