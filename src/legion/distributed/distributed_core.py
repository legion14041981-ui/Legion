"""Distributed Core - распределенное ядро Legion.

Использует Ray для кластерного выполнения.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional

try:
    import ray
    from ray.util.queue import Queue as RayQueue
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False
    ray = None
    RayQueue = None

logger = logging.getLogger(__name__)


class DistributedCore:
    """Распределенное ядро Legion с Ray backend."""
    
    def __init__(self, redis_address: Optional[str] = None, num_cpus: Optional[int] = None):
        """
        Инициализация distributed core.
        
        Args:
            redis_address: Redis адрес для Ray cluster
            num_cpus: Количество CPU для local cluster
        """
        if not RAY_AVAILABLE:
            raise ImportError("Ray not installed. Install with: pip install ray[default]>=2.9.0")
        
        self.redis_address = redis_address
        self.num_cpus = num_cpus
        self.is_initialized = False
        self.task_queue: Optional[RayQueue] = None
        
        logger.info("DistributedCore initialized")
    
    def init_cluster(self):
        """Инициализировать Ray cluster."""
        if self.is_initialized:
            logger.warning("Cluster already initialized")
            return
        
        if self.redis_address:
            # Подключение к существующему кластеру
            ray.init(address=self.redis_address)
            logger.info(f"Connected to existing Ray cluster: {self.redis_address}")
        else:
            # Создать local cluster
            ray.init(num_cpus=self.num_cpus, ignore_reinit_error=True)
            logger.info(f"Started local Ray cluster (CPUs: {self.num_cpus or 'auto'})")
        
        self.task_queue = RayQueue(maxsize=1000)
        self.is_initialized = True
    
    def shutdown(self):
        """Остановить cluster."""
        if self.is_initialized:
            ray.shutdown()
            self.is_initialized = False
            logger.info("Ray cluster shut down")
    
    async def submit_task(self, task: Dict[str, Any]) -> Any:
        """
        Отправить задачу в кластер.
        
        Args:
            task: Задача для выполнения
        
        Returns:
            Результат выполнения
        """
        if not self.is_initialized:
            self.init_cluster()
        
        # Создать Ray remote function
        @ray.remote
        def execute_task(task_data):
            from legion.distributed.distributed_worker import DistributedWorker
            worker = DistributedWorker()
            return worker.execute(task_data)
        
        # Запустить задачу
        future = execute_task.remote(task)
        result = await asyncio.wrap_future(asyncio.ensure_future(ray.get(future)))
        
        return result
    
    async def submit_tasks_parallel(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """
        Параллельное выполнение задач.
        
        Args:
            tasks: Список задач
        
        Returns:
            Список результатов
        """
        if not self.is_initialized:
            self.init_cluster()
        
        @ray.remote
        def execute_task(task_data):
            from legion.distributed.distributed_worker import DistributedWorker
            worker = DistributedWorker()
            return worker.execute(task_data)
        
        # Запустить все задачи
        futures = [execute_task.remote(task) for task in tasks]
        results = ray.get(futures)
        
        return results
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """
        Получить информацию о кластере.
        
        Returns:
            Dict с информацией о кластере
        """
        if not self.is_initialized:
            return {'status': 'not_initialized'}
        
        return {
            'status': 'active',
            'nodes': len(ray.nodes()),
            'available_resources': ray.available_resources(),
            'cluster_resources': ray.cluster_resources()
        }
