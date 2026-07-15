# webapp/services/analysis/evidence_resolver.py

def review_missing_evidence(results, graph):

    result_map = {
        r["bom_ref"]: r
        for r in results
    }
    for component in results:
        if component["status"] != "EVIDENCE_NOT_FOUND":
            continue
        evidence = find_evidence(
            component["bom_ref"],
            graph,
            result_map
        )
        if evidence:
            component["effective_status"] = "SUPPORTED_TRANSITIVELY"
            component["evidence_source"] = evidence
        else:
            component["effective_status"] = "EVIDENCE_NOT_FOUND"

    for component in results:
        component["effective_status"] = component.get(
            "effective_status",
            component["status"]
        )

    for component in results:
        component["status"] = component.get("effective_status", component.get("status"))
    return results


def find_evidence(node, graph, result_map, visited=None):
    if visited is None:
        visited = set()

    # Prevent cycles
    if node in visited:
        return None

    visited.add(node)
    current = result_map.get(node)

    if current:
        current_status = current.get("status")
        effective_status = current.get("effective_status")

        # Direct evidence
        if current_status in [
            "EMBEDDED_METADATA",
            "OFFICIAL_METADATA"
        ]:
            return {
                "source": node,
                "status": current_status,
                "path": [node]
            }

        if effective_status == "SUPPORTED_TRANSITIVELY":
            return {
                "source": current.get("evidence_source"),
                "status": effective_status,
                "path": [node]
            }
    children = graph.get(node, [])
    for child in children:
        evidence = find_evidence(
            child,
            graph,
            result_map,
            visited
        )
        if evidence:
            return {
                "source": evidence["source"],
                "status": evidence["status"],
                "path": [node] + evidence["path"]
            }
    return None