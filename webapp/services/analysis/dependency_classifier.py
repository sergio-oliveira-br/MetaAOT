# webapp/services/analysis/dependency_classifier.py

from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

class ClassificationError(Exception):
    pass

def _make_coord(dep):
    g = dep.get("groupId", "").strip()
    a = dep.get("artifactId", "").strip()
    return f"{g}:{a}"

def _normalize_node(node: str) -> str:
    return (node or "").lower().strip()

def _normalize_purl_to_ga(node: str) -> str:
    if not node:
        return ""
    node = node.lower().strip()
    if not node.startswith("pkg:maven/"):
        return node
    try:
        purl = node[len("pkg:maven/"):]
        if "@" in purl:
            purl = purl.split("@", 1)[0]
        parts = purl.split("/")
        if len(parts) != 2:
            return node
        group_id, artifact_id = parts
        return f"{group_id}:{artifact_id}"
    except Exception:
        return node

def classify_direct_vs_transitive(pom_deps: List[Dict[str, str]], sbom_graph: Dict[str, Set[str]]) -> List[Dict]:
    try:
        sbom_nodes = set(_normalize_purl_to_ga(n) for n in sbom_graph.keys())
        all_children = set(_normalize_purl_to_ga(c) for children in sbom_graph.values() for c in children)

        results = []
        for dep in pom_deps:
            coord = _make_coord(dep)
            declared_scope = dep.get("scope", "compile")
            origin = "unknown"
            evidence = []

            coord_norm = _normalize_node(coord)
            matched_nodes = [n for n in sbom_nodes if n == coord_norm]
            if matched_nodes:
                origin = "direct"
                evidence.append(f"Matched SBOM node(s): {matched_nodes}")
            else:
                matched_children = [n for n in all_children if n == coord_norm]
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
