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
        "high_evidence": 0,
        "medium_evidence": 0,
        "no_evidence": 0
    }
    for item in aot_results:
        status = (item.get("status") or "").strip().upper()
        if status in ["HIGH EVIDENCE", "HIGH_EVIDENCE"]:
            summary["high_evidence"] += 1
        elif status in ["MEDIUM EVIDENCE", "MEDIUM_EVIDENCE"]:
            summary["medium_evidence"] += 1
        elif status == "NO EVIDENCE":
            summary["no_evidence"] += 1
        else:
            logger.warning(f"Unknown AOT status: {status}")
            summary["no_evidence"] += 1
    total = summary["total_components"]
    if total > 0:
        summary["evidence_coverage"] = round((summary["high_evidence"]+ summary["medium_evidence"])/ total * 100, 2)
    else:
        summary["evidence_coverage"] = 0
    return summary