# MetaAOT: From POM to Binary: An Evidence-Based Assessment of GraalVM Native Image Readiness Using Maven Dependency Metadata

This repository contains the proof-of-concept developed as part of the **Master of Science in Cloud Computing** at the **National College of Ireland (NCI)**.

MetaAOT investigates whether structural metadata contained in Maven dependency ecosystems can provide early evidence of GraalVM Native Image readiness before native compilation takes place. The proposed approach performs a lightweight static inspection of dependency metadata to identify available evidence and potential evidence gaps.

---

## 📌 Project Overview

Native compilation introduces stricter constraints than traditional JVM execution. Dependencies relying on mechanisms such as reflection, dynamic proxies, or JNI may require additional configuration before they can be successfully compiled as native executables.

Current workflows typically discover these compatibility issues during native compilation or through runtime tracing. MetaAOT explores a complementary **Shift-Left** approach by applying **Software Composition Analysis** principles to inspect dependency metadata before execution or compilation.

The framework analyses Maven dependency graphs and classifies each dependency according to the structural evidence available within the Native Image ecosystem.

---

## 🧭 Scope and Project Status

This repository houses the structural tokenizers, routing logic, and verification services built to test the research hypothesis.

* **Status:** Student Research Project / Functional Academic Prototype.
* **Approach:** Low-overhead static analysis using manifest ingestion, bypassing the need for heavy local compilation environments or dynamic runtime tracing agents.

---

## 🎓 Academic Affiliation

This framework was developed purely for educational and academic research purposes at the NCI to analyze modern cloud-native software supply chain architectures.
