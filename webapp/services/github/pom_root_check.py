# webapp/services/github/pom_root_check.py
import requests

from webapp.services.github.check_public import GITHUB_API, _github_headers

class GitHubAPIError(Exception):
    pass

def is_pom_in_root(owner: str, repo: str) -> bool:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/pom.xml"
    resp = requests.get(url, headers=_github_headers(), timeout=10)

    if resp.status_code == 200:
        return True

    if resp.status_code == 404:
        return False

    raise GitHubAPIError(f"GitHub contents error {resp.status_code}: {resp.text}")