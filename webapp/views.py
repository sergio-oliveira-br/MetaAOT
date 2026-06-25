# webapp/views.py
import json
import logging
import time
import uuid

import boto3
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from webapp.forms import UrlForm
from webapp.services.github.extract_owner_repo import extract_owner_repo_from_url
from webapp.services.github.check_public import is_github_repository_public, GitHubAPIError
from webapp.services.github.detect_maven import is_java_maven_project
from webapp.services.github.pom_root_check import is_pom_in_root, PomCheckError

logger = logging.getLogger(__name__)
lambda_client = boto3.client("lambda")
table_db = boto3.resource("dynamodb").Table( "AnalysisJob")

@require_http_methods(["GET", "POST"])
def health(request):
    return HttpResponse("OK")

@require_http_methods(["GET", "POST"])
def sleep60(request):
    import time
    time.sleep(60)
    return HttpResponse("OK AFTER 60")

def job_status(request, job_id):
    response = table_db.get_item(
        Key={
            "job_id": job_id
        }
    )
    item = response.get("Item")
    if not item:
        return JsonResponse({"status": "NOT_FOUND"})
    return JsonResponse(item)

@require_http_methods(["GET", "POST"])
def index(request):
    start = time.time()
    steps_log = []
    result = None
    form = UrlForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        url = form.cleaned_data['url']
        steps_log.append(f"1) Initiating analysis for: {url}")
        owner_repo = extract_owner_repo_from_url(url)
        if not owner_repo:
            steps_log.append("    [!] URL is not a valid GitHub repository. Terminating...")
            return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})
        owner, repo = owner_repo
        steps_log.append(f"2) Repository detected: {owner}/{repo}")

        # Check if is public
        try:
            steps_log.append("3) Checking if the repository is public...")
            is_public = is_github_repository_public(owner, repo)
            if not is_public:
                steps_log.append("    [!] Repository is not public. Terminating analysis.")
                return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})
            steps_log.append(f"    [OK] Public Repository Confirmed.")
        except GitHubAPIError:
            steps_log.append("    [X] Unexpected error while checking the repository.")
            return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})

        # Check if is Java/Maven
        try:
            steps_log.append("4) Check if the project appears to be Java/Maven...")
            is_java_maven = is_java_maven_project(owner, repo)
            if not is_java_maven:
                steps_log.append("    [!] Project is not Java Maven. Terminating analysis.")
                return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})
            steps_log.append(f"    [OK] Java/Maven Confirmed.")
        except Exception:
            steps_log.append("    [X] Unexpected error while checking the project")
            logger.exception("Unexpected error while checking the project: %s/%s", owner, repo)
            return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})

        # Check if is POM is in root
        try:
            steps_log.append("5) Checking if the POM.xml is in root of the repository...")
            pom_exists = is_pom_in_root(owner, repo)
            if not pom_exists:
                steps_log.append("    [!] POM.xml not found in the root. Terminating analysis.")
                return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})
            steps_log.append(f"    [OK] POM.xml found in root of the repository.")
        except PomCheckError:
            steps_log.append("    [X] Error checking POM.xml in the repository.")
            return render(request, 'index.html', {'form': form, 'steps_log': steps_log, 'result': result})

        job_id = str(uuid.uuid4())
        table_db.put_item(
            Item={
                "job_id": job_id,
                "status": "PROCESSING",
                "owner": owner,
                "repo": repo,
                "steps_log": steps_log
            }
        )
        lambda_client.invoke(
            FunctionName="metaaot-worker-worker",
            InvocationType="Event",
            Payload=json.dumps({
                "job_id": job_id,
                "owner": owner,
                "repo": repo
            })
        )

        elapsedTime = time.time() - start
        steps_log.append(f"Delegated to worker. Local elapsed time: %.2f sec" % elapsedTime)

        return render(request, "index.html", {
            "form": form,
            "steps_log": steps_log,
            "result": result,
            "job_id": job_id
        })
    return render(request, "index.html", {"form": form, "steps_log": steps_log, "result": result})