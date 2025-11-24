"""AiderAgent - Legion agent wrapper for Aider CLI-based code assistance."""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from legion.agents import LegionAgent
from legion.integrations.aider_bridge import AiderBridge

logger = logging.getLogger(__name__)


class AiderAgent(LegionAgent):
    """Legion agent that leverages Aider for code analysis, generation, and refactoring."""

    def __init__(self, agent_id: str, repo_path: str = r"C:\Legion", model: str = "openrouter/deepseek/deepseek-r1:free"):
        """Initialize AiderAgent.
        
        Args:
            agent_id: Unique agent identifier
            repo_path: Path to Legion repository
            model: LLM model to use
        """
        super().__init__(agent_id=agent_id, agent_type="aider")
        self.bridge = AiderBridge(repo_path=repo_path, model=model)
        self.repo_path = repo_path
        self.model = model
        self.task_history: list = []

    async def initialize(self) -> bool:
        """Initialize agent and start Aider bridge."""
        try:
            if not self.bridge.start():
                logger.error(f"{self.agent_id}: Failed to start AiderBridge")
                return False
            
            self.status = "initialized"
            logger.info(f"{self.agent_id}: AiderAgent initialized")
            return True
        except Exception as e:
            logger.error(f"{self.agent_id}: Initialization error: {str(e)}")
            return False

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task through Aider.
        
        Args:
            task: Task dictionary containing 'type' and 'description'
            
        Returns:
            Task result dictionary
        """
        task_type = task.get("type", "analysis")
        description = task.get("description", "")
        
        try:
            self.status = "executing"
            
            if task_type == "analyze":
                result = await self._analyze_code(description)
            elif task_type == "generate":
                result = await self._generate_code(description)
            elif task_type == "refactor":
                result = await self._refactor_code(description)
            elif task_type == "bugfix":
                result = await self._fix_bugs(description)
            elif task_type == "document":
                result = await self._generate_docs(description)
            else:
                result = await self._generic_query(description)
            
            self.status = "completed"
            self.task_history.append({"type": task_type, "timestamp": datetime.now().isoformat(), "result": result})
            
            return {
                "status": "success",
                "agent_id": self.agent_id,
                "task_type": task_type,
                "result": result
            }
        except Exception as e:
            logger.error(f"{self.agent_id}: Execution error: {str(e)}")
            self.status = "failed"
            return {"status": "error", "error": str(e)}

    async def _analyze_code(self, description: str) -> str:
        """Analyze code using Aider."""
        prompt = f"Analyze the following code requirement: {description}. Provide detailed analysis and recommendations."
        return self.bridge.send_command(prompt) or "[Analysis failed]"

    async def _generate_code(self, description: str) -> str:
        """Generate code using Aider."""
        prompt = f"Generate code for: {description}. Provide complete, working implementation with comments."
        return self.bridge.send_command(prompt) or "[Code generation failed]"

    async def _refactor_code(self, description: str) -> str:
        """Refactor existing code."""
        prompt = f"Refactor the code as follows: {description}. Maintain functionality while improving quality, performance, and readability."
        return self.bridge.send_command(prompt) or "[Refactoring failed]"

    async def _fix_bugs(self, description: str) -> str:
        """Fix bugs identified in the code."""
        prompt = f"Fix the following bug: {description}. Provide the corrected code with explanation."
        return self.bridge.send_command(prompt) or "[Bug fix failed]"

    async def _generate_docs(self, description: str) -> str:
        """Generate documentation."""
        prompt = f"Generate comprehensive documentation for: {description}. Include examples and usage."
        return self.bridge.send_command(prompt) or "[Documentation generation failed]"

    async def _generic_query(self, description: str) -> str:
        """Handle generic queries."""
        return self.bridge.send_command(description) or "[Query failed]"

    async def batch_execute(self, tasks: list) -> Dict[str, Any]:
        """Execute multiple tasks sequentially.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Aggregated results
        """
        results = []
        for task in tasks:
            result = await self.execute(task)
            results.append(result)
        
        return {
            "status": "batch_completed",
            "agent_id": self.agent_id,
            "total_tasks": len(tasks),
            "results": results
        }

    async def shutdown(self) -> None:
        """Shutdown agent and close Aider bridge."""
        try:
            self.bridge.close()
            self.status = "stopped"
            logger.info(f"{self.agent_id}: AiderAgent shutdown complete")
        except Exception as e:
            logger.error(f"{self.agent_id}: Shutdown error: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "bridge_status": self.bridge.get_status(),
            "tasks_executed": len(self.task_history),
            "timestamp": datetime.now().isoformat()
        }
