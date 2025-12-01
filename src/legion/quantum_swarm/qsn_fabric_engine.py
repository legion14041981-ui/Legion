"""FabricEngine — QSN Cluster Lifecycle Management v4.5.0

Управление жизненным циклом кластера QSN:
- Provisioning и deprovisioning узлов
- Self-healing при отказе узлов
- Автоматическое масштабирование
- Интеграция с orchestrator workflows
- Prometheus health monitoring
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

try:
    from prometheus_client import Counter, Gauge
except ImportError:
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self

from .qsn_node import QSNNode
from .qsn_mesh_router import MeshRouter

logger = logging.getLogger(__name__)


class FabricEngine:
    """Управление кластером Quantum-Swarm Nodes.
    
    Attributes:
        max_nodes: Максимальное количество узлов
        nodes: Список активных QSNNode
        mesh_router: Сетевой маршрутизатор
        
    Prometheus Metrics:
        qsn_fabric_nodes: Количество узлов в кластере
        qsn_fabric_spawn_events: События создания узлов
        qsn_fabric_healing_events: События self-healing
    """
    
    _nodes_gauge = Gauge("qsn_fabric_nodes_total", "Total nodes in fabric", ["fabric_id"])
    _spawn_counter = Counter("qsn_fabric_spawn_events", "Node spawn events", ["fabric_id"])
    _healing_counter = Counter("qsn_fabric_healing_events", "Self-healing events", ["fabric_id"])
    
    def __init__(self, fabric_id: str = "default", max_nodes: int = 10):
        self.fabric_id = fabric_id
        self.max_nodes = max_nodes
        self.nodes: List[QSNNode] = []
        self.mesh_router = MeshRouter(node_id=f"{fabric_id}_router")
        self._healing_task: Optional[asyncio.Task] = None
        logger.info(f"FabricEngine {fabric_id} initialized (max_nodes={max_nodes})")
    
    async def start(self) -> None:
        """Start fabric engine."""
        logger.info(f"Starting FabricEngine {self.fabric_id}")
        await self.mesh_router.start()
        self._healing_task = asyncio.create_task(self._healing_loop())
        logger.info(f"FabricEngine {self.fabric_id} started")
    
    async def stop(self) -> None:
        """Stop fabric engine."""
        logger.info(f"Stopping FabricEngine {self.fabric_id}")
        if self._healing_task:
            self._healing_task.cancel()
            try:
                await self._healing_task
            except asyncio.CancelledError:
                pass
        await self.mesh_router.stop()
        for node in self.nodes:
            await node.stop()
        logger.info(f"FabricEngine {self.fabric_id} stopped")
    
    async def spawn_node(self, parent_id: Optional[str] = None) -> QSNNode:
        """Spawn new QSN node."""
        if len(self.nodes) >= self.max_nodes:
            raise RuntimeError(f"Max nodes limit ({self.max_nodes}) reached")
        
        node = QSNNode(parent_id=parent_id)
        await node.start()
        self.nodes.append(node)
        await self.mesh_router.register_peer(node.node_id)
        
        self._spawn_counter.labels(fabric_id=self.fabric_id).inc()
        self._update_metrics()
        
        logger.info(f"Node {node.node_id} spawned in fabric {self.fabric_id}")
        return node
    
    async def remove_node(self, node_id: str) -> bool:
        """Remove node from fabric."""
        node = next((n for n in self.nodes if n.node_id == node_id), None)
        if not node:
            return False
        
        await node.stop()
        self.nodes.remove(node)
        await self.mesh_router.unregister_peer(node_id)
        self._update_metrics()
        
        logger.info(f"Node {node_id} removed from fabric {self.fabric_id}")
        return True
    
    async def _healing_loop(self) -> None:
        """Self-healing background loop."""
        while True:
            try:
                await asyncio.sleep(10.0)
                dead_nodes = [n for n in self.nodes if n.state.value == "terminated"]
                for node in dead_nodes:
                    logger.warning(f"Healing dead node {node.node_id}")
                    await self.remove_node(node.node_id)
                    self._healing_counter.labels(fabric_id=self.fabric_id).inc()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Healing loop error: {e}")
    
    def _update_metrics(self) -> None:
        self._nodes_gauge.labels(fabric_id=self.fabric_id).set(len(self.nodes))
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "fabric_id": self.fabric_id,
            "nodes_count": len(self.nodes),
            "max_nodes": self.max_nodes,
            "nodes": [n.get_status() for n in self.nodes],
            "mesh_topology": self.mesh_router.get_topology(),
        }
