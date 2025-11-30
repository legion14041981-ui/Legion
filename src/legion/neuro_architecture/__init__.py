"""
Legion Neuro-Architecture Module - Ultra-Orchestrator v4.

Этот модуль реализует автоматическую эволюцию архитектуры LEGION:
- Генерация и тестирование нейроархитектур
- Применение адаптеров (LoRA, adapters)
- Model surgery (объединение, разделение, rewiring)
- Многокритериальная оптимизация
- Immutable реестр архитектур
- Mobile Agent (DroidRun-style)
- Humanistic Controller (Microsoft AI principles)
- Memory Manager для обучения
- Containment Policies для безопасности
"""

from .generator import ArchitectureGenerator, ArchitectureProposal
from .trainer import ProxyTrainer, TrainingMetrics
from .evaluator import MultiObjectiveEvaluator, EvaluationResult
from .registry import ArchitectureRegistry, ArchitectureSnapshot
from .adapters import LoRAAdapter, BaseAdapter, BottleneckAdapter
from .mobile_agent import AdaptiveUIInterpreter, MobileAgentOrchestrator, UIElement, Action
from .humanistic_controller import HumanisticController, MemoryManager, ContainmentPolicy
from .storage import CompactConfigEncoder, ArchitectureCache

__version__ = "4.0.0"
__all__ = [
    # Core components
    "ArchitectureGenerator",
    "ArchitectureProposal",
    "ProxyTrainer",
    "TrainingMetrics",
    "MultiObjectiveEvaluator",
    "EvaluationResult",
    "ArchitectureRegistry",
    "ArchitectureSnapshot",
    
    # Adapters
    "LoRAAdapter",
    "BaseAdapter",
    "BottleneckAdapter",
    
    # Mobile Agent (DroidRun-style)
    "AdaptiveUIInterpreter",
    "MobileAgentOrchestrator",
    "UIElement",
    "Action",
    
    # Humanistic Controller (Microsoft AI)
    "HumanisticController",
    "MemoryManager",
    "ContainmentPolicy",
    
    # Storage optimization
    "CompactConfigEncoder",
    "ArchitectureCache",
]
