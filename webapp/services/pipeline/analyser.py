# webapp/services/pipeline/analyser.py

from webapp.services.github.fetch_file import fetch_file_content
from webapp.services.analysis.pom_parser import parse_pom_content
from webapp.services.sbom.codebuild_runner import generate_sbom
from webapp.services.analysis.dependency_graph import build_graph_from_sbom
from webapp.services.analysis.sbom_components import extract_components
from webapp.services.layers.aot_engine import analyze_component
from webapp.services.analysis.dependency_classifier import classify_direct_vs_transitive
from webapp.services.analysis.reporter import summarize_dependencies

MAX_COMPONENTS_ANALYZED = 20

def run_analysis(owner, repo):
    pom_text = fetch_file_content(owner, repo, "pom.xml")
    pom_deps = parse_pom_content(pom_text)
    sbom_text = generate_sbom(owner, repo)
    graph = build_graph_from_sbom(sbom_text)
    components = extract_components(sbom_text)
    aot_results = []

    for component in components[:MAX_COMPONENTS_ANALYZED]:
        result = analyze_component(component["group"],component["name"],component["version"])
        aot_results.append({"status": result.status,"layer": result.layer,"package_name": result.package_name})

    classified = classify_direct_vs_transitive(pom_deps,graph)
    summary = summarize_dependencies(classified)

    return {"summary": summary,"aot_results": aot_results}
