# webapp/services/analysis/dependency_classifier.py

from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

class ClassificationError(Exception):
    pass

def _normalize_node(node: str) -> str:
    return (node or "").lower().strip()

def _parse_purl_details(purl: str) -> tuple:
    if not purl or not purl.startswith("pkg:maven/"):
        return purl, "", ""
    try:
        data = purl[len("pkg:maven/"):]
        version = ""
        if "@" in data:
            data, version = data.split("@", 1)
            if "?" in version:
                version = version.split("?", 1)[0]

        parts = data.split("/")
        if len(parts) == 2:
            return parts[0], parts[1], version
        return data, "", version
    except Exception:
        return purl, "", ""


def classify_direct_vs_transitive(pom_deps: List[Dict[str, str]], sbom_graph: Dict[str, Set[str]]) -> List[Dict]:
    try:
        pom_map = {}
        for dep in pom_deps:
            g = dep.get("groupId", "").strip().lower()
            a = dep.get("artifactId", "").strip().lower()
            pom_map[f"{g}:{a}"] = dep

        all_sbom_purls = set(sbom_graph.keys())
        for children in sbom_graph.values():
            all_sbom_purls.update(children)

        results = []
        classified_ga_coords = set()

        for purl in all_sbom_purls:
            group_id, artifact_id, version = _parse_purl_details(purl)
            coord = f"{group_id}:{artifact_id}"
            coord_norm = _normalize_node(coord)

            package_full_name = f"{coord}:{version}" if version else coord

            if coord_norm in pom_map:
                origin = "direct"
                dep_info = pom_map[coord_norm]
                declared_scope = dep_info.get("scope", "compile")
                optional = dep_info.get("optional", "false")
                evidence = [f"Matched direct POM dependency mapped via SBOM node: {purl}"]
            else:
                origin = "transitive"
                declared_scope = "transitive"
                optional = "false"
                evidence = [f"Discovered as runtime transitive dependency in SBOM graph: {purl}"]

            results.append({
                "name": package_full_name,
                "declared_scope": declared_scope,
                "origin": origin,
                "evidence": evidence,
                "optional": optional,
            })
            classified_ga_coords.add(coord_norm)

        for coord_norm, dep_info in pom_map.items():
            if coord_norm not in classified_ga_coords:
                coord_original = f"{dep_info.get('groupId')}:{dep_info.get('artifactId')}"
                results.append({
                    "name": coord_original,
                    "declared_scope": dep_info.get("scope", "compile"),
                    "origin": "unknown",
                    "evidence": ["Declared in POM but omitted/filtered out from the generated active SBOM graph"],
                    "optional": dep_info.get("optional", "false"),
                })

        return results
    except Exception:
        logger.exception("Error when classifying dependencies")
        raise ClassificationError("Error when classifying dependencies")