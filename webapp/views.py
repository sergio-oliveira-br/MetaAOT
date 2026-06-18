# webapp/views.py

import logging

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from webapp.forms import UrlForm
from webapp.services.github.extract_owner_repo import extract_owner_repo_from_url
from webapp.services.github.check_public import is_github_repository_public
from webapp.services.github.detect_maven import is_java_maven_project
from webapp.services.github.pom_root_check import is_pom_in_root

logger = logging.getLogger(__name__)

class CheckPublicError:
    pass

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
        else:
            owner, repo = owner_repo
            steps_log.append(f"2) Repository detected: {owner}/{repo}")

            # Check if is public
            try:
                steps_log.append("3) Checking if the repository is public...")
                is_public = is_github_repository_public(owner, repo)
                steps_log.append(f" --> Public Repository: {is_public}")
                result = {'owner': owner, 'repo': repo, 'repo_public': is_public}

            except Exception:
                steps_log.append("3) Unexpected error while checking the repository.")
                logger.exception("Unexpected error while checking repo: %s/%s", owner, repo)


        steps_log.append(f"Finished analysis for: {url}")


    return render(request, 'index.html', {
        'form': form,
        'steps_log': steps_log,
        'result': result,
    })
