"""CI-Healer Agent подмодули.

Вспомогательные компоненты для автономного исправления CI/CD ошибок.
"""

from .detectors import ErrorDetector
from .patch_engine import PatchEngine
from .dependency_doctor import DependencyDoctor
from .semantic_indexer import SemanticIndexer
from .risk_analyzer import RiskAnalyzer
from .telemetry import Telemetry

__all__ = [
    "ErrorDetector",
    "PatchEngine",
    "DependencyDoctor",
    "SemanticIndexer",
    "RiskAnalyzer",
    "Telemetry"
]

__version__ = "2.0.0"
