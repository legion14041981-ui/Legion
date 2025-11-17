"""Integration module for Legion AI enhancements.

Connects MCP, AI script generation, browser automation, and orchestration.
"""

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from .core import LegionCore
from .mcp.server import LegionMCPServer
from .mcp.tools import LegionToolRegistry
from .mcp.executor import CodeExecutionEngine
from .ai.script_generator import ScriptGenerator
from .agents.browser_agent import PlaywrightBrowserAgent
from .orchestration.orchestrator import MultiAgentOrchestrator
from .orchestration.agents import PlanningAgent, ExecutionAgent, MonitoringAgent

logger = logging.getLogger(__name__)


class LegionAISystem:
    """Integrated Legion AI System.
    
    Combines all AI enhancements into a unified system:
    - MCP protocol for tool integration
    - AI-powered script generation
    - Browser automation with Playwright
    - Multi-agent orchestration
    - Self-healing capabilities
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize Legion AI System.
        
        Args:
            config: System configuration
        """
        self.config = config or {}
        
        # Core components
        self.core = LegionCore()
        
        # AI components
        self.script_generator = None
        if os.getenv('OPENAI_API_KEY'):
            self.script_generator = ScriptGenerator()
            logger.info("✓ AI Script Generator initialized")
        else:
            logger.warning("⚠ OPENAI_API_KEY not set, script generation disabled")
        
        # Browser automation
        self.browser_agent = None
        try:
            self.browser_agent = PlaywrightBrowserAgent(
                agent_id='main-browser',
                config={
                    'browser': os.getenv('PLAYWRIGHT_BROWSER', 'chromium'),
                    'headless': os.getenv('PLAYWRIGHT_HEADLESS', 'true') == 'true'
                }
            )
            logger.info("✓ Browser Agent initialized")
        except ImportError:
            logger.warning("⚠ Playwright not installed, browser automation disabled")
        
        # MCP components
        self.mcp_server = None
        self.tool_registry = None
        self.code_executor = None
        
        if self.config.get('mcp_enabled', os.getenv('MCP_ENABLED', 'true') == 'true'):
            self._initialize_mcp()
        
        # Orchestration
        self.orchestrator = None
        if self.config.get('orchestration_enabled', True):
            self._initialize_orchestration()
        
        logger.info("=" * 60)
        logger.info("Legion AI System initialized successfully")
        logger.info("=" * 60)
    
    def _initialize_mcp(self):
        """Initialize MCP components."""
        self.mcp_server = LegionMCPServer({
            'name': 'legion-ai-server',
            'version': '1.0.0'
        })
        
        self.tool_registry = LegionToolRegistry()
        self.code_executor = CodeExecutionEngine(self.tool_registry)
        
        # Register browser tools
        if self.browser_agent:
            self._register_browser_tools()
        
        logger.info("✓ MCP Server initialized")
    
    def _register_browser_tools(self):
        """Register browser automation tools with MCP."""
        async def browser_navigate(url: str, wait_until: str = 'load'):
            return await self.browser_agent.execute({
                'action': 'navigate',
                'params': {'url': url, 'wait_until': wait_until}
            })
        
        async def browser_click(selector: str):
            return await self.browser_agent.execute({
                'action': 'click',
                'params': {'selector': selector}
            })
        
        async def browser_screenshot(path: str = None):
            return await self.browser_agent.execute({
                'action': 'screenshot',
                'params': {'path': path}
            })
        
        async def browser_extract(selector: str = None, attribute: str = 'textContent'):
            return await self.browser_agent.execute({
                'action': 'extract',
                'params': {'selector': selector, 'attribute': attribute}
            })
        
        # Register tools
        self.tool_registry.register(
            'browser_navigate',
            browser_navigate,
            'Navigate to URL',
            category='browser',
            examples=['await tools.execute("browser_navigate", url="https://example.com")']
        )
        
        self.tool_registry.register(
            'browser_click',
            browser_click,
            'Click element by selector',
            category='browser',
            examples=['await tools.execute("browser_click", selector="#submit-btn")']
        )
        
        self.tool_registry.register(
            'browser_screenshot',
            browser_screenshot,
            'Take screenshot',
            category='browser'
        )
        
        self.tool_registry.register(
            'browser_extract',
            browser_extract,
            'Extract data from page',
            category='browser'
        )
        
        logger.info("✓ Registered 4 browser tools")
    
    def _initialize_orchestration(self):
        """Initialize multi-agent orchestration."""
        try:
            self.orchestrator = MultiAgentOrchestrator()
            
            # Create agents
            planning_agent = PlanningAgent(self.script_generator)
            execution_agent = ExecutionAgent(self.browser_agent) if self.browser_agent else None
            monitoring_agent = MonitoringAgent(self.script_generator)
            
            # Register agents
            self.orchestrator.register_agent('planning', planning_agent, 'planning')
            if execution_agent:
                self.orchestrator.register_agent('execution', execution_agent, 'execution')
            self.orchestrator.register_agent('monitoring', monitoring_agent, 'monitoring')
            
            # Build workflow
            pattern = os.getenv('ORCHESTRATION_PATTERN', 'hierarchical')
            if pattern == 'sequential' and execution_agent:
                self.orchestrator.build_sequential_workflow(['planning', 'execution'])
            elif pattern == 'hierarchical' and execution_agent:
                self.orchestrator.build_hierarchical_workflow('planning', ['execution'])
            
            logger.info(f"✓ Orchestration initialized (pattern: {pattern})")
        except ImportError:
            logger.warning("⚠ LangGraph not installed, orchestration disabled")
    
    async def execute_task(self, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a task using AI automation.
        
        Args:
            description: Natural language task description
            context: Optional context (URL, etc.)
            
        Returns:
            Task execution results
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Executing task: {description}")
        logger.info(f"{'='*60}\n")
        
        task = {
            'description': description,
            'context': context or {},
            'timestamp': asyncio.get_event_loop().time()
        }
        
        # Use orchestrator if available
        if self.orchestrator:
            try:
                result = await self.orchestrator.execute(task)
                logger.info("✓ Task completed via orchestration")
                return result
            except Exception as e:
                logger.error(f"Orchestration failed: {e}")
        
        # Fallback: direct execution
        if self.script_generator and self.browser_agent:
            # Generate script
            script_result = await self.script_generator.generate_playwright_script(
                description,
                context
            )
            
            if script_result.get('success'):
                # Execute generated script
                # Note: In production, use code_executor for sandboxed execution
                logger.info("✓ Script generated successfully")
                return {
                    'success': True,
                    'script': script_result.get('code'),
                    'method': 'direct_generation'
                }
        
        return {
            'success': False,
            'error': 'No execution method available'
        }
    
    async def start_mcp_server(self):
        """Start MCP server."""
        if self.mcp_server:
            host = os.getenv('MCP_SERVER_HOST', '0.0.0.0')
            port = int(os.getenv('MCP_SERVER_PORT', '8001'))
            await self.mcp_server.start(host, port)
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.browser_agent:
            await self.browser_agent.cleanup()
        if self.mcp_server:
            await self.mcp_server.stop()
        logger.info("Legion AI System cleaned up")
