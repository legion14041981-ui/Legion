"""AiderIntegration Demo - Complete example of Legion + Aider integration."""

import asyncio
import logging
from legion.integrations.aider_bridge import AiderBridge
from legion.agents.aider_agent import AiderAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_basic_bridge():
    """Demonstrate basic AiderBridge usage."""
    logger.info("=== Demo: Basic AiderBridge ===")
    
    with AiderBridge(repo_path=r"C:\Legion") as bridge:
        # Send single commands
        result = bridge.send_command("Analyze the Legion project structure and provide summary")
        print(f"Analysis Result:\n{result}\n")
        
        # Batch commands
        commands = [
            "Check the status of git repository",
            "List all Python files in src/legion",
            "Suggest improvements for code quality"
        ]
        batch_results = bridge.send_batch(commands)
        
        for cmd, resp in batch_results.items():
            print(f"Command: {cmd}")
            print(f"Response: {resp[:200]}...\n")


async def demo_aider_agent():
    """Demonstrate AiderAgent usage with Legion."""
    logger.info("=== Demo: AiderAgent ===")
    
    # Create agent
    agent = AiderAgent(agent_id="aider-1", repo_path=r"C:\Legion")
    
    # Initialize
    if await agent.initialize():
        logger.info(f"Agent initialized: {agent.status}")
        
        # Execute individual tasks
        tasks = [
            {"type": "analyze", "description": "Review the core.py module for design patterns"},
            {"type": "generate", "description": "Create a utility module for common helper functions"},
            {"type": "refactor", "description": "Improve variable naming conventions in agents.py"},
            {"type": "bugfix", "description": "Fix any potential threading issues in task queue"}
        ]
        
        for task in tasks:
            result = await agent.execute(task)
            print(f"\nTask: {task['type']}")
            print(f"Status: {result['status']}")
            print(f"Result Preview: {str(result.get('result', 'N/A'))[:150]}...")
        
        # Get agent status
        status = agent.get_status()
        print(f"\nAgent Final Status:")
        print(f"  Tasks Executed: {status['tasks_executed']}")
        print(f"  Status: {status['status']}")
        
        # Shutdown
        await agent.shutdown()
        logger.info("Agent shutdown complete")
    else:
        logger.error("Failed to initialize agent")


async def demo_batch_execution():
    """Demonstrate batch task execution."""
    logger.info("=== Demo: Batch Execution ===")
    
    agent = AiderAgent(agent_id="batch-agent", repo_path=r"C:\Legion")
    
    if await agent.initialize():
        # Batch tasks for comprehensive project review
        batch_tasks = [
            {"type": "analyze", "description": "Security: Check for potential vulnerabilities"},
            {"type": "analyze", "description": "Performance: Identify bottlenecks"},
            {"type": "generate", "description": "Create comprehensive API documentation"},
            {"type": "refactor", "description": "Optimize database query patterns"}
        ]
        
        batch_result = await agent.batch_execute(batch_tasks)
        
        print(f"\nBatch Results:")
        print(f"  Total Tasks: {batch_result['total_tasks']}")
        print(f"  Completed: {len(batch_result['results'])}")
        print(f"  Status: {batch_result['status']}")
        
        await agent.shutdown()


async def demo_event_callbacks():
    """Demonstrate event callback system."""
    logger.info("=== Demo: Event Callbacks ===")
    
    bridge = AiderBridge(repo_path=r"C:\Legion")
    
    def on_task_complete(data):
        logger.info(f"Callback: Task completed with data: {data}")
    
    def on_error(data):
        logger.error(f"Callback: Error occurred: {data}")
    
    bridge.register_callback("on_task_complete", on_task_complete)
    bridge.register_callback("on_error", on_error)
    
    if bridge.start():
        # Simulate task
        result = bridge.send_command("Perform static code analysis on the project")
        bridge.trigger_callback("on_task_complete", {"result": result[:100]})
        
        bridge.close()


async def main():
    """Run all demonstrations."""
    logger.info("Starting Legion + Aider Integration Demo")
    
    try:
        # Run demos sequentially
        await demo_basic_bridge()
        print("\n" + "="*80 + "\n")
        
        await demo_aider_agent()
        print("\n" + "="*80 + "\n")
        
        await demo_batch_execution()
        print("\n" + "="*80 + "\n")
        
        await demo_event_callbacks()
        
        logger.info("All demos completed successfully")
    except Exception as e:
        logger.error(f"Demo error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
