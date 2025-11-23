# -*- coding: utf-8 -*-
"""
Legion Specialized Agents Example

Demonstration of specialized agents:
- EmailAgent: email sending via SMTP
- GoogleSheetsAgent: work with Google Sheets
- Agent integration for complex tasks
"""
import asyncio
import os
from pathlib import Path

# Add parent directory to path for legion module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from legion import LegionCore, LegionAgent, setup_logging


async def main():
    """Demonstrate specialized agents in Legion."""
    
    logger = setup_logging("SpecializedAgentsExample", "INFO")
    logger.info("Starting Legion Specialized Agents example")
    
    # Create Legion coordinator
    legion = LegionCore()
    logger.info("LegionCore initialized")
    
    # Create specialized agents
    logger.info("\nCreating specialized agents...")
    
    # Email Agent
    email_agent_config = {
        "agent_id": "email_agent_001",
        "name": "EmailAgent",
        "capabilities": ["send_email", "receive_email", "email_scheduling"],
        "max_tasks": 10
    }
    
    email_agent = LegionAgent(
        agent_id=email_agent_config["agent_id"],
        name=email_agent_config["name"],
        capabilities=email_agent_config["capabilities"],
        max_tasks=email_agent_config["max_tasks"]
    )
    legion.register_agent(email_agent)
    logger.info(f"Registered: {email_agent.name}")
    
    # Google Sheets Agent
    sheets_agent_config = {
        "agent_id": "sheets_agent_001",
        "name": "GoogleSheetsAgent",
        "capabilities": ["read_sheets", "write_sheets", "create_sheets", "data_sync"],
        "max_tasks": 5
    }
    
    sheets_agent = LegionAgent(
        agent_id=sheets_agent_config["agent_id"],
        name=sheets_agent_config["name"],
        capabilities=sheets_agent_config["capabilities"],
        max_tasks=sheets_agent_config["max_tasks"]
    )
    legion.register_agent(sheets_agent)
    logger.info(f"Registered: {sheets_agent.name}")
    
    # Data Processing Agent
    processor_config = {
        "agent_id": "processor_001",
        "name": "DataProcessorAgent",
        "capabilities": ["process_data", "analyze", "transform", "export"],
        "max_tasks": 15
    }
    
    processor_agent = LegionAgent(
        agent_id=processor_config["agent_id"],
        name=processor_config["name"],
        capabilities=processor_config["capabilities"],
        max_tasks=processor_config["max_tasks"]
    )
    legion.register_agent(processor_agent)
    logger.info(f"Registered: {processor_agent.name}")
    
    # List all registered agents
    logger.info("\nRegistered agents:")
    for agent in legion.get_agents():
        logger.info(f" - {agent.name}: {', '.join(agent.capabilities)}")
    
    # Demonstrate agent capabilities
    logger.info("\nAgent capabilities demonstration:")
    
    # Email Agent tasks
    logger.info("\nEmail Agent - available operations:")
    logger.info(" - Send emails via SMTP")
    logger.info(" - Receive and process emails")
    logger.info(" - Schedule email campaigns")
    
    # Sheets Agent tasks
    logger.info("\nGoogle Sheets Agent - available operations:")
    logger.info(" - Read data from Google Sheets")
    logger.info(" - Write and update sheets")
    logger.info(" - Create new spreadsheets")
    logger.info(" - Sync data with external systems")
    
    # Processor Agent tasks
    logger.info("\nData Processor Agent - available operations:")
    logger.info(" - Process structured data")
    logger.info(" - Perform data analysis")
    logger.info(" - Transform data formats")
    logger.info(" - Export results")
    
    # Demonstrate agent coordination
    logger.info("\nAgent coordination example:")
    logger.info("1. Processor reads data from Sheets")
    logger.info("2. Processor analyzes the data")
    logger.info("3. Processor exports results")
    logger.info("4. Email agent sends notification")
    
    logger.info("\nSpecialized Agents example completed successfully!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
