"""Multi-agent orchestrator using LangGraph.

Coordinates planning, execution, and monitoring agents.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, TypedDict, Annotated
import operator

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logging.warning("LangGraph not installed. Install with: pip install langgraph")

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State shared between agents."""
    messages: Annotated[List[Dict[str, Any]], operator.add]
    task: Dict[str, Any]
    results: Dict[str, Any]
    next_agent: str
    error: Optional[str]

class MultiAgentOrchestrator:
    """Orchestrates multiple Legion agents.
    
    Uses LangGraph for workflow management with support for:
    - Sequential execution
    - Parallel execution
    - Dynamic handoffs
    - Error recovery
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize orchestrator.
        
        Args:
            config: Orchestration configuration
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph required: pip install langgraph")
        
        self.config = config or {}
        self.graph = StateGraph(AgentState)
        self.agents = {}
        self._compiled_graph = None
        
        logger.info("Initialized Multi-Agent Orchestrator")
    
    def register_agent(self, name: str, agent: Any, role: str):
        """Register an agent.
        
        Args:
            name: Agent name
            agent: Agent instance
            role: Agent role (planning/execution/monitoring)
        """
        self.agents[name] = {
            'instance': agent,
            'role': role,
            'name': name
        }
        logger.info(f"Registered agent: {name} (role: {role})")
    
    def build_sequential_workflow(self, agent_sequence: List[str]):
        """Build sequential workflow.
        
        Args:
            agent_sequence: List of agent names in execution order
        """
        logger.info(f"Building sequential workflow: {' -> '.join(agent_sequence)}")
        
        for i, agent_name in enumerate(agent_sequence):
            agent_data = self.agents.get(agent_name)
            if not agent_data:
                raise ValueError(f"Agent not found: {agent_name}")
            
            def create_node(agent):
                async def node_func(state: AgentState) -> AgentState:
                    logger.info(f"Executing agent: {agent['name']}")
                    
                    try:
                        result = await agent['instance'].execute(state['task'])
                        
                        return {
                            'messages': state['messages'] + [{
                                'agent': agent['name'],
                                'result': result
                            }],
                            'results': {**state['results'], agent['name']: result},
                            'next_agent': agent_sequence[i+1] if i+1 < len(agent_sequence) else END,
                            'error': None
                        }
                    except Exception as e:
                        logger.error(f"Agent {agent['name']} failed: {e}")
                        return {
                            'messages': state['messages'],
                            'results': state['results'],
                            'next_agent': 'monitoring',  # Route to monitoring for recovery
                            'error': str(e)
                        }
                
                return node_func
            
            self.graph.add_node(agent_name, create_node(agent_data))
            
            if i == 0:
                self.graph.set_entry_point(agent_name)
            
            if i > 0:
                self.graph.add_edge(agent_sequence[i-1], agent_name)
        
        # Final edge to END
        self.graph.add_edge(agent_sequence[-1], END)
    
    def build_hierarchical_workflow(self, supervisor: str, workers: List[str]):
        """Build hierarchical workflow with supervisor.
        
        Args:
            supervisor: Supervisor agent name
            workers: List of worker agent names
        """
        logger.info(f"Building hierarchical workflow: {supervisor} -> [{', '.join(workers)}]")
        
        supervisor_agent = self.agents.get(supervisor)
        if not supervisor_agent:
            raise ValueError(f"Supervisor not found: {supervisor}")
        
        # Supervisor node
        async def supervisor_node(state: AgentState) -> AgentState:
            logger.info("Supervisor planning work...")
            result = await supervisor_agent['instance'].execute(state['task'])
            
            # Supervisor decides which worker to use
            next_worker = result.get('assigned_worker', workers[0])
            
            return {
                'messages': state['messages'] + [{'agent': supervisor, 'decision': next_worker}],
                'task': result.get('modified_task', state['task']),
                'results': state['results'],
                'next_agent': next_worker,
                'error': None
            }
        
        self.graph.add_node(supervisor, supervisor_node)
        self.graph.set_entry_point(supervisor)
        
        # Worker nodes
        for worker_name in workers:
            worker_agent = self.agents.get(worker_name)
            if not worker_agent:
                continue
            
            async def worker_node(state: AgentState, worker=worker_agent) -> AgentState:
                logger.info(f"Worker executing: {worker['name']}")
                result = await worker['instance'].execute(state['task'])
                
                return {
                    'messages': state['messages'] + [{'agent': worker['name'], 'result': result}],
                    'task': state['task'],
                    'results': {**state['results'], worker['name']: result},
                    'next_agent': END,
                    'error': None
                }
            
            self.graph.add_node(worker_name, worker_node)
            self.graph.add_edge(supervisor, worker_name)
            self.graph.add_edge(worker_name, END)
    
    def compile(self):
        """Compile the workflow graph.
        
        Returns:
            Compiled graph ready for execution
        """
           
        logger.info("Compiling orchestration graph...")
        self._compiled_graph = self.graph.compile()
        return self._compiled_graph
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestrated workflow.
        
        Args:
            task: Task to execute
            
        Returns:
            Execution results from all agents
        """
        if not self._compiled_graph:
            self.compile()
        
        logger.info(f"Executing orchestrated workflow for task: {task.get('description', 'N/A')}")
        
        initial_state: AgentState = {
            'messages': [],
            'task': task,
            'results': {},
            'next_agent': '',
            'error': None
        }
        
        try:
            final_state = await self._compiled_graph.ainvoke(initial_state)
            
            return {
                'success': True,
                'results': final_state['results'],
                'messages': final_state['messages'],
                'error': final_state.get('error')                   
}
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': {}
}
