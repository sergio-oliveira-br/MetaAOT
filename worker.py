# worker.py

import json
import logging
import traceback
import boto3

from webapp.services.analysis.attention_points import build_attention_points
from webapp.services.analysis.evidence_resolver import review_missing_evidence
from webapp.services.analysis.executive_summary import build_executive_summary
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
MAX_COMPONENTS_ANALYZED = 300

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
        logger.exception(f"Error updating steps_log in DynamoDB: {e}")

def handle_failure(job_id, exc, final_message):
    append_log(job_id, final_message)
    table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #s=:s, #e=:e",
        ExpressionAttributeNames={"#s": "status", "#e": "error"},
        ExpressionAttributeValues={":s": "FAILED", ":e": traceback.format_exc()}
    )

def lambda_handler(event, context):
    logger.info("Worker Started. Received event: " + json.dumps(event, indent=2))

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

    excluded_count = 0

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
            append_log(job_id, f"    [OK] {len(pom_deps)} dependencies declared found on POM.")
        except PomParseError as exc:
            handle_failure(job_id, exc, "    [X] Error parsing POM.xml.")
            return {"statusCode": 200}

        if len(pom_deps) == 0:
            append_log(job_id, "    [OK] Clean project detected. Bypassing downstream analysis steps.")

            dependency_summary = summarize_dependencies([])
            aot_summary = summarize_aot_results([])
            executive_summary = build_executive_summary(dependency_summary, aot_summary)
            attention_points = build_attention_points([])

            result = {
                "dependency_summary": dependency_summary,
                "aot_summary": aot_summary,
                "executive_summary": executive_summary,
                "attention_points": attention_points,
                "aot_results": []
            }

            append_log(job_id, f"    [FINISHED] Job {job_id} successfully (No dependencies to analyze).")

            table.update_item(
                Key={"job_id": job_id},
                UpdateExpression="SET #s=:s, #r=:r",
                ExpressionAttributeNames={"#s": "status", "#r": "result"},
                ExpressionAttributeValues={":s": "COMPLETED", ":r": convert_floats(result)}
            )
            return {
                "statusCode": 200,
                "body": json.dumps({"message": f"Job {job_id} processed successfully (0 dependencies found)."})
            }

        append_log(job_id, "8) Generating CycloneDX SBOM using AWS CodeBuild...")
        try:
            sbom_text = generate_sbom(owner, repo)
            if not sbom_text:
                handle_failure(job_id, "Empty SBOM", "    [!] Unable to generate SBOM. Closing analysis.")
                return {"statusCode": 200}
            append_log(job_id, "    [OK] SBOM generated successfully.")
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
            handle_failure(job_id, exc, "    [X] Building dependency graph failed.")
            return {"statusCode": 500}

        append_log(job_id, "10) Extracting Components...")
        try:
            components = extract_components(sbom_text)
            if not components:
                handle_failure(job_id, "No Components", "     [!] No Components Found.")
                return {"statusCode": 200}
            append_log(job_id, f"    [OK] {len(components)} components found.")
        except Exception as exc:
            handle_failure(job_id, exc, "    [X] Extracting components failed.")
            return {"statusCode": 500}

        append_log(job_id, "11) Analysing Native Image Compatibility...")
        try:
            aot_results = []
            for component in components[:MAX_COMPONENTS_ANALYZED]:
                res = analyze_component(component["group"], component["name"], component["version"])
                aot_results.append({
                    "status": res.status,
                    "layer": res.layer,
                    "package_name": res.package_name,
                    "group": component["group"],
                    "name": component["name"],
                    "version": component["version"],
                    "bom_ref": component["bom_ref"],
                })

            append_log(job_id, f"    [OK] Analysis completed")

            embedded = sum(1 for x in aot_results if x["status"] == "EMBEDDED_METADATA")
            official = sum(1 for x in aot_results if x["status"] == "OFFICIAL_METADATA")
            not_tested = sum(1 for x in aot_results if x["status"] == "VERSION_NOT_TESTED")
            not_applicable = sum(1 for x in aot_results if x["status"] == "NOT_APPLICABLE")
            evidence_not_found = sum(1 for x in aot_results if x["status"] == "EVIDENCE_NOT_FOUND")
            supported_transitively = sum(1 for x in aot_results if x["status"] == "SUPPORTED_TRANSITIVELY")

        #     append_log(
        #         job_id,
        #         f"Embedded={embedded} "
        #         f"Official={official} "
        #         f"VersionNotTested={not_tested} "
        #         f"NotApplicable={not_applicable} "
        #         f"EvidenceNotFound={evidence_not_found}"
        #         f"SupportedTransitively={supported_transitively}"
        # )
        except Exception as exc:
            handle_failure(job_id, exc, "    [X] AOT Analysis Failed.")
            return {"statusCode": 500}

        append_log(job_id, "12) Classifying Dependencies...")
        try:
            classified = classify_direct_vs_transitive(pom_deps, graph)
            # origin_map = {item["name"]: item["origin"] for item in classified}
            classified_map = {item["name"]: item for item in classified}
            dependency_summary = summarize_dependencies(classified)
            aot_results = review_missing_evidence(aot_results, graph)
            aot_summary = summarize_aot_results(aot_results)
            executive_summary = build_executive_summary(dependency_summary, aot_summary)
            attention_points = build_attention_points(aot_results)
            append_log(job_id, "    [OK] Classification completed.")
        except ClassificationError as exc:
            handle_failure(job_id, exc, "    [X] Error classifying dependencies.")
            return {"statusCode": 500}


        aot_results_classified = []
        for comp in aot_results:
            if hasattr(comp, "__dict__") and not isinstance(comp, dict):
                comp_dict = {
                    "package_name": getattr(comp, "package_name", ""),
                    "status": getattr(comp, "status", ""),
                    "effective_status": getattr(comp, "effective_status", ""),
                    "evidence_source": getattr(comp, "evidence_source", []),
                    "confidence": getattr(comp, "confidence", ""),
                    "reason": getattr(comp, "reason", ""),
                    "layer": getattr(comp, "layer", ""),
                    "elapsed_ms": getattr(comp, "elapsed_ms", 0),
                }
            else:
                comp_dict = dict(comp)

            pkg_name = comp_dict.get("package_name", "")
            class_info = classified_map.get(pkg_name, {})
            comp_dict["origin"] = class_info.get("origin", "transitive")
            comp_dict["declared_scope"] = class_info.get("declared_scope", "compile")
            comp_dict["optional"] = class_info.get("optional", "false")
            aot_results_classified.append(comp_dict)

        result = {
            "dependency_summary": dependency_summary,
            "aot_summary": aot_summary,
            "executive_summary": executive_summary,
            "attention_points": attention_points,
            "aot_results": aot_results_classified
        }
        append_log(job_id, f"    [FINISHED] Job {job_id}.")

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
        handle_failure(job_id, exc, "    [X] Unexpected Worker failure.")
        raise exc