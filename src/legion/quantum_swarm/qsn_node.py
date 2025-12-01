"""QSNNode — Quantum-Swarm Node v4.5.0

Базовый вычислительный узел с возможностью:
- Автономного размножения при росте нагрузки
- Self-healing и graceful degradation
- Prometheus metrics export
- Async lifecycle management

Node States:
    INITIALIZING -> HEALTHY -> OVERLOADED -> SPAWNING -> HEALTHY
                                          -> DEGRADED -> TERMINATED
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field

try:
    from prometheus_client import Counter, Gauge, Histogram
except ImportError:
    # Fallback для тестирования без prometheus
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass


logger = logging.getLogger(__name__)


class NodeState(str, Enum):
    """Состояния жизненного цикла QSN-узла."""
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    OVERLOADED = "overloaded"
    SPAWNING = "spawning"
    DEGRADED = "degraded"
    TERMINATED = "terminated"


@dataclass
class NodeMetrics:
    """Метрики производительности узла."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    task_queue_size: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    uptime_seconds: float = 0.0
    last_health_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class QSNNode:
    """Quantum-Swarm Node — автономный вычислительный узел.
    
    Attributes:
        node_id: Уникальный идентификатор узла
        state: Текущее состояние узла
        parent_id: ID родительского узла (если есть)
        children: Список дочерних узлов
        metrics: Текущие метрики производительности
        
    Prometheus Metrics:
        qsn_node_state: Gauge текущего состояния
        qsn_tasks_total: Counter выполненных задач
        qsn_spawn_events: Counter событий размножения
        qsn_task_duration: Histogram времени выполнения задач
    """
    
    # Prometheus metrics (class-level)
    _state_gauge = Gauge(
        "qsn_node_state",
        "Current state of QSN node",
        ["node_id", "state"]
    )
    _tasks_counter = Counter(
        "qsn_tasks_total",
        "Total tasks processed",
        ["node_id", "status"]
    )
    _spawn_counter = Counter(
        "qsn_spawn_events",
        "Node spawn events",
        ["parent_id"]
    )
    _task_duration = Histogram(
        "qsn_task_duration_seconds",
        "Task execution duration",
        ["node_id"]
    )
    
    def __init__(
        self,
        node_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        max_queue_size: int = 100,
        spawn_threshold: float = 0.8,
    ):
        """Инициализация QSN узла.
        
        Args:
            node_id: ID узла (генерируется автоматически если не указан)
            parent_id: ID родительского узла
            max_queue_size: Максимальный размер очереди задач
            spawn_threshold: Порог загрузки для создания дочернего узла (0-1)
        """
        self.node_id = node_id or str(uuid.uuid4())
        self.parent_id = parent_id
        self.state = NodeState.INITIALIZING
        self.children: List["QSNNode"] = []
        self.metrics = NodeMetrics()
        
        self.max_queue_size = max_queue_size
        self.spawn_threshold = spawn_threshold
        self._task_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._worker_task: Optional[asyncio.Task] = None
        self._created_at = datetime.now(timezone.utc)
        
        logger.info(f"QSNNode {self.node_id} initialized (parent={parent_id})")
    
    async def start(self) -> None:
        """Запуск узла и его рабочего цикла."""
        if self._worker_task is not None:
            logger.warning(f"Node {self.node_id} already started")
            return
        
        self.state = NodeState.HEALTHY
        self._update_metrics()
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info(f"QSNNode {self.node_id} started")
    
    async def stop(self) -> None:
        """Graceful shutdown узла."""
        logger.info(f"Stopping QSNNode {self.node_id}")
        self.state = NodeState.TERMINATED
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        # Остановить дочерние узлы
        for child in self.children:
            await child.stop()
        
        self._update_metrics()
        logger.info(f"QSNNode {self.node_id} stopped")
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Any:
        """Добавление задачи в очередь выполнения.
        
        Args:
            task_data: Данные задачи для выполнения
            
        Returns:
            Результат выполнения задачи
            
        Raises:
            asyncio.QueueFull: Если очередь переполнена
        """
        await self._task_queue.put(task_data)
        self.metrics.task_queue_size = self._task_queue.qsize()
        
        # Проверка необходимости масштабирования
        if await self._should_spawn():
            await self.spawn_child()
        
        return {"queued": True, "node_id": self.node_id}
    
    async def spawn_child(self) -> "QSNNode":
        """Создание дочернего узла для распределения нагрузки.
        
        Returns:
            Новый дочерний QSNNode
        """
        logger.info(f"Node {self.node_id} spawning child")
        self.state = NodeState.SPAWNING
        self._update_metrics()
        
        child = QSNNode(
            parent_id=self.node_id,
            max_queue_size=self.max_queue_size,
            spawn_threshold=self.spawn_threshold,
        )
        await child.start()
        self.children.append(child)
        
        self._spawn_counter.labels(parent_id=self.node_id).inc()
        self.state = NodeState.HEALTHY
        self._update_metrics()
        
        logger.info(f"Child node {child.node_id} spawned by {self.node_id}")
        return child
    
    async def _should_spawn(self) -> bool:
        """Определение необходимости создания дочернего узла.
        
        Returns:
            True если нужно создать дочерний узел
        """
        queue_load = self._task_queue.qsize() / self.max_queue_size
        return (
            queue_load > self.spawn_threshold
            and self.state == NodeState.HEALTHY
            and len(self.children) < 5  # Ограничение глубины
        )
    
    async def _worker_loop(self) -> None:
        """Основной рабочий цикл обработки задач."""
        while self.state not in (NodeState.TERMINATED, NodeState.DEGRADED):
            try:
                # Получение задачи с таймаутом
                task_data = await asyncio.wait_for(
                    self._task_queue.get(),
                    timeout=1.0
                )
                
                # Выполнение задачи с метрикой времени
                start_time = asyncio.get_event_loop().time()
                try:
                    await self._process_task(task_data)
                    self.metrics.tasks_completed += 1
                    self._tasks_counter.labels(
                        node_id=self.node_id,
                        status="success"
                    ).inc()
                except Exception as e:
                    logger.error(f"Task failed in {self.node_id}: {e}")
                    self.metrics.tasks_failed += 1
                    self._tasks_counter.labels(
                        node_id=self.node_id,
                        status="failure"
                    ).inc()
                finally:
                    duration = asyncio.get_event_loop().time() - start_time
                    self._task_duration.labels(node_id=self.node_id).observe(duration)
                    self.metrics.task_queue_size = self._task_queue.qsize()
                
            except asyncio.TimeoutError:
                # Нет задач — обновить метрики
                await self._health_check()
            except asyncio.CancelledError:
                logger.info(f"Worker loop cancelled for {self.node_id}")
                break
            except Exception as e:
                logger.exception(f"Unexpected error in worker loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_task(self, task_data: Dict[str, Any]) -> Any:
        """Обработка одной задачи (stub для тестирования).
        
        Args:
            task_data: Данные задачи
            
        Returns:
            Результат обработки
        """
        # Placeholder: в production здесь вызов реального обработчика
        await asyncio.sleep(0.1)  # Симуляция работы
        return {"status": "processed", "node_id": self.node_id}
    
    async def _health_check(self) -> None:
        """Проверка здоровья узла и обновление метрик."""
        self.metrics.uptime_seconds = (
            datetime.now(timezone.utc) - self._created_at
        ).total_seconds()
        self.metrics.last_health_check = datetime.now(timezone.utc)
        
        # Обновление состояния на основе метрик
        if self.metrics.tasks_failed > 10 and self.metrics.tasks_completed < 5:
            self.state = NodeState.DEGRADED
            logger.warning(f"Node {self.node_id} degraded")
        
        self._update_metrics()
    
    def _update_metrics(self) -> None:
        """Отправка метрик в Prometheus."""
        self._state_gauge.labels(
            node_id=self.node_id,
            state=self.state.value
        ).set(1)
    
    async def apply_patch(self, patch_data: Dict[str, Any]) -> bool:
        """Применение патча к узлу (для meta-learning).
        
        Args:
            patch_data: Данные патча для применения
            
        Returns:
            True если патч применён успешно
        """
        logger.info(f"Applying patch to node {self.node_id}: {patch_data}")
        # Placeholder для будущей имплементации
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Получение текущего статуса узла.
        
        Returns:
            Словарь со статусом и метриками
        """
        return {
            "node_id": self.node_id,
            "parent_id": self.parent_id,
            "state": self.state.value,
            "children_count": len(self.children),
            "metrics": {
                "queue_size": self.metrics.task_queue_size,
                "completed": self.metrics.tasks_completed,
                "failed": self.metrics.tasks_failed,
                "uptime": self.metrics.uptime_seconds,
            },
        }
