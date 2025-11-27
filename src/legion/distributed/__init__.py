"""Distributed Execution Layer для Legion.

Опциональный модуль для распределенного выполнения агентов.

Требует:
  pip install ray[default]>=2.9.0
  pip install redis>=5.0.0
"""

try:
    from .distributed_core import DistributedCore
    from .distributed_worker import DistributedWorker
    from .distributed_launcher import launch_cluster
    
    DISTRIBUTED_AVAILABLE = True
except ImportError:
    DISTRIBUTED_AVAILABLE = False
    
    class DistributedCore:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "Distributed execution requires Ray. Install with: pip install ray[default]>=2.9.0"
            )

__all__ = [
    'DistributedCore',
    'DistributedWorker',
    'launch_cluster',
    'DISTRIBUTED_AVAILABLE'
]
