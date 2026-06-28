# webapp/services/layers/repository_client.py

import logging
import requests

from functools import lru_cache

BASE_URL = (
    "https://raw.githubusercontent.com/"
    "oracle/graalvm-reachability-metadata/master/"
    "metadata"
)
TIMEOUT = 10
logger = logging.getLogger(__name__)

class RepositoryClient:

    @staticmethod
    @lru_cache(maxsize=2048)
    def load_index(group_id: str, artifact_id: str):
        url = (
            f"{BASE_URL}/"
            f"{group_id}/"
            f"{artifact_id}/"
            "index.json"
        )

        logger.info("[RepositoryClient] Loading index: %s", url)
        try:
            response = requests.get(url, timeout=TIMEOUT)
        except Exception:
            logger.exception("[RepositoryClient] Network error")
            return {
                "status": "ERROR",
                "data": None
            }

        logger.info("[RepositoryClient] HTTP status=%s",response.status_code)

        if response.status_code == 404:
            return None

        if response.status_code != 200:
            logger.warning("[RepositoryClient] Unexpected HTTP status=%s",response.status_code)
            return None

        try:
            return response.json()
        except Exception:
            logger.exception("[RepositoryClient] Invalid JSON")
            return None

    @staticmethod
    def metadata_exists(group_id, artifact_id, version):
        url = (
            f"{BASE_URL}/"
            f"{group_id}/"
            f"{artifact_id}/"
            f"{version}/"
            "reachability-metadata.json"
        )
        logger.info("[RepositoryClient] Checking metadata: %s",url)

        response = requests.get(url, timeout=TIMEOUT)
        exists = response.status_code == 200

        logger.info("[RepositoryClient] Metadata exists: %s",exists)
        return exists