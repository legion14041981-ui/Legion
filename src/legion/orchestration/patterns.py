"""Orchestration patterns for multi-agent workflows."""

import asyncio
import logging
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class SequentialPattern:
    """Sequential execution pattern.
    
    Executes agents one after another in order.
    """
    
    @staticmethod
    async def execute(agents: List[Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents sequentially.
        
        Args:
            agents: List of agents to execute
            task: Task to pass to each agent
            
        Returns:
            Aggregated results
        """
        logger.info(f"Sequential execution: {len(agents)} agents")
        
        results = []
        current_task = task
        
        for i, agent in enumerate(agents):
            logger.info(f"Step {i+1}/{len(agents)}: Executing agent")
            
            try:
                result = await agent.execute(current_task)
                results.append(result)
                
                # Pass result to next agent
                current_task = {
                    **current_task,
                    'previous_result': result
                }
                
                if not result.get('success'):
                    logger.warning(f"Agent {i+1} failed, stopping sequence")
                    break
                    
            except Exception as e:
                logger.error(f"Agent {i+1} error: {e}")
                results.append({'success': False, 'error': str(e)})
                break
        
        return {
            'success': all(r.get('success', False) for r in results),
            'results': results,
            'pattern': 'sequential'
        }


class ParallelPattern:
    """Parallel execution pattern.
    
    Executes all agents simultaneously.
    """
    
    @staticmethod
    async def execute(agents: List[Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents in parallel.
        
        Args:
            agents: List of agents to execute
            task: Task to pass to all agents
            
        Returns:
            Aggregated results
        """
        logger.info(f"Parallel execution: {len(agents)} agents")
        
        # Execute all agents concurrently
        tasks = [agent.execute(task) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'agent_index': i
                })
            else:
                processed_results.append(result)
        
        return {
            'success': any(r.get('success', False) for r in processed_results),
            'results': processed_results,
            'pattern': 'parallel'
        }


class HierarchicalPattern:
    """Hierarchical execution pattern.
    
    Supervisor agent coordinates worker agents.
    """
    
    @staticmethod
    async def execute(
        supervisor: Any,
        workers: List[Any],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute hierarchical pattern.
        
        Args:
            supervisor: Supervisor agent
            workers: Worker agents
            task: Initial task
            
        Returns:
            Execution results
        """
        logger.info(f"Hierarchical execution: 1 supervisor, {len(workers)} workers")
        
        # Supervisor creates plan
        supervisor_result = await supervisor.execute(task)
        
        if not supervisor_result.get('success'):
            return {
                'success': False,
                'error': 'Supervisor planning failed',
                'pattern': 'hierarchical'
            }
        
        # Execute assigned worker
        assigned_worker_index = supervisor_result.get('assigned_worker_index', 0)
        worker = workers[assigned_worker_index] if assigned_worker_index < len(workers) else workers[0]
        
        modified_task = supervisor_result.get('modified_task', task)
        worker_result = await worker.execute(modified_task)
        
        return {
            'success': worker_result.get('success', False),
            'supervisor_plan': supervisor_result,
            'worker_result': worker_result,
            'pattern': 'hierarchical'
        }


class HandoffPattern:
    """Handoff execution pattern.
    
    Agents dynamically delegate tasks to each other.
    """
    
    @staticmethod
    async def execute(
        agents: Dict[str, Any],
        initial_task: Dict[str, Any],
        entry_point: str,
        max_handoffs: int = 10
    ) -> Dict[str, Any]:
        """Execute handoff pattern.
        
        Args:
            agents: Dict of agent_name -> agent instance
            initial_task: Starting task
            entry_point: Name of starting agent
            max_handoffs: Maximum number of handoffs
            
        Returns:
            Execution results
        """
        logger.info(f"Handoff execution: {len(agents)} agents, entry: {entry_point}")
        
        current_agent_name = entry_point
        current_task = initial_task
        handoff_chain = [entry_point]
        results = []
        
        for i in range(max_handoffs):
            if current_agent_name not in agents:
                logger.error(f"Agent not found: {current_agent_name}")
                break
            
            agent = agents[current_agent_name]
            logger.info(f"Handoff {i+1}: Executing {current_agent_name}")
            
            try:
                result = await agent.execute(current_task)
                results.append({
                    'agent': current_agent_name,
                    'result': result
                })
                
                # Check if handoff requested
                next_agent = result.get('handoff_to')
                if not next_agent or next_agent == 'END':
                    logger.info("Handoff chain completed")
                    break
                
                current_agent_name = next_agent
                handoff_chain.append(next_agent)
                current_task = result.get('modified_task', current_task)
                
            except Exception as e:
                logger.error(f"Handoff error at {current_agent_name}: {e}")
                results.append({
                    'agent': current_agent_name,
                    'result': {'success': False, 'error': str(e)}
                })
                break
        
        return {
            'success': len(results) > 0 and results[-1]['result'].get('success', False),
            'handoff_chain': handoff_chain,
            'results': results,
            'pattern': 'handoff'
        }
