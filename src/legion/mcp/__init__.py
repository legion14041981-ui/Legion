"""Model Context Protocol (MCP) integration for Legion.

This module implements MCP server and client capabilities,
allowing Legion to integrate with any MCP-compatible AI system.
"""

from .server import LegionMCPServer
from .client import LegionMCPClient

__all__ = [
    'LegionMCPServer',
    'LegionMCPClient',
]

__version__ = '1.0.0'