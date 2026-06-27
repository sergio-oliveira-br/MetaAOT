# webapp/services/analysis/reporter.py

from typing import List, Dict, Any

import logging

logger = logging.getLogger(__name__)

def summarize_dependencies(classified: List[Dict]) -> Dict:
    summary = {"total": len(classified), "direct": 0, "transitive": 0, "unknown": 0, "details": classified}
    for item in classified:
        origin = item.get("origin", "unknown")
        if origin in summary:
            summary[origin] += 1
        else:
            summary["unknown"] += 1
    logger.debug("Generated summary: %s", {k: summary[k] for k in ("total","direct","transitive","unknown")})
    return summary


def summarize_aot_results(aot_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "total_components": len(aot_results),
        "embedded_metadata": 0,
        "official_metadata": 0,
        "version_not_tested": 0,
        "not_applicable": 0,
        "no_evidence": 0
    }

    for item in aot_results:
        status = (item.get("status") or "").strip().upper()
        logger.info(f"AOT Status => {status}")

        if status == "EMBEDDED_METADATA":
            summary["embedded_metadata"] += 1

        elif status == "OFFICIAL_METADATA":
            summary["official_metadata"] += 1

        elif status == "VERSION_NOT_TESTED":
            summary["version_not_tested"] += 1

        elif status == "NOT_APPLICABLE":
            summary["not_applicable"] += 1

        elif status == "NO_EVIDENCE":
            summary["no_evidence"] += 1

        else:
            logger.warning(f"Unknown status: {status}")
            summary["no_evidence"] += 1

    effective = (
        summary["embedded_metadata"]
        + summary["official_metadata"]
        + summary["version_not_tested"]
        + summary["no_evidence"]
    )

    if effective > 0:
        supported = (summary["embedded_metadata"]+ summary["official_metadata"])
        summary["evidence_coverage"] = round(supported / effective * 100, 2)
        logger.info(summary["evidence_coverage"])
    else:
        summary["evidence_coverage"] = 100.0

    logger.info(f"AOT Summary => {summary}")
    return summary