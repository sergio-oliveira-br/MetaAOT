# webapp/services/analysis/executive_summary.py

from typing import Dict

def build_executive_summary(dependency_summary, aot_summary):

    total = aot_summary.get("total_components", 0)
    high = aot_summary.get("high_evidence", 0)
    medium = aot_summary.get("medium_evidence", 0)
    no_ev = aot_summary.get("no_evidence", 0)

    coverage = aot_summary.get("evidence_coverage", 0)

    if total < 5:
        readiness = "INSUFFICIENT DATA"
        message = (
            "The analysed dataset is too small to produce a reliable "
            "migration assessment."
        )

    elif no_ev / total >= 0.6:
        readiness = "HIGH RISK"
        message = (
            "Most components lack compatibility evidence. "
            "Migration will likely require significant effort and validation."
        )

    elif coverage >= 80:
        readiness = "No Migration Effort Expected"
        message = (
            "Most components contain compatibility evidence. "
            "Migration is expected to be smooth."
        )

    elif coverage >= 50:
        readiness = "Moderate Migration Effort Expected"
        message = (
            "A mixed evidence profile was detected. "
            "Some components require validation."
        )

    else:
        readiness = "Significant Migration Effort Expected"
        message = (
            "A large portion of the dependency graph lacks evidence. "
            "Migration may require substantial work."
        )

    return {
        "readiness": readiness,
        "evidence_coverage": coverage,
        "components_analyzed": total,
        "components_without_evidence": no_ev,
        "high_evidence": high,
        "medium_evidence": medium,
        "message": message
    }