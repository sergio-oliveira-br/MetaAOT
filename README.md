# MetaAOT: Dependency Compatibility Evaluator for Ahead-of-Time Compilation

This repository contains the prototype codebase for an academic research project developed as part of the Master of Science in Cloud Computing curriculum at the **National College of Ireland (NCI)**. 

The objective of this project is to explore how Software Bill of Materials (SBOM) metadata can be used to analyze software dependency compatibility before initiating build lifecycles.

---

## 📌 Project Overview

Migrating traditional Java applications to Ahead-of-Time (AOT) environments introduces the strict **Closed-World Assumption**. In these runtime scenarios, dynamic features like reflection or dynamic proxies can cause system failures if they are not explicitly configured. 

To explore how developers can gain visibility into these ecosystem constraints early, this academic prototype implements a binary triage framework:
* **Complete Map (100%):** Every analyzed dependency node contains a verified path or non-applicability flag within the research registers, indicating a stable configuration path.
* **Action Required (< 100%):** Any unmapped metadata triggers a unified warning signal, indicating that human intervention would be required to manually inject configuration files before attempting compilation.

---

## 🧭 Scope and Project Status

This repository houses the structural tokenizers, routing logic, and verification services built to test the research hypothesis.

* **Status:** Student Research Project / Functional Academic Prototype.
* **Approach:** Low-overhead static analysis using manifest ingestion, bypassing the need for heavy local compilation environments or dynamic runtime tracing agents.

---

## 🎓 Academic Affiliation

This framework was developed purely for educational and academic research purposes at the NCI to analyze modern cloud-native software supply chain architectures.
