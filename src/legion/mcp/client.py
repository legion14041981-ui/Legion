"""Legion MCP Client Implementation.

Provides an MCP client for connecting to external MCP servers
and consuming their tools and resources.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class LegionMCPClient:
    """MCP Client for consuming external MCP servers.
    
    Allows Legion to use tools and resources from other MCP-compatible
    systems like Browser MCP, Playwright MCP, etc.
    """
    
    def __init__(self, server_url: str, timeout: int = 30):
        """Initialize MCP client.
        
        Args:
            server_url: URL of the MCP server
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self._available_tools = []
        self._available_resources = []
        
        logger.info(f"Initialized MCP client for: {server_url}")
    
    async def connect(self):
        """Connect to the MCP server and discover capabilities."""
        try:
            # Discover available tools
            self._available_tools = await self.list_tools()
            self._available_resources = await self.list_resources()
            
            logger.info(
                f"Connected to MCP server: {len(self._available_tools)} tools, "
                f"{len(self._available_resources)} resources"
            )
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools available on the server.
        
        Returns:
            List of tool definitions
        """
        response = await self.client.post(
            f"{self.server_url}/tools/list",
            json={}
        )
        response.raise_for_status()
        return response.json().get('tools', [])
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        logger.info(f"Calling MCP tool: {name}")
        
        response = await self.client.post(
            f"{self.server_url}/tools/call",
            json={
                'name': name,
                'arguments': arguments
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all resources available on the server.
        
        Returns:
            List of resource definitions
        """
        response = await self.client.post(
            f"{self.server_url}/resources/list",
            json={}
        )
        response.raise_for_status()
        return response.json().get('resources', [])
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource from the server.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        response = await self.client.post(
            f"{self.server_url}/resources/read",
            json={'uri': uri}
        )
        response.raise_for_status()
        return response.json()
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        await self.client.aclose()
        logger.info("Disconnected from MCP server")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return [tool['name'] for tool in self._available_tools]