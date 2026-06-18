# webapp/services/analysis/pom_parser.py
from typing import List, Dict
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class PomParseError(Exception):
    pass

def parse_pom_content(pom_text: str) -> List[Dict[str, str]]:
    try:
        ns = {}
        it = ET.iterparse(__import__("io").StringIO(pom_text), events=("start",))
        root_tag = None
        for event, elem in it:
            root_tag = elem.tag
            break
        if root_tag and root_tag.startswith("{"):
            uri = root_tag.split("}")[0].strip("{")
            ns = {"m": uri}
            dep_path = ".//m:dependencies/m:dependency"
        else:
            dep_path = ".//dependencies/dependency"

        tree = ET.fromstring(pom_text)
        deps = []
        for dep in tree.findall(dep_path, ns):
            def get_text(tag):
                el = dep.find(f"m:{tag}", ns) if ns else dep.find(tag)
                return (el.text or "").strip() if el is not None and el.text else ""
            d = {
                "groupId": get_text("groupId"),
                "artifactId": get_text("artifactId"),
                "version": get_text("version"),
                "scope": get_text("scope") or "compile",
                "optional": get_text("optional") or "false",
            }
            deps.append(d)
        logger.debug("Parsed %d dependencies from POM", len(deps))
        return deps
    except Exception as exc:
        logger.exception("Error when parse pom.xml")
        raise PomParseError("Error when parse pom.xml") from exc
