# webapp/services/analysis/attention_points.py

from typing import List, Dict

MAX_POINTS = 100

def build_attention_points(aot_results: List[Dict]) -> List[str]:
    candidates = []
    for item in aot_results:
        if item.get("status") == "NO EVIDENCE":
            candidates.append(item["package_name"])
    return sorted(candidates)[:MAX_POINTS]