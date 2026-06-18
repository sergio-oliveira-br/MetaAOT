# webapp/services/analysis/sbom_loader.py

from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

class SBOMError(Exception):
    pass

def load_sbom_from_repo(owner: str, repo: str, http_get: Optional[Callable] = None) -> Optional[str]:
    """
    Tries to locate and return the content of SBOM CycloneDX in the repository.
    """
    http_get = http_get or __import__("requests").get
    candidates = [
        "cyclonedx.xml",
        "bom.xml",
        "sbom.xml",
        "cyclonedx.json",
        "bom.json",
    ]
    base_url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/"
    for name in candidates:
        url = base_url + name
        logger.debug("Trying SBOM candidate %s", url)

        try:
            resp = http_get(url, timeout=10)
        except Exception:
            logger.exception("Network error when fetching SBOM %s/%s -> %s", owner, repo, name)
            continue

        if getattr(resp, "status_code", None) == 200 and getattr(resp, "text", None):
            logger.info("SBOM found: %s", name)
            return resp.text

        logger.debug("SBOM not found %s (status %s)", name, getattr(resp, "status_code", None))
    logger.info("No SBOM found for %s/%s", owner, repo)
    return None
