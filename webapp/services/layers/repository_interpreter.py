# webapp/services/layers/repository_interpreter.py

import logging

logger = logging.getLogger(__name__)

class RepositoryInterpreter:

    @staticmethod
    def interpret(metadata, version):
        logger.info("[Interpreter] Analysing repository metadata...")
        if metadata is None:
            logger.info("[Interpreter] No index metadata.")
            return {
                "status": "NO_EVIDENCE",
                "confidence": "LOW",
                "reason": "Repository index not found"
            }

        if not isinstance(metadata, list):
            logger.warning("[Interpreter] Invalid JSON.")
            return {
                "status": "NO_EVIDENCE",
                "confidence": "LOW",
                "reason": "Invalid index.json"
            }

        for entry in metadata:
            if entry.get("not-for-native-image"):
                logger.info("[Interpreter] Artifact marked as NOT_APPLICABLE.")
                return {
                    "status": "NOT_APPLICABLE",
                    "confidence": "HIGH",
                    "reason": entry.get("reason"),
                    "replacement": entry.get("replacement")
                }

            tested = entry.get("tested-versions", [])
            if version in tested:
                logger.info("[Interpreter] Exact version found.")
                return {
                    "status": "OFFICIAL_METADATA",
                    "confidence": "HIGH",
                    "reason": "Official metadata",
                    "tested_versions": tested
                }

            if tested:
                logger.info("[Interpreter] Version not tested.")
                return {
                    "status": "VERSION_NOT_TESTED",
                    "confidence": "MEDIUM",
                    "reason": "Metadata exists for other versions",
                    "tested_versions": tested
                }

            logger.info("[Interpreter] Metadata without tested versions.")
            return {
                "status": "OFFICIAL_METADATA",
                "confidence": "MEDIUM",
                "reason": "Metadata available"
            }

        logger.warning("[Interpreter] Could not classify metadata.")
        return {
            "status": "NO_EVIDENCE",
            "confidence": "LOW",
            "reason": "Unable to classify"
        }