# webapp/services/analysis/attention_points.py

from typing import List, Dict

MAX_POINTS = 200

def build_attention_points(aot_results: List[Dict]) -> List[Dict]:
    candidates = []
    for item in aot_results:
        if item.get("status") == "EVIDENCE_NOT_FOUND":
            package_name = item.get("package_name", "")
            scope = item.get("declared_scope", "compile").lower()
            origin = item.get("origin", "compile").lower()

            if scope == "test" or origin == "unknown":
                is_mitigated = True
                justification = "Non-production dependency (either test scope or omitted from runtime build)."
            else:
                is_mitigated = False
                justification = ""

            candidates.append({
                "package_name": package_name,
                "is_mitigated": is_mitigated,
                "justification": justification
            })

    return sorted(candidates, key=lambda x: (x["is_mitigated"], x["package_name"]))[:MAX_POINTS]