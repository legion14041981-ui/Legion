"""Model Context Protocol (MCP) integration for Legion.

This module implements MCP server and client capabilities,
allowing Legion to integrate with any MCP-compatible AI system.
"""
from .server import LegionMCPServer
from .client import LegionMCPClient
from .tools import LegionToolRegistry
from .executor import CodeExecutionEngine

__all__ = [
    'LegionMCPServer',
    'LegionMCPClient',
    'LegionToolRegistry',
    'CodeExecutionEngine',
]
