# webapp/services/analysis/reporter.py

from typing import List, Dict
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
