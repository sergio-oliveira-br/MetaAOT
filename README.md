# MetaAOT: From POM to Binary: An Evidence-Based Assessment of GraalVM Native Image Readiness Using Maven Dependency Metadata

This repository contains the proof-of-concept developed as part of the **Master of Science in Cloud Computing** at the **National College of Ireland (NCI)**.

MetaAOT investigates whether structural metadata contained in Maven dependency ecosystems can provide early evidence of GraalVM Native Image readiness before native compilation takes place. The proposed approach performs a lightweight static inspection of dependency metadata to identify available evidence and potential evidence gaps.

---

## Project Overview

Native compilation introduces stricter constraints than traditional JVM execution. Dependencies relying on mechanisms such as reflection, dynamic proxies, or JNI may require additional configuration before they can be successfully compiled as native executables.

Current workflows typically discover these compatibility issues during native compilation or through runtime tracing. MetaAOT explores a complementary **Shift-Left** approach by applying **Software Composition Analysis** principles to inspect dependency metadata before execution or compilation.

The framework analyses Maven dependency graphs and classifies each dependency according to the structural evidence available within the Native Image ecosystem.

---

# Evidence Classification

Each dependency is evaluated using a layered evidence model based on Native Image metadata and structural inspection.

| Classification | Description |
|----------------|-------------|
| **Embedded Metadata** | Native Image configuration was found directly inside the dependency artifact. |
| **Official Metadata** | The analyzed version matches metadata officially published by the GraalVM Reachability Metadata Repository. |
| **Version Not Tested** | The dependency exists in the official repository, but the exact version has not been validated. The closest compatible version within the same major release is used as structural evidence. |
| **Indirect Evidence Only** | No direct metadata exists for the dependency, but supporting evidence was identified through related or transitive dependencies. This evidence should be interpreted conservatively and does not represent verified compatibility. |
| **Not Applicable** | The dependency does not require Native Image metadata evaluation, for example because it contains no Java bytecode or is explicitly marked as not requiring metadata. |
| **Evidence Not Found** | No structural Native Image metadata could be identified after all inspection stages were completed. Additional investigation may be required before native compilation. |

The final report summarizes the overall dependency ecosystem and highlights evidence gaps that deserve further investigation before attempting native compilation.

---

# Analysis Workflow

For every dependency identified in the Software Bill of Materials (SBOM), MetaAOT performs the following inspection sequence:

1. Generate an SBOM from the target Maven project.
2. Build the complete dependency graph.
3. Normalize dependency coordinates.
4. Download dependency artifacts directly into memory.
5. Verify whether the artifact contains Java bytecode.
6. Inspect embedded Native Image metadata.
7. Query the GraalVM Reachability Metadata Repository.
8. Evaluate compatible versions when an exact match is unavailable.
9. Search for indirect evidence through the dependency graph.
10. Produce an evidence-based readiness assessment.

The entire process is performed through static analysis without executing application code or invoking the GraalVM Native Image compiler.

---

# Scope

MetaAOT is an **evidence-based structural inspection framework**.

The framework is designed to complement existing Native Image workflows by providing earlier visibility into dependency ecosystems.

It does **not**:

- Predict whether a project will successfully compile as a Native Image.
- Reproduce GraalVM's internal reachability analysis.
- Replace native compilation.
- Replace runtime validation performed by the GraalVM Native Image Agent.

Instead, it provides a transparent and reproducible assessment of dependency ecosystems before execution or native compilation begins.

---

# Academic Context

This repository accompanies the research presented in the dissertation:

> **From POM to Binary: From POM to Binary: An Evidence-Based Assessment of GraalVM Native Image Readiness Using Maven Dependency Metadata**

The research investigates whether structural metadata available in Maven dependency graphs can provide early evidence of Native Image readiness.

The proposed inspection model extends Software Composition Analysis concepts beyond traditional security and license analysis by introducing an evidence-based approach for evaluating Ahead-of-Time migration readiness.

This framework was developed exclusively for academic research purposes.

It demonstrates the feasibility of an evidence-based structural inspection model and serves as the experimental platform used throughout the controlled case studies presented in the dissertation.
