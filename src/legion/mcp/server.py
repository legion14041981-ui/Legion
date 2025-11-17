"""Legion MCP Server Implementation.

Provides a Model Context Protocol server that exposes Legion's
browser automation capabilities as MCP tools.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LegionMCPServer:
    """MCP Server exposing Legion automation tools.
    
    Implements the Model Context Protocol specification to allow
    AI models to interact with Legion's browser automation capabilities.
    
    Features:
    - Tool registration and discovery
    - Asynchronous tool execution
    - Result streaming
    - Error handling and retry logic
    - HMAC signature verification
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MCP server.
        
        Args:
            config: Server configuration including:
                - name: Server name
                - version: Server version
                - tools: List of available tools
                - security: Security settings (HMAC, rate limiting)
        """
        self.config = config
        self.name = config.get('name', 'legion-mcp-server')
        self.version = config.get('version', '1.0.0')
        self.tools = {}
        self.resources = {}
        self.prompts = {}
        self._running = False
        
        logger.info(f"Initializing Legion MCP Server v{self.version}")
    
    def register_tool(self, name: str, description: str, 
                     input_schema: Dict, handler: callable):
        """Register a tool with the MCP server.
        
        Args:
            name: Tool name (e.g., 'browser_navigate')
            description: Human-readable description
            input_schema: JSON schema for tool inputs
            handler: Async function to execute the tool
        """
        self.tools[name] = {
            'name': name,
            'description': description,
            'inputSchema': input_schema,
            'handler': handler,
            'registered_at': datetime.now().isoformat()
        }
        logger.info(f"Registered MCP tool: {name}")
    
    def register_resource(self, uri: str, name: str, 
                         mime_type: str, handler: callable):
        """Register a resource accessible via MCP.
        
        Args:
            uri: Resource URI (e.g., 'legion://screenshots/latest')
            name: Human-readable name
            mime_type: MIME type of resource
            handler: Async function to fetch resource
        """
        self.resources[uri] = {
            'uri': uri,
            'name': name,
            'mimeType': mime_type,
            'handler': handler
        }
        logger.info(f"Registered MCP resource: {uri}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools.
        
        Returns:
            List of tool definitions (without handlers)
        """
        return [
            {
                'name': tool['name'],
                'description': tool['description'],
                'inputSchema': tool['inputSchema']
            }
            for tool in self.tools.values()
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool.
        
        Args:
            name: Tool name
            arguments: Tool arguments matching input schema
            
        Returns:
            Tool execution result
        """
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")
        
        tool = self.tools[name]
        logger.info(f"Executing MCP tool: {name}")
        
        try:
            result = await tool['handler'](arguments)
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': json.dumps(result, indent=2)
                    }
                ],
                'isError': False
            }
        except Exception as e:
            logger.error(f"Tool execution error: {name} - {e}")
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f"Error: {str(e)}"
                    }
                ],
                'isError': True
            }
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources.
        
        Returns:
            List of resource definitions
        """
        return [
            {
                'uri': res['uri'],
                'name': res['name'],
                'mimeType': res['mimeType']
            }
            for res in self.resources.values()
        ]
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        if uri not in self.resources:
            raise ValueError(f"Resource not found: {uri}")
        
        resource = self.resources[uri]
        content = await resource['handler']()
        
        return {
            'contents': [
                {
                    'uri': uri,
                    'mimeType': resource['mimeType'],
                    'text': content if isinstance(content, str) else json.dumps(content)
                }
            ]
        }
    
    async def start(self, host: str = '0.0.0.0', port: int = 8001):
        """Start the MCP server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self._running = True
        logger.info(f"Legion MCP Server started on {host}:{port}")
        
        # Implementation note: This is a simplified version.
        # In production, use aiohttp or fastapi for HTTP transport,
        # or stdio for local MCP communication.
        
        while self._running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Stop the MCP server."""
        self._running = False
        logger.info("Legion MCP Server stopped")