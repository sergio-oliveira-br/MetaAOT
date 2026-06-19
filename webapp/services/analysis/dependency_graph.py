# webapp/services/analysis/dependency_graph.py

import logging
import json

logger = logging.getLogger(__name__)

class SBOMParseError(Exception):
    pass

def build_graph_from_sbom(sbom_text):
    try:
        sbom = json.loads(sbom_text)
    except Exception as exc:
        raise SBOMParseError(
            "Invalid CycloneDX JSON"
        ) from exc
    graph = {}
    for dep in sbom.get("dependencies", []):
        parent = dep.get("ref")
        if not parent:
            continue
        graph[parent] = set(
            dep.get("dependsOn", [])
        )
    logger.info(
        "SBOM graph built with %d nodes",
        len(graph)
    )
    return graph