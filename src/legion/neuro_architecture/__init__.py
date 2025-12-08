"""
Neuro-Architecture Module - Autonomous Architecture Evolution.

v4.1.0 additions:
- NeuroLearningLoop: Self-improvement cycle
- SelfImprover: Code patch generation
- AdaptiveRefactor: Architecture modernization
- Memory v4.1: L4 semantic cache
- Mobile Agent v4.1: Enhanced UI automation
- Watchdog v4.1: 20 monitoring criteria
"""
from typing import Optional

from legion.neuro_architecture.generator import (
    ArchitectureGenerator,
    ArchitectureProposal
)
from legion.neuro_architecture.trainer import (
    ProxyTrainer,
    TrainingMetrics
)
from legion.neuro_architecture.evaluator import (
    MultiObjectiveEvaluator,
    EvaluationResult
)
from legion.neuro_architecture.registry import (
    ArchitectureRegistry,
    ArchitectureSnapshot
)
from legion.neuro_architecture.adapters import (
    LoRAAdapter,
    BottleneckAdapter
)
from legion.neuro_architecture.mobile_agent import (
    AdaptiveUIInterpreter,
    MobileAgentOrchestrator,
    UIElement,
    Action
)
from legion.neuro_architecture.humanistic_controller import (
    HumanisticController,
    MemoryManager,
    ContainmentPolicy,
    DecisionRecord
)
from legion.neuro_architecture.storage import (
    CompactConfigEncoder,
    ArchitectureCache
)
from legion.neuro_architecture.watchdog import (
    PerformanceWatchdog,
    HealthCheckResult,
    MetricThreshold
)

# v4.1.0 new imports
from legion.neuro_architecture.neuro_learning_loop import (
    NeuroLearningLoop,
    MetricsSnapshot,
    Issue,
    ImprovementPatch
)
from legion.neuro_architecture.self_improver import (
    SelfImprover,
    CodeMetrics,
    CodePatch
)

__all__ = [
    # v4.0.0
    'ArchitectureGenerator',
    'ArchitectureProposal',
    'ProxyTrainer',
    'TrainingMetrics',
    'MultiObjectiveEvaluator',
    'EvaluationResult',
    'ArchitectureRegistry',
    'ArchitectureSnapshot',
    'LoRAAdapter',
    'BottleneckAdapter',
    'AdaptiveUIInterpreter',
    'MobileAgentOrchestrator',
    'UIElement',
    'Action',
    'HumanisticController',
    'MemoryManager',
    'ContainmentPolicy',
    'DecisionRecord',
    'CompactConfigEncoder',
    'ArchitectureCache',
    'PerformanceWatchdog',
    'HealthCheckResult',
    'MetricThreshold',
    # v4.1.0
    'NeuroLearningLoop',
    'MetricsSnapshot',
    'Issue',
    'ImprovementPatch',
    'SelfImprover',
    'CodeMetrics',
    'CodePatch',
]

__version__ = '4.1.0'
