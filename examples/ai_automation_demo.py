"""Demo: AI-powered browser automation with Legion.

Demonstrates:
- Natural language task descriptions
- Automatic script generation
- Browser automation
- Self-healing
"""

import asyncio
import logging
import sys
import os

<<<<<<< HEAD
# Add parent directory to path
=======
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.legion.integration import LegionAISystem

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def demo_simple_navigation():
    """Demo: Simple browser navigation."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 1: Simple Navigation")
    logger.info("="*80)
    
    system = LegionAISystem()
    
    try:
        result = await system.execute_task(
<<<<<<< HEAD
            description="Navigate to example.com and take a screenshot",
=======
            description="Navigate to example.com",
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
            context={'url': 'https://example.com'}
        )
        
        logger.info(f"Result: {result}")
    finally:
        await system.cleanup()


<<<<<<< HEAD
async def demo_complex_automation():
    """Demo: Complex multi-step automation."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 2: Complex Automation")
    logger.info("="*80)
    
    system = LegionAISystem()
    
    try:
        result = await system.execute_task(
            description="""
            Go to Google, search for 'Playwright automation',
            click the first result, and extract the page title
            """,
            context={'url': 'https://google.com'}
        )
        
        logger.info(f"Result: {result}")
    finally:
        await system.cleanup()


async def demo_orchestration():
    """Demo: Multi-agent orchestration."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 3: Multi-Agent Orchestration")
    logger.info("="*80)
    
    system = LegionAISystem(config={'orchestration_enabled': True})
    
    try:
        result = await system.execute_task(
            description="Automate login to a test website",
            context={
                'url': 'https://example.com/login',
                'username': 'testuser',
                'password': 'testpass'
            }
        )
        
        logger.info(f"Result: {result}")
    finally:
        await system.cleanup()


async def demo_mcp_tools():
    """Demo: MCP tool registry."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 4: MCP Tool Registry")
    logger.info("="*80)
    
    system = LegionAISystem()
    
    if system.tool_registry:
        # List all tools
        tools = system.tool_registry.list_tools()
        logger.info(f"\nAvailable tools: {len(tools)}")
        
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")
        
        # Generate API documentation
        docs = system.tool_registry.generate_api_documentation()
        logger.info(f"\nAPI Documentation:\n{docs}")
    else:
        logger.warning("MCP not enabled")
    
    await system.cleanup()


async def main():
    """Run all demos."""
=======
async def main():
    """Run demos."""
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
    logger.info("\n" + "#"*80)
    logger.info("# Legion AI System - Demonstration Suite")
    logger.info("#"*80)
    
<<<<<<< HEAD
    # Check environment
=======
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("\n⚠ WARNING: OPENAI_API_KEY not set")
        logger.warning("Some demos will run in limited mode\n")
    
    try:
<<<<<<< HEAD
        # Run demos
        await demo_simple_navigation()
        await asyncio.sleep(2)
        
        await demo_complex_automation()
        await asyncio.sleep(2)
        
        await demo_orchestration()
        await asyncio.sleep(2)
        
        await demo_mcp_tools()
=======
        await demo_simple_navigation()
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
        
    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"\nDemo failed: {e}", exc_info=True)
    
    logger.info("\n" + "#"*80)
    logger.info("# Demo completed")
    logger.info("#"*80)


if __name__ == '__main__':
<<<<<<< HEAD
    asyncio.run(main())
=======
    asyncio.run(main())
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
