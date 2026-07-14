# webapp/services/analysis/executive_summary.py

from typing import Dict

def build_executive_summary(dependency_summary, aot_summary):

    total = aot_summary.get("total_components", 0)
    no_ev = aot_summary.get("no_evidence", 0)
    coverage = aot_summary.get("evidence_coverage", 0)
    not_applicable = aot_summary.get("not_applicable", 0)
    
    effective_components = total - not_applicable

    if total < 1:
        readiness = "No Migration Effort Expected"
        message = (
            "No external dependencies were detected. Since the project structure is clean, "
            "the migration to a native binary should proceed smoothly without any compatibility issues."
        )

    elif no_ev / effective_components >= 0.6:
        readiness = "Required Attention"
        message = (
            "Most components lack compatibility evidence. "
            "Migration will likely require significant effort and validation."
        )

    elif coverage == 100:
        readiness = "No Migration Effort Expected"
        message = (
            "All components contain compatibility evidence. "
            "Migration is expected to be smooth."
    )

    else:
        readiness = "Required Attention"
        message = (
            "One or more dependency lacks evidence. "
            "Migration may require substantial work."
        )

    return {
        "readiness": readiness,
        "evidence_coverage": coverage,
        "components_analyzed": total,
        "components_without_evidence": no_ev,
        "message": message
    }