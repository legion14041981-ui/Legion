"""
Supabase integration example for Legion framework.

This script demonstrates:
- Connecting to Supabase database
- Using LegionDatabase with Supabase
- Creating and managing agents with database storage
- Working with tasks using Edge Functions
- Using TaskQueue with database backend
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from legion import LegionCore, LegionAgent, LegionDatabase, TaskQueue, setup_logging

# Load environment variables
load_dotenv()


async def main():
    """Demonstrate Supabase integration with Legion."""
    
    # Setup logging
    logger = setup_logging("SupabaseExample", "INFO")
    logger.info("Starting Legion Supabase integration example")
    
    # Get Supabase credentials from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        logger.error("Please create a .env file with these values")
        return
    
    logger.info(f"Connecting to Supabase: {supabase_url}")
    
    # Create database connection
    try:
        db = LegionDatabase(supabase_url, supabase_key)
        logger.info("✓ Connected to Supabase successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return
    
    # Create Legion coordinator
    legion = LegionCore()
    logger.info("✓ LegionCore initialized")
    
    # Create agents
    logger.info("\nCreating agents with database storage...")
    
    agents_data = [
        {
            "agent_id": "supabase_agent_001",
            "name": "DataSyncAgent",
            "capabilities": ["data_sync", "backup"],
            "max_tasks": 5
        },
        {
            "agent_id": "supabase_agent_002",
            "name": "APIAgent",
            "capabilities": ["api_calls", "webhooks"],
            "max_tasks": 10
        },
        {
            "agent_id": "supabase_agent_003",
            "name": "ProcessorAgent",
            "capabilities": ["data_processing", "analytics"],
            "max_tasks": 3
        }
    ]
    
    # Create and register agents
    for agent_data in agents_data:
        agent = LegionAgent(**agent_data)
        
        # Register agent in database
        try:
            result = await db.create_agent(
                agent_id=agent.agent_id,
                name=agent.name,
                capabilities=agent.capabilities,
                status="active"
            )
            
            # Register with coordinator
            legion.register_agent(agent)
            
            logger.info(f"✓ Created and registered: {agent.name} ({agent.agent_id})")
        except Exception as e:
            logger.error(f"Failed to create agent {agent.name}: {e}")
    
    # List all agents from database
    logger.info("\nFetching agents from database...")
    try:
        all_agents = await db.get_all_agents()
        logger.info(f"Total agents in database: {len(all_agents)}")
        for agent in all_agents:
            logger.info(f"  - {agent['name']} ({agent['agent_id']}) - Status: {agent['status']}")
    except Exception as e:
        logger.error(f"Failed to fetch agents: {e}")
    
    # Initialize TaskQueue with database
    logger.info("\nInitializing TaskQueue...")
    task_queue = TaskQueue(db, check_interval=5)
    logger.info("✓ TaskQueue initialized")
    
    # Create sample tasks
    logger.info("\nCreating sample tasks...")
    
    tasks_data = [
        {
            "task_type": "data_sync",
            "description": "Sync customer database",
            "priority": 1,
            "data": {"source": "main_db", "target": "backup_db"}
        },
        {
            "task_type": "api_call",
            "description": "Fetch weather data",
            "priority": 2,
            "data": {"endpoint": "/api/weather", "location": "Moscow"}
        },
        {
            "task_type": "processing",
            "description": "Process analytics report",
            "priority": 1,
            "data": {"report_type": "monthly", "month": "December"}
        }
    ]
    
    for task_data in tasks_data:
        try:
            task_id = await db.create_task(**task_data)
            logger.info(f"✓ Created task: {task_data['description']} (ID: {task_id})")
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
    
    # Get pending tasks
    logger.info("\nFetching pending tasks...")
    try:
        pending_tasks = await db.get_pending_tasks()
        logger.info(f"Pending tasks: {len(pending_tasks)}")
        for task in pending_tasks:
            logger.info(f"  - [{task['priority']}] {task['description']} (Type: {task['task_type']})")
    except Exception as e:
        logger.error(f"Failed to fetch tasks: {e}")
    
    # Start task queue processing
    logger.info("\nStarting task queue processing...")
    await task_queue.start()
    logger.info("✓ Task queue started")
    
    # Let it process for a few seconds
    logger.info("Processing tasks for 5 seconds...")
    await asyncio.sleep(5)
    
    # Get queue statistics
    stats = task_queue.get_stats()
    logger.info(f"\nQueue Statistics:")
    logger.info(f"  Tasks processed: {stats['tasks_processed']}")
    logger.info(f"  Tasks failed: {stats['tasks_failed']}")
    logger.info(f"  Queue running: {stats['is_running']}")
    
    # Stop task queue
    logger.info("\nStopping task queue...")
    await task_queue.stop()
    logger.info("✓ Task queue stopped")
    
    # Final status check
    logger.info("\nFinal agent status:")
    try:
        all_agents = await db.get_all_agents()
        for agent in all_agents:
            logger.info(f"  {agent['name']}: {agent['status']}")
    except Exception as e:
        logger.error(f"Failed to get final status: {e}")
    
    logger.info("\nSupabase integration example completed successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
