"""Quantum-Swarm Node Architecture v4.5.0

Автономная подсистема для динамического масштабирования агентов Legion.
Обеспечивает:
- Автоматическое создание и удаление узлов (QSN)
- Mesh-топологию с динамической маршрутизацией
- Event coherence между агентами
- Meta-learning capability
- Prometheus telemetry integration

Architecture:
    QSNNode: базовый вычислительный узел
    MeshRouter: сетевая топология и routing
    QSNControllerAgent: интеграция с Legion Orchestrator
    FabricEngine: управление жизненным циклом кластера
    EventCoherenceField: синхронизация состояний
    MetaArchitect: самопроектирование архитектуры

Usage:
    from legion.quantum_swarm import QSNNode, FabricEngine
    
    engine = FabricEngine(max_nodes=10)
    node = await engine.spawn_node()
    await node.execute_task(task_data)
"""

from typing import TYPE_CHECKING

__version__ = "4.5.0"
__author__ = "COMET FABRICATOR v4.5.0"
__all__ = [
    "QSNNode",
    "MeshRouter",
    "QSNControllerAgent",
    "FabricEngine",
    "QSNTelemetry",
    "EventCoherenceField",
    "MetaArchitect",
]

if TYPE_CHECKING:
    from .qsn_node import QSNNode
    from .qsn_mesh_router import MeshRouter
    from .qsn_controller_agent import QSNControllerAgent
    from .qsn_fabric_engine import FabricEngine
    from .qsn_telemetry import QSNTelemetry
    from .event_coherence_field import EventCoherenceField
    from .meta_architect import MetaArchitect


def __getattr__(name: str):
    """Lazy import для оптимизации загрузки модуля."""
    if name == "QSNNode":
        from .qsn_node import QSNNode
        return QSNNode
    elif name == "MeshRouter":
        from .qsn_mesh_router import MeshRouter
        return MeshRouter
    elif name == "QSNControllerAgent":
        from .qsn_controller_agent import QSNControllerAgent
        return QSNControllerAgent
    elif name == "FabricEngine":
        from .qsn_fabric_engine import FabricEngine
        return FabricEngine
    elif name == "QSNTelemetry":
        from .qsn_telemetry import QSNTelemetry
        return QSNTelemetry
    elif name == "EventCoherenceField":
        from .event_coherence_field import EventCoherenceField
        return EventCoherenceField
    elif name == "MetaArchitect":
        from .meta_architect import MetaArchitect
        return MetaArchitect
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
