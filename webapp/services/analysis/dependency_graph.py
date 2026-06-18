# webapp/services/analysis/dependency_graph.py
from typing import Dict, Set, Optional
import logging

logger = logging.getLogger(__name__)

class SBOMParseError(Exception):
    pass

def build_graph_from_sbom(sbom_text: str) -> Dict[str, Set[str]]:
    try:
        from cyclonedx.parser import XmlParser, JsonParser
        from cyclonedx.model import Component, Dependency
    except Exception as exc:
        raise SBOMParseError("cyclonedx-python-lib not installed") from exc

    # XML
    parsers = [("xml", XmlParser), ("json", JsonParser)]
    last_exc = None
    for kind, ParserCls in parsers:
        try:
            parser = ParserCls(sbom_text)
            bom = parser.get_bom()
            id_to_ref = {}
            for comp in bom.components or []:
                ref = None
                try:
                    ref = comp.purl or (f"{comp.group}:{comp.name}:{comp.version}" if getattr(comp, "group", None) else f"{comp.name}:{comp.version}" if comp.version else comp.name)
                except Exception:
                    ref = getattr(comp, "name", None) or getattr(comp, "bom_ref", None) or ""
                bom_ref = getattr(comp, "bom_ref", None) or getattr(comp, "bom-ref", None) or getattr(comp, "ref", None) or ref
                id_to_ref[bom_ref] = ref

            # construct the graph from pom.dependencies (each dependency has a reference and depends_on list)
            graph: Dict[str, Set[str]] = {}
            for dep in bom.dependencies or []:
                parent_ref = id_to_ref.get(dep.ref, dep.ref)
                children = set()
                for child in getattr(dep, "depends_on", []) or []:
                    children.add(id_to_ref.get(child, child))
                graph[parent_ref] = children
            logger.debug("Graph Built - SBOM (%s) com %d nós", kind, len(graph))
            return graph

        except Exception as exc:
            last_exc = exc
            logger.debug("Fails when parsing SBOM as %s: %s", kind, exc)
            continue

    logger.exception("It was not possible to stop SBOM")
    raise SBOMParseError("It was not possible to parse SBOM") from last_exc