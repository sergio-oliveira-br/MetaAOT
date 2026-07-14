# webapp/services/layers/aot_engine.py

import time

from .maven import download_jar
from .jar_inspector import inspect_jar
from .models import AOTAnalysisResult
from .repository_service import RepositoryService


def analyze_component(group_id, artifact_id, version):
    start = time.perf_counter()
    package_name = (f"{group_id}:"
        f"{artifact_id}:"
        f"{version}")
    jar = download_jar(group_id, artifact_id, version)

    if jar:
        jar_result = inspect_jar(jar)

        if jar_result["status"] in ["EMBEDDED_METADATA", "NOT_APPLICABLE"]:
            return AOTAnalysisResult(
                package_name=package_name,
                status=jar_result["status"],
                confidence=jar_result["confidence"],
                reason=jar_result["reason"],
                elapsed_ms=(time.perf_counter() - start) * 1000, layer=1
            )

    repository = RepositoryService.analyse(group_id, artifact_id, version)
    if repository["status"] != "EVIDENCE_NOT_FOUND":
        return AOTAnalysisResult(
            package_name=package_name,
            status=repository["status"],
            confidence=repository["confidence"],
            reason=repository["reason"],
            elapsed_ms=(time.perf_counter() - start) * 1000, layer=2)

    return AOTAnalysisResult(
        package_name=package_name,
        status="EVIDENCE_NOT_FOUND",
        confidence="LOW",
        reason="No internal metadata found and no external reachability metadata available",
        elapsed_ms=(time.perf_counter()-start) * 1000,
        layer=3)