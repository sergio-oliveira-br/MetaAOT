# webapp/views.py

import logging

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from webapp.forms import UrlForm
from webapp.services.analysis.dependency_classifier import classify_direct_vs_transitive, ClassificationError
from webapp.services.analysis.dependency_graph import build_graph_from_sbom
from webapp.services.analysis.pom_parser import parse_pom_content, PomParseError
from webapp.services.analysis.reporter import summarize_dependencies
from webapp.services.analysis.sbom_loader import load_sbom_from_repo
from webapp.services.github.extract_owner_repo import extract_owner_repo_from_url
from webapp.services.github.check_public import is_github_repository_public, GitHubAPIError
from webapp.services.github.detect_maven import is_java_maven_project
from webapp.services.github.fetch_file import FetchError, fetch_file_content
from webapp.services.github.pom_root_check import is_pom_in_root, PomCheckError

logger = logging.getLogger(__name__)

@require_http_methods(["GET", "POST"])
def index(request):
    steps_log = []
    result = None
    form = UrlForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        url = form.cleaned_data['url']
        steps_log.append(f"1) Initiating analysis for: {url}")

        #extract owner/repo
        owner_repo = extract_owner_repo_from_url(url)
        if not owner_repo:
            steps_log.append("2) URL is not a valid GitHub repository.")
            return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})

        owner, repo = owner_repo
        steps_log.append(f"2) Repository detected: {owner}/{repo}")

        # Check if is public
        try:
            steps_log.append("3) Checking if the repository is public...")
            is_public = is_github_repository_public(owner, repo)
            steps_log.append(f" --> Public Repository: {is_public}")
            if not is_public:
                steps_log.append(" --> Repository is not public. Terminating analysis.")
                return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})

        except GitHubAPIError:
            steps_log.append("3) Unexpected error while checking the repository.")
            return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})

        # Check if is Java/Maven
        try:
            steps_log.append("4) Check if the project appears to be Java/Maven...")
            is_java_maven = is_java_maven_project(owner, repo)
            steps_log.append(f" --> Java Maven: {is_java_maven}")
            if not is_java_maven:
                steps_log.append(" --> Project is not Java Maven. Terminating analysis.")
                return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})
        except Exception:
            steps_log.append("4) Unexpected error while checking the project")
            logger.exception("Unexpected error while checking the project: %s/%s", owner, repo)

        # Check if is POM is in root
        try:
            steps_log.append("5) Checking if the POM.xml is in root of the repository...")
            pom_exists = is_pom_in_root(owner, repo)
            steps_log.append(f" --> Is POM in Root: {pom_exists}")
            if not pom_exists:
                steps_log.append(" --> POM.xml not found in the root. Terminating analysis.")
                return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})
        except PomCheckError:
            steps_log.append("5) Error checking POM.xml in the repository.")
            return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})

        # fetch pom content
        try:
            steps_log.append("6) Downloading pom.xml...")
            pom_text = fetch_file_content(owner, repo, "pom.xml")
            if not pom_text:
                steps_log.append(" --> Unable to download POM.xml. Closing analysis.")
                return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})
            steps_log.append(" --> POM.xml downloaded successfully.")
        except FetchError:
            steps_log.append("6) Error downloading POM.xml.")
            logger.exception("Error fetching POM.xml for %s/%s", owner, repo)
            return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})

        # parse pom
        try:
            steps_log.append("7) Parsing POM.xml...")
            pom_deps = parse_pom_content(pom_text)
            steps_log.append(f" --> {len(pom_deps)} dependencies declared found on POM.")
        except PomParseError:
            steps_log.append("7) Error parsing POM.xml.")
            logger.exception("Error parsing POM.xml for %s/%s", owner, repo)
            return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})

        # try load SBOM and build graph using cyclonedx
        try:
            steps_log.append("8) Searching for SBOM CycloneDX in the repository...")
            sbom_text = load_sbom_from_repo(owner, repo)
            if sbom_text:
                steps_log.append(" --> SBOM detected. Parsing with cyclonedx-python-lib...")
                graph = build_graph_from_sbom(sbom_text)
                steps_log.append(f" --> Graph SBOM built with {len(graph)} nodes.")
            else:
                steps_log.append(" --> SBOM not found. It will use heuristics only with the POM.")
                graph = {}
        except Exception:
            steps_log.append("8) Error loading/parsing SBOM.")
            logger.exception("Error loading/parsing SBOM for %s/%s", owner, repo)
            graph = {}

        # classify dependencies
        try:
            steps_log.append("9) Classifying direct vs transitive dependencies...")
            classified = classify_direct_vs_transitive(pom_deps, graph)
            summary = summarize_dependencies(classified)
            steps_log.append(" --> Classification completed.")
            result = {"summary": summary}
        except ClassificationError:
            steps_log.append("9) Error classifying dependencies.")
            logger.exception("Error classifying dependencies for %s/%s", owner, repo)
            result = None

        steps_log.append(f"Finished analysis for: {url}")

    return render(request, 'index.html', {
        'form': form,
        'steps_log': steps_log,
        'result': result,
    })
