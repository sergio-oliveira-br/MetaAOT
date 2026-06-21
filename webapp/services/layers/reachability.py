# webapp/services/layers/reachability.py

import requests

from webapp.services.layers.github_api import get_available_versions
from webapp.services.layers.version_matcher import find_best_version_match

BASE_URL = (
    "https://raw.githubusercontent.com/"
    "oracle/graalvm-reachability-metadata/master/"
    "metadata")

def metadata_exists(group_id, artifact_id, version):
    url = (
        f"{BASE_URL}/"
        f"{group_id}/"
        f"{artifact_id}/"
        f"{version}/"
        f"reachability-metadata.json")
    response = requests.get(url, timeout=10)
    return response.status_code == 200

def has_reachability_metadata(group_id, artifact_id, version):
    if metadata_exists(group_id, artifact_id, version):
        return True

    # fallback
    metadata = get_available_versions(group_id, artifact_id)
    available_versions = metadata["versions"]

    if not available_versions:
        return False

    best_match = (find_best_version_match(version, available_versions))
    if not best_match:
        return False

    return metadata_exists(group_id, artifact_id, best_match)