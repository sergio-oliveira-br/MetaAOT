# webapp/services/analysis/dependency_classifier.py

from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

class ClassificationError(Exception):
    pass

def _make_coord(dep: Dict[str, str]) -> str:
    g = dep.get("groupId", "").strip()
    a = dep.get("artifactId", "").strip()
    v = dep.get("version", "").strip()
    if v:
        return f"{g}:{a}:{v}"
    return f"{g}:{a}"

def _normalize_node(node: str) -> str:
    return (node or "").lower().strip()

def classify_direct_vs_transitive(pom_deps: List[Dict[str, str]], sbom_graph: Dict[str, Set[str]]) -> List[Dict]:
    try:
        sbom_nodes = set(_normalize_node(n) for n in sbom_graph.keys())
        all_children = set(_normalize_node(c) for children in sbom_graph.values() for c in children)

        results = []
        for dep in pom_deps:
            coord = _make_coord(dep)
            declared_scope = dep.get("scope", "compile")
            origin = "unknown"
            evidence = []

            coord_norm = _normalize_node(coord)
            # heurística: match by exact purl or suffix group:artifact or group:artifact:version
            matched_nodes = [n for n in sbom_nodes if n.endswith(coord_norm) or coord_norm.endswith(n)]
            if matched_nodes:
                origin = "direct"
                evidence.append(f"Matched SBOM node(s): {matched_nodes}")
            else:
                matched_children = [n for n in all_children if n.endswith(coord_norm) or coord_norm.endswith(n)]
                if matched_children:
                    origin = "transitive"
                    evidence.append(f"Matched SBOM dependency(s): {matched_children}")

            results.append({
                "name": coord,
                "declared_scope": declared_scope,
                "origin": origin,
                "evidence": evidence or ["No SBOM evidence found"],
                "optional": dep.get("optional", "false"),
            })
        return results
    except Exception:
        logger.exception("Error when classifying dependencies")
        raise ClassificationError("Error when classifying dependencies")
