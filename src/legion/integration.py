"""Integration module for Legion AI enhancements.
Connects MCP, AI script generation, browser automation, and orchestration.
"""

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from .core import LegionCore

# Placeholder imports - will be available after full merge
try:
    from .mcp.server import LegionMCPServer
    from .mcp.tools import LegionToolRegistry
    from .mcp.executor import CodeExecutionEngine
except ImportError:
    LegionMCPServer = None
    LegionToolRegistry = None
    CodeExecutionEngine = None

try:
    from .ai.script_generator import ScriptGenerator
except ImportError:
    ScriptGenerator = None

try:
    from .agents.browser_agent import PlaywrightBrowserAgent
except ImportError:
    PlaywrightBrowserAgent = None

try:
    from .orchestration.orchestrator import MultiAgentOrchestrator
    from .orchestration.agents import PlanningAgent, ExecutionAgent, MonitoringAgent
except ImportError:
    MultiAgentOrchestrator = None
    PlanningAgent = None
    ExecutionAgent = None
    MonitoringAgent = None

logger = logging.getLogger(__name__)


class LegionAISystem:
    """Integrated Legion AI System.
    
    Combines all Legion components into a unified interface.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the Legion AI System.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.core = LegionCore()
        self.mcp_server = None
        self.script_generator = None
        self.browser_agent = None
        self.orchestrator = None
        
        # Initialize optional components
        if LegionMCPServer:
            self.mcp_server = LegionMCPServer()
        if ScriptGenerator:
            self.script_generator = ScriptGenerator()
        if PlaywrightBrowserAgent:
            self.browser_agent = PlaywrightBrowserAgent()
        if MultiAgentOrchestrator:
            self.orchestrator = MultiAgentOrchestrator()
        
        logger.info("Legion AI System v2.0 initialized")
    
    async def execute_task(self, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a task.
        
        Args:
            description: Task description
            context: Optional context
            
        Returns:
            Task results
        """
        logger.info(f"Task: {description}")
        
        # Use orchestrator if available
        if self.orchestrator:
            return await self.orchestrator.execute(description, context)
        
        # Fallback to core execution
        result = await self.core.execute(description, context)
        return {
            'success': result.get('success', False),
            'result': result,
            'description': description
        }
    
    async def generate_script(self, prompt: str, language: str = "python") -> Dict[str, Any]:
        """Generate a script using AI.
        
        Args:
            prompt: Script generation prompt
            language: Target programming language
            
        Returns:
            Generated script and metadata
        """
        if not self.script_generator:
            return {
                'success': False,
                'error': 'Script generator not available'
            }
        
        return await self.script_generator.generate(prompt, language)
    
    async def browse(self, url: str, actions: Optional[list] = None) -> Dict[str, Any]:
        """Perform browser automation.
        
        Args:
            url: URL to navigate to
            actions: Optional list of actions to perform
            
        Returns:
            Browser session results
        """
        if not self.browser_agent:
            return {
                'success': False,
                'error': 'Browser agent not available'
            }
        
        await self.browser_agent.navigate(url)
        if actions:
            for action in actions:
                await self.browser_agent.execute_action(action)
        
        return {
            'success': True,
            'url': url,
            'actions_performed': len(actions) if actions else 0
        }
    
    async def start_mcp_server(self):
        """Start MCP server."""
        if self.mcp_server:
            host = os.getenv('MCP_SERVER_HOST', '0.0.0.0')
            port = int(os.getenv('MCP_SERVER_PORT', '8001'))
            await self.mcp_server.start(host, port)
            logger.info(f"MCP server started on {host}:{port}")
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.browser_agent:
            await self.browser_agent.cleanup()
        if self.mcp_server:
            await self.mcp_server.stop()
        logger.info("Legion AI System cleaned up")


# Convenience function for quick system access
def create_legion_system(config: Optional[Dict] = None) -> LegionAISystem:
    """Create a Legion AI System instance.
    
    Args:
        config: Optional configuration
        
    Returns:
        LegionAISystem instance
    """
    return LegionAISystem(config)
