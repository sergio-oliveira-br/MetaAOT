# webapp/services/layers/aot_engine.py

import time

from .maven import download_jar
from .jar_inspector import has_native_image_metadata
from .reachability import has_reachability_metadata
from .models import AOTAnalysisResult

def analyze_component(group_id, artifact_id, version):
    start = time.perf_counter()
    package_name = (f"{group_id}:"
        f"{artifact_id}:"
        f"{version}")
    jar = download_jar(group_id, artifact_id, version)

    if jar:
        if has_native_image_metadata(jar):
            return AOTAnalysisResult(
                package_name=package_name,
                status="GREEN",
                confidence="HIGH",
                reason="Embedded Native Image metadata",
                elapsed_ms=(time.perf_counter()-start) * 1000, layer=1)

    if has_reachability_metadata(group_id, artifact_id, version):
        return AOTAnalysisResult(
            package_name=package_name,
            status="YELLOW",
            confidence="MEDIUM",
            reason="Reachability Metadata Repository",
            elapsed_ms=(time.perf_counter()-start) * 1000,layer=2)

    return AOTAnalysisResult(
        package_name=package_name,
        status="NEXT_LAYER",
        confidence="LOW",
        reason="No metadata found",
        elapsed_ms=(time.perf_counter()-start) * 1000,
        layer=3)