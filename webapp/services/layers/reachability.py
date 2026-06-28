# webapp/services/layers/reachability.py

import logging
import requests

from functools import lru_cache
from webapp.services.layers.github_api import get_available_versions
from webapp.services.layers.version_matcher import find_best_version_match

BASE_URL = (
    "https://raw.githubusercontent.com/"
    "oracle/graalvm-reachability-metadata/master/"
    "metadata")

TIMEOUT = 10
logger = logging.getLogger(__name__)

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
    logger.info("[Repository] Looking for %s:%s", group_id, artifact_id)
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


@lru_cache(maxsize=2048)
def load_repository_metadata(group_id: str, artifact_id: str):
    url = (
        f"{BASE_URL}/"
        f"{group_id}/"
        f"{artifact_id}/"
        "index.json"
    )

    logger.info("[Repository] Looking for %s:%s", group_id, artifact_id)
    logger.info("[Repository] URL=%s", url)
    response = requests.get(url, timeout=TIMEOUT)

    response.raise_for_status()

    if response.status_code == 404:
        logger.info("[Repository] Metadata NOT FOUND.")
        return None

    response.raise_for_status()
    logger.info("[Repository] Metadata FOUND.")
    return response.json()

def interpret_metadata(metadata, version):
    logger.info("[Repository] Interpreting metadata...")
    if metadata is None:
        logger.info("[Repository] No metadata available.")
        return {
            "status": "NO_EVIDENCE",
            "confidence": "LOW",
            "reason": "Repository metadata not found"
        }

    if not isinstance(metadata, list):
        logger.warning(
            "[Repository] Unexpected JSON type: %s",
            type(metadata)
        )
        return {
            "status": "NO_EVIDENCE",
            "confidence": "LOW",
            "reason": "Unexpected metadata format"
        }

    if len(metadata) == 0:
        logger.warning("[Repository] Empty metadata list.")
        return {
            "status": "NO_EVIDENCE",
            "confidence": "LOW",
            "reason": "Empty metadata"
        }

    # Iterate through every metadata entry.
    for entry in metadata:
        # Case 1: GraalVM explicitly says the artifact should not be analysed.
        if entry.get("not-for-native-image", False):
            logger.info("[Repository] Artifact marked as NOT_APPLICABLE.")
            return {
                "status": "NOT_APPLICABLE",
                "confidence": "HIGH",
                "reason": entry.get(
                    "reason",
                    "Officially marked as not applicable."
                )
            }

        tested_versions = entry.get("tested-versions", [])

        # Case 2: Exact version officially tested.
        if version in tested_versions:
            logger.info("[Repository] Version %s officially tested.",version)
            return {
                "status": "OFFICIAL_METADATA",
                "confidence": "HIGH",
                "reason": "Official Reachability Metadata",
                "tested_versions": tested_versions,
                "metadata_version": entry.get("metadata-version")
            }
        # Case 3: Metadata exists but version not listed.
        if tested_versions:
            logger.info("[Repository] Metadata exists, but %s not explicitly tested.",version)
            return {
                "status": "VERSION_NOT_TESTED",
                "confidence": "MEDIUM",
                "reason": (
                    "Official metadata exists but this version "
                    "is not explicitly listed."
                ),
                "tested_versions": tested_versions,
                "metadata_version": entry.get("metadata-version")
            }

        # Case 4: Metadata exists without tested-versions.
        logger.info("[Repository] Metadata found without tested versions.")
        return {
            "status": "OFFICIAL_METADATA",
            "confidence": "MEDIUM",
            "reason": "Official metadata available.",
            "metadata_version": entry.get("metadata-version")
        }

    # Fallback
    logger.warning("[Repository] Unable to classify metadata.")
    return {
        "status": "NO_EVIDENCE",
        "confidence": "LOW",
        "reason": "Unable to interpret metadata."
    }