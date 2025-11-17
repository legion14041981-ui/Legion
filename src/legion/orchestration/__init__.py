"""Multi-agent orchestration for Legion.

Implements various orchestration patterns:
- Centralized (sequential, parallel, hierarchical)
- Decentralized (group chat, handoff)
- Federated (for distributed environments)
"""

from .orchestrator import MultiAgentOrchestrator
from .agents import PlanningAgent, ExecutionAgent, MonitoringAgent
from .patterns import (
    SequentialPattern,
    ParallelPattern,
    HierarchicalPattern,
    HandoffPattern
)

__all__ = [
    'MultiAgentOrchestrator',
    'PlanningAgent',
    'ExecutionAgent',
    'MonitoringAgent',
    'SequentialPattern',
    'ParallelPattern',
    'HierarchicalPattern',
    'HandoffPattern',
]
