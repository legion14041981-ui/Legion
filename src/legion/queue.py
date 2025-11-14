"""Task Queue Module for Legion

Handles task queue processing and distribution to agents.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskQueue:
    """Task queue for managing and distributing tasks to agents."""
    
    def __init__(self, db):
        """Initialize task queue with database connection.
        
        Args:
            db: LegionDatabase instance
        """
        self.db = db
        self.running = False
        self._processing_task = None
        
    async def start(self):
        """Start the task queue processing loop."""
        if self.running:
            logger.warning("Task queue is already running")
            return
            
        self.running = True
        logger.info("Task queue started")
        
        # Start background processing
        self._processing_task = asyncio.create_task(self._process_loop())
        
    async def stop(self):
        """Stop the task queue processing loop."""
        self.running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Task queue stopped")
        
    async def _process_loop(self):
        """Background loop for processing pending tasks."""
        while self.running:
            try:
                await self.process_pending_tasks()
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Error in task processing loop: {e}")
                await asyncio.sleep(10)  # Wait longer on error
                
    async def process_pending_tasks(self) -> List[Dict[str, Any]]:
        """Process all pending tasks in the queue.
        
        Returns:
            List of processed tasks
        """
        try:
            # Get pending tasks from database
            tasks = self.db.get_pending_tasks(limit=10)
            
            if not tasks:
                return []
                
            logger.info(f"Processing {len(tasks)} pending tasks")
            
            processed = []
            for task in tasks:
                try:
                    result = await self._process_task(task)
                    processed.append(result)
                except Exception as e:
                    logger.error(f"Error processing task {task['task_id']}: {e}")
                    # Update task with error
                    self.db.update_task_status(
                        task['task_id'],
                        'failed',
                        {'error': str(e)}
                    )
                    
            return processed
            
        except Exception as e:
            logger.error(f"Error in process_pending_tasks: {e}")
            return []
            
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single task.
        
        Args:
            task: Task dictionary
            
        Returns:
            Processing result
        """
        task_id = task['task_id']
        agent_id = task.get('agent_id')
        
        logger.info(f"Processing task {task_id} for agent {agent_id}")
        
        # Update task status to processing
        self.db.update_task_status(task_id, 'processing')
        
        # Update agent activity
        if agent_id:
            self.db.client.from_('agents').update({
                'last_activity': datetime.now().isoformat(),
                'status': 'running'
            }).eq('agent_id', agent_id).execute()
            
        # Simulate task processing (in real implementation, agent would execute)
        await asyncio.sleep(1)
        
        # Mark as completed
        self.db.update_task_status(task_id, 'completed')
        
        return {
            'task_id': task_id,
            'status': 'completed',
            'timestamp': datetime.now().isoformat()
        }
        
    async def add_task(self, task_data: Dict[str, Any], agent_id: Optional[str] = None) -> str:
        """Add a new task to the queue.
        
        Args:
            task_data: Task data dictionary
            agent_id: Optional agent ID to assign task to
            
        Returns:
            Task ID
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        self.db.create_task(
            task_id=task_id,
            agent_id=agent_id,
            task_data=task_data
        )
        
        logger.info(f"Task {task_id} added to queue")
        return task_id
        
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about the task queue.
        
        Returns:
            Dictionary with queue statistics
        """
        pending = self.db.get_pending_tasks()
        
        return {
            'pending_count': len(pending),
            'running': self.running,
            'timestamp': datetime.now().isoformat()
        }
