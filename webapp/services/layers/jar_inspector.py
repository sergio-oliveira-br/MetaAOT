# webapp/services/layers/jar_inspector.py

import io
import logging
import zipfile

logger = logging.getLogger(__name__)

def inspect_jar(jar_bytes: bytes) -> dict:
    has_bytecode = False
    found_signatures = []

    with zipfile.ZipFile(io.BytesIO(jar_bytes)) as jar:
        for file_name in jar.namelist():

            # 1. Physical Validation of Executable Bytecode
            if file_name.endswith(".class"):
                has_bytecode = True

            # 2. Tracing architectural signatures within META-INF
            if file_name.startswith("META-INF/"):
                logger.debug("[JarInspector] Analyzing file: %s", file_name)

                # Role A: GraalVM’s native static standard
                if file_name.startswith("META-INF/native-image/"):
                    logger.info("[JarInspector] Evidence GraalVM detected: %s", file_name)
                    found_signatures.append("GRAALVM_NATIVE_IMAGE")

                # Role B: Programmatic standard of modern frameworks (SPI AOT of Spring 3+)
                elif file_name == "META-INF/spring/aot.factories":
                    logger.info("[JarInspector] Evidence SPRING_AOT detected: %s", file_name)
                    found_signatures.append("SPRING_AOT_FACTORIES")

                # Role C: Static annotation indexing standard (Quarkus / Jandex)
                elif file_name == "META-INF/jandex.idx":
                    logger.info("[JarInspector] Evidence JANDEX detected: %s", file_name)
                    found_signatures.append("JANDEX_INDEX")

    # case 1: JAR does not have a bytecode (.class) -> Configuration / Starter / BOM Artifact
    if not has_bytecode:
        logger.info("[JarInspector] No class file found. Classified as NOT_APPLICABLE.")
        return {
            "status": "NOT_APPLICABLE",
            "confidence": "HIGH",
            "reason": "Pure configuration or aggregator artifact containing no executable bytecode (.class files)."
        }

    # case 2: Has bytecode and has internally known AOT signatures
    if found_signatures:
        logger.info("[JarInspector] AOT signatures found: %s. Classified as EMBEDDED_METADATA.",found_signatures)
        return {
            "status": "EMBEDDED_METADATA",
            "confidence": "HIGH",
            "reason": f"Embedded AOT compile signatures detected inside the JAR: {', '.join(found_signatures)}."
        }

    # case 3: Has bytecode, but no internal signature was detected (go to Layer 2)
    logger.warning("[JarInspector] Contains bytecode but no internal AOT signature was detected.")
    return {
        "status": "PROCEED",
        "confidence": "LOW",
        "reason": "Contains bytecode but no embedded AOT evidence found. Structural fallback activated."
    }