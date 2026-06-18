# webapp/services/github/fetch_file.py
from typing import Optional

import requests

from webapp.services.github.check_public import GITHUB_API, _github_headers, GitHubAPIError

class FetchError(Exception):
    pass


def fetch_file_content(owner: str, repo: str, path: str) -> Optional[str]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=_github_headers(), timeout=10)

    if resp.status_code == 200:
        data = resp.json()
        import base64
        content_b64 = data.get("content", "")

        try:
            return base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except FetchError:
            return None

    if resp.status_code == 404:
        return None
    raise GitHubAPIError(f"GitHub contents error {resp.status_code}: {resp.text}")