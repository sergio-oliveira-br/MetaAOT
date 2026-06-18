# webapp/services/github/detect_maven.py

import requests

from webapp.services.github.check_public import _github_headers

GITHUB_API = "https://api.github.com"

class GitHubAPIError(Exception):
    pass

def is_java_maven_project(owner: str, repo: str) -> bool:
    # check languages
    lang_url = f"{GITHUB_API}/repos/{owner}/{repo}/languages"
    resp = requests.get(lang_url, headers=_github_headers(), timeout=10)

    if resp.status_code == 404:
        return False

    if resp.status_code != 200:
        raise GitHubAPIError(f"GitHub languages error {resp.status_code}: {resp.text}")

    languages = resp.json() or {}
    if "Java" in languages:
        return True

    #search for pom.xml via recursive tree
    repo_url = f"{GITHUB_API}/repos/{owner}/{repo}"
    r2 = requests.get(repo_url, headers=_github_headers(), timeout=10)

    if r2.status_code != 200:
        raise GitHubAPIError(f"GitHub repo error {r2.status_code}: {r2.text}")
    default_branch = r2.json().get("default_branch", "main")

    tree_url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
    r3 = requests.get(tree_url, headers=_github_headers(), timeout=20)
    if r3.status_code == 200:
        tree = r3.json().get("tree", [])
        for item in tree:
            if item.get("path", "").lower().endswith("pom.xml"):
                return True
        return False

    elif r3.status_code == 404:
        return False
    else:
        raise GitHubAPIError(f"GitHub tree error {r3.status_code}: {r3.text}")
