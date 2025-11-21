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
            description="Navigate to example.com",
            context={'url': 'https://example.com'}
        )
        
        logger.info(f"Result: {result}")
    finally:
        await system.cleanup()


async def main():
    """Run demos."""
    logger.info("\n" + "#"*80)
    logger.info("# Legion AI System - Demonstration Suite")
    logger.info("#"*80)
    
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("\n⚠ WARNING: OPENAI_API_KEY not set")
        logger.warning("Some demos will run in limited mode\n")
    
    try:
        await demo_simple_navigation()
        
    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"\nDemo failed: {e}", exc_info=True)
    
    logger.info("\n" + "#"*80)
    logger.info("# Demo completed")
    logger.info("#"*80)


if __name__ == '__main__':
    asyncio.run(main())