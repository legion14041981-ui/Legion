"""
Legion Neuro-Architecture Module - Ultra-Orchestrator v4.

Этот модуль реализует автоматическую эволюцию архитектуры LEGION:
- Генерация и тестирование нейроархитектур
- Применение адаптеров (LoRA, adapters)
- Model surgery (объединение, разделение, rewiring)
- Многокритериальная оптимизация
- Immutable реестр архитектур
"""

from .generator import ArchitectureGenerator, ArchitectureProposal
from .trainer import ProxyTrainer, TrainingMetrics
from .evaluator import MultiObjectiveEvaluator, EvaluationResult
from .registry import ArchitectureRegistry, ArchitectureSnapshot
from .adapters import LoRAAdapter, BaseAdapter

__version__ = "4.0.0"
__all__ = [
    "ArchitectureGenerator",
    "ArchitectureProposal",
    "ProxyTrainer",
    "TrainingMetrics",
    "MultiObjectiveEvaluator",
    "EvaluationResult",
    "ArchitectureRegistry",
    "ArchitectureSnapshot",
    "LoRAAdapter",
    "BaseAdapter",
]
