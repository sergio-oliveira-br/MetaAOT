# webapp/services/layers/models.py

from dataclasses import dataclass

@dataclass
class AOTAnalysisResult:
    package_name: str
    status: str
    confidence: str
    reason: str
    elapsed_ms: float
    layer: int