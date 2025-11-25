"""Model Context Protocol (MCP) integration for Legion.

This module implements MCP server and client capabilities,
allowing Legion to integrate with any MCP-compatible AI system.
"""
from .server import LegionMCPServer
from .client import LegionMCPClient
from .tools import LegionToolRegistry
from .executor import CodeExecutionEngine
=======
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535

__all__ = [
    'LegionMCPServer',
    'LegionMCPClient',
<<<<<<< HEAD
    'LegionToolRegistry',
    'CodeExecutionEngine',
=======
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
]

__version__ = '1.0.0'
