"""Legion OS Integration Layer.

Provides OS-level capabilities for agents:
- Agent Workspace (isolation)
- Agent Identity (authentication)
- OS Interface (filesystem, terminal, etc.)
- Audit Trail (tamper-evident logging)
"""

from .workspace import LegionAgentWorkspace
from .identity import LegionAgentIdentity
from .os_interface import LegionOSInterface
from .audit import LegionAuditTrail

__all__ = [
    'LegionAgentWorkspace',
    'LegionAgentIdentity',
    'LegionOSInterface',
    'LegionAuditTrail'
]
