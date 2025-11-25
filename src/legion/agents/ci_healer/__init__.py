"""CI-Healer Agent подмодули.

Подмодули для автономного исправления CI/CD ошибок:
- detectors: Детекторы ошибок из логов
- patch_engine: AST-based генератор патчей
- dependency_doctor: Авто-фикс зависимостей
- semantic_indexer: Поиск релевантных файлов
- risk_analyzer: Анализ риска патчей
- telemetry: Slack + S3 логирование
"""

from .detectors import ErrorDetector, CIProblem
from .patch_engine import PatchEngine, Patch
from .dependency_doctor import DependencyDoctor
from .semantic_indexer import SemanticIndexer
from .risk_analyzer import RiskAnalyzer
from .telemetry import Telemetry

__all__ = [
    'ErrorDetector',
    'CIProblem',
    'PatchEngine',
    'Patch',
    'DependencyDoctor',
    'SemanticIndexer',
    'RiskAnalyzer',
    'Telemetry'
]

__version__ = "2.0.0"
