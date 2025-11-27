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
=======
try:
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
except ImportError:
    # LangGraph not installed
    __all__ = []
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
