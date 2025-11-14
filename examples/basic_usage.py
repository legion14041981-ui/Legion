"""
Basic usage example for Legion framework.

This script demonstrates the core functionality of Legion:
- Creating and managing agents
- Working with the coordinator (LegionCore)
- Using the logging system
- Basic task execution
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from legion import LegionCore, LegionAgent, setup_logging


async def main():
    """Demonstrate basic Legion functionality."""
    
    # Setup logging
    logger = setup_logging("BasicExample", "INFO")
    logger.info("Starting Legion basic usage example")
    
    # Create Legion coordinator
    logger.info("Creating LegionCore coordinator...")
    legion = LegionCore()
    
    # Create some agents
    logger.info("Creating agents...")
    
    agent1 = LegionAgent(
        agent_id="agent_001",
        name="DataProcessor",
        capabilities=["data_processing", "file_handling"],
        max_tasks=5
    )
    
    agent2 = LegionAgent(
        agent_id="agent_002",
        name="WebScraper",
        capabilities=["web_scraping", "api_calls"],
        max_tasks=3
    )
    
    agent3 = LegionAgent(
        agent_id="agent_003",
        name="EmailHandler",
        capabilities=["email_sending", "notifications"],
        max_tasks=10
    )
    
    # Register agents with coordinator
    logger.info("Registering agents with coordinator...")
    legion.register_agent(agent1)
    legion.register_agent(agent2)
    legion.register_agent(agent3)
    
    # Display registered agents
    logger.info(f"Total agents registered: {len(legion.agents)}")
    for agent_id, agent in legion.agents.items():
        logger.info(f"  - {agent.name} (ID: {agent_id}) - Capabilities: {', '.join(agent.capabilities)}")
    
    # Demonstrate agent status
    logger.info("\nAgent Status:")
    for agent in legion.agents.values():
        status = agent.get_status()
        logger.info(f"  {status['name']}: {status['status']} - Tasks: {status['current_tasks']}/{status['max_tasks']}")
    
    # Simulate starting agents
    logger.info("\nStarting agents...")
    agent1.start()
    agent2.start()
    agent3.start()
    
    logger.info("All agents started successfully!")
    
    # Display updated status
    logger.info("\nUpdated Agent Status:")
    for agent in legion.agents.values():
        status = agent.get_status()
        logger.info(f"  {status['name']}: {status['status']}")
    
    # Simulate some work
    logger.info("\nSimulating task execution...")
    await asyncio.sleep(1)
    
    # Stop agents
    logger.info("\nStopping agents...")
    agent1.stop()
    agent2.stop()
    agent3.stop()
    
    logger.info("All agents stopped successfully!")
    logger.info("Basic example completed successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
