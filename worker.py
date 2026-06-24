# worker.py

import json
import logging
import boto3

from webapp.services.github.fetch_file import fetch_file_content
from webapp.services.analysis.pom_parser import parse_pom_content
from webapp.services.sbom.codebuild_runner import generate_sbom
from webapp.services.analysis.dependency_graph import build_graph_from_sbom
from webapp.services.analysis.sbom_components import extract_components
from webapp.services.layers.aot_engine import analyze_component
from webapp.services.analysis.dependency_classifier import classify_direct_vs_transitive
from webapp.services.analysis.reporter import summarize_dependencies

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("AnalysisJob")
MAX_COMPONENTS_ANALYZED = 20

def lambda_handler(event, context):
    logger.info("Worker started")
    logger.info("Received event: " + json.dumps(event, indent=2))

    if "body" in event:
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
            job_id = body.get("job_id")
            owner = body.get("owner")
            repo = body.get("repo")
        except Exception:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON body"})}
    else:
        job_id = event.get("job_id")
        owner = event.get("owner")
        repo = event.get("repo")

    # Checker
    if not job_id or not owner or not repo:
        logger.error("Missing required parameters: job_id, owner, or repo.")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing parameters", "received": event})
        }

    try:
        logger.info("Processing %s/%s",owner,repo)

        pom_text = fetch_file_content(owner, repo, "pom.xml")
        pom_deps = parse_pom_content(pom_text)
        sbom_text = generate_sbom(owner, repo)
        graph = build_graph_from_sbom(sbom_text)
        components = extract_components(sbom_text)
        aot_results = []

        for component in components[:MAX_COMPONENTS_ANALYZED]:
            result = analyze_component(component["group"], component["name"], component["version"])
            aot_results.append({"status": result.status, "layer": result.layer, "package_name": result.package_name})

        classified = classify_direct_vs_transitive(pom_deps, graph)
        summary = summarize_dependencies(classified)

        result = {"summary": summary, "aot_results": aot_results}

        logger.info("Processing %s/%s",owner,repo)
        logger.info("Summary: %s", summary)
        logger.info("AOT Results: %s", aot_results)
        logger.info("jobID: %s", job_id)

        table.update_item(
            Key={
                "job_id": job_id
            },
            UpdateExpression=
                "SET #s=:s,#r=:r",
            ExpressionAttributeNames={
                "#s": "status",
                "#r": "result"
            },
            ExpressionAttributeValues={
                ":s": "COMPLETED",
                ":r": result
            }
        )
        logger.info("Job %s completed",job_id)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Job {job_id} processed successfully"})
        }

    except Exception as exc:
        logger.exception("Job %s failed",job_id)
        table.update_item(
            Key={
                "job_id": job_id
            },
            UpdateExpression=
                "SET #s=:s,#e=:e",
            ExpressionAttributeNames={
                "#s": "status",
                "#e": "error"
            },
            ExpressionAttributeValues={
                ":s": "FAILED",
                ":e": str(exc)
            }
        )
        raise