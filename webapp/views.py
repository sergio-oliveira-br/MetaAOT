# webapp/views.py

import logging

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from webapp.forms import UrlForm
from webapp.services.github.extract_owner_repo import extract_owner_repo_from_url
from webapp.services.github.check_public import is_github_repository_public, GitHubAPIError
from webapp.services.github.detect_maven import is_java_maven_project
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

        steps_log.append(f"Finished analysis for: {url}")


    return render(request, 'index.html', {
        'form': form,
        'steps_log': steps_log,
        'result': result,
    })
