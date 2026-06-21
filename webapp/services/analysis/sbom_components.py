# webapp/services/analysis/sbom_components.py

import json

def extract_components(sbom_text):
    sbom = json.loads(sbom_text)
    result = []

    for component in sbom.get("components", []):
        result.append({
            "group": component.get("group"),
            "name": component.get("name"),
            "version": component.get("version")})
    return result