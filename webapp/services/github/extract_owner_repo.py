# webapp/services/github/extract_owner_repo.py

from typing import Optional, Tuple
from urllib.parse import urlparse

class GitHubAPIError(Exception):
    pass

def extract_owner_repo_from_url(url: str) -> Optional[Tuple[str, str]]:

    try:
        p = urlparse(url)
        if p.netloc not in ("github.com", "www.github.com"):
            return None

        parts = [seg for seg in p.path.split("/") if seg]
        if len(parts) < 2:
            return None

        owner, repo = parts[0], parts[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo

    except Exception:
        return None
