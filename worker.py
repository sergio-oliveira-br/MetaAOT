# worker.py

import json
import logging
import boto3

from webapp.services.analysis.attention_points import build_attention_points
from webapp.services.analysis.executive_summary import build_executive_summary
from webapp.services.analysis.readiness_report import build_readiness_report
from webapp.services.github.fetch_file import fetch_file_content, FetchError
from webapp.services.analysis.pom_parser import parse_pom_content, PomParseError
from webapp.services.infra.dynamodb_serializer import convert_floats
from webapp.services.sbom.codebuild_runner import generate_sbom
from webapp.services.analysis.dependency_graph import build_graph_from_sbom
from webapp.services.analysis.sbom_components import extract_components
from webapp.services.layers.aot_engine import analyze_component
from webapp.services.analysis.dependency_classifier import classify_direct_vs_transitive, ClassificationError
from webapp.services.analysis.reporter import summarize_dependencies, summarize_aot_results

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("AnalysisJob")
MAX_COMPONENTS_ANALYZED = 100

def append_log(job_id, message):
    logger.info(f"[{job_id}] {message}")
    try:
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET steps_log = list_append(if_not_exists(steps_log, :empty_list), :log_msg)",
            ExpressionAttributeValues={
                ":log_msg": [message],
                ":empty_list": []
            }
        )
    except Exception as e:
        logger.error(f"Error updating steps_log in DynamoDB: {e}")

def handle_failure(job_id, exc, final_message):
    append_log(job_id, final_message)
    table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #s=:s, #e=:e",
        ExpressionAttributeNames={"#s": "status", "#e": "error"},
        ExpressionAttributeValues={":s": "FAILED", ":e": str(exc)}
    )

def lambda_handler(event, context):
    logger.info("Worker Started")
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

    if not job_id or not owner or not repo:
        logger.error("Missing required parameters: job_id, owner, or repo.")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing parameters", "received": event})
        }

    try:
        append_log(job_id, "6) Downloading pom.xml...")
        try:
            pom_text = fetch_file_content(owner, repo, "pom.xml")
            if not pom_text:
                handle_failure(job_id, "Empty POM", "    [!] Unable to download POM.xml. Closing analysis.")
                return {"statusCode": 200}
            append_log(job_id, "    [OK] POM.xml downloaded successfully.")
        except FetchError as exc:
            handle_failure(job_id, exc, "    [X] Error downloading POM.xml.")
            return {"statusCode": 200}

        append_log(job_id, "7) Parsing POM.xml...")
        try:
            pom_deps = parse_pom_content(pom_text)
            if not pom_deps:
                append_log(job_id, "    [!] Unable to parse POM. It does not exist. Terminating analysis.")
            append_log(job_id, f"    [OK] {len(pom_deps)} dependencies declared found on POM.")
        except PomParseError as exc:
            handle_failure(job_id, exc, "    [X] Error parsing POM.xml.")
            return {"statusCode": 200}

        append_log(job_id, "8) Generating CycloneDX SBOM using AWS CodeBuild...")
        try:
            sbom_text = generate_sbom(owner, repo)
            if not sbom_text:
                handle_failure(job_id, "Empty SBOM", "    [!] Unable to generate SBOM. Closing analysis.")
                return {"statusCode": 200}
            append_log(job_id, "    [OK] SBOM Generated Successfully.")
        except Exception as exc:
            handle_failure(job_id, exc, "    [X] SBOM generation failed.")
            return {"statusCode": 200}

        append_log(job_id, "9) Building Dependency Graph...")
        try:
            graph = build_graph_from_sbom(sbom_text)
            if not graph:
                handle_failure(job_id, "Empty Graph", " [!] Unable to build SBOM Graph. Closing analysis.")
                return {"statusCode": 200}
            append_log(job_id, f"    [OK] Graph SBOM built with {len(graph)} nodes.")
        except Exception as exc:
            handle_failure(job_id, exc, "    [X] Building Dependency Graph Failed.")
            return {"statusCode": 200}

        append_log(job_id, "10) Extracting Components...")
        try:
            components = extract_components(sbom_text)
            if not components:
                handle_failure(job_id, "No Components", "     [!] No Components Found.")
                return {"statusCode": 200}
            append_log(job_id, f"     [OK] {len(components)} Components Found.")
        except Exception as exc:
            handle_failure(job_id, exc, "     [X] Extracting Components Failed.")
            return {"statusCode": 200}

        append_log(job_id, "11) Analysing Native Image Compatibility...")
        try:
            aot_results = []
            for component in components[:MAX_COMPONENTS_ANALYZED]:
                res = analyze_component(component["group"], component["name"], component["version"])
                aot_results.append({
                    "status": res.status,
                    "layer": res.layer,
                    "package_name": res.package_name
                })
            green_count = sum(1 for x in aot_results if x["status"] == "HIGH EVIDENCE")
            yellow_count = sum(1 for x in aot_results if x["status"] == "MEDIUM EVIDENCE")
            next_layer_count = sum(1 for x in aot_results if x["status"] == "NO EVIDENCE")

            append_log(job_id, "     [OK] AOT Analysis finished")
            append_log(job_id, f"     [OK] HIGH EVIDENCE={green_count} MEDIUM EVIDENCE={yellow_count} NO EVIDENCE={next_layer_count}")
        except Exception as exc:
            handle_failure(job_id, exc, "     [X] AOT Analysis Failed.")
            return {"statusCode": 200}

        append_log(job_id, "12) Classifying direct vs transitive dependencies...")
        try:
            classified = classify_direct_vs_transitive(pom_deps, graph)
            # summary = summarize_dependencies(classified)
            dependency_summary = summarize_dependencies(classified)
            aot_summary = summarize_aot_results(aot_results)
            # readiness_report = build_readiness_report(aot_summary)
            executive_summary = build_executive_summary(dependency_summary, aot_summary)
            attention_points = build_attention_points(aot_results)
            append_log(job_id, "     [OK] Classification completed.")
        except ClassificationError as exc:
            handle_failure(job_id, exc, "     [X] Error classifying dependencies.")
            return {"statusCode": 200}

        result = {
            "dependency_summary": dependency_summary,
            "aot_summary": aot_summary,
            "executive_summary": executive_summary,
            "attention_points": attention_points,
            "aot_results": aot_results
        }
        append_log(job_id, f"     [FINISHED] analysis for job {job_id}.")

        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #s=:s, #r=:r",
            ExpressionAttributeNames={"#s": "status", "#r": "result"},
            ExpressionAttributeValues={":s": "COMPLETED", ":r": convert_floats(result)}
        )
        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Job {job_id} processed successfully"})
        }

    except Exception as exc:
        handle_failure(job_id, exc, "     [X] Unexpected Worker failure.")
        raise exc