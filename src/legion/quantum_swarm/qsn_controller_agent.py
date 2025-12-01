"""QSNControllerAgent — Orchestrator Integration Layer v4.5.0

Интеграция Quantum-Swarm с Ultra-Orchestrator 4.1.0:
- Регистрация в MultiAgentOrchestrator
- Обработка задач через QSN mesh
- Автоматическое масштабирование при нагрузке
- Error recovery и self-healing
- Prometheus telemetry hooks

Architecture:
    Наследует BaseAgent из Legion
    Управляет пулом QSNNode через FabricEngine
    Интегрируется с orchestration workflows
"""

import asyncio
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone

try:
    from prometheus_client import Counter, Histogram, Gauge
except ImportError:
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self


logger = logging.getLogger(__name__)


class QSNControllerAgent:
    """Controller Agent для интеграции QSN с Legion Orchestrator.
    
    Attributes:
        agent_id: Уникальный идентификатор агента
        fabric_engine: Ссылка на FabricEngine для управления узлами
        state: Текущее состояние контроллера
        
    Prometheus Metrics:
        qsn_controller_tasks: Счётчик обработанных задач
        qsn_controller_errors: Счётчик ошибок
        qsn_controller_latency: Латентность обработки
    """
    
    # Prometheus metrics
    _tasks_counter = Counter(
        "qsn_controller_tasks_total",
        "Total tasks processed by controller",
        ["agent_id", "status"]
    )
    _errors_counter = Counter(
        "qsn_controller_errors_total",
        "Total controller errors",
        ["agent_id", "error_type"]
    )
    _latency_histogram = Histogram(
        "qsn_controller_latency_seconds",
        "Task processing latency",
        ["agent_id"]
    )
    _active_nodes_gauge = Gauge(
        "qsn_controller_active_nodes",
        "Number of active QSN nodes",
        ["agent_id"]
    )
    
    def __init__(
        self,
        agent_id: str = "qsn_controller",
        max_nodes: int = 10,
        auto_scale: bool = True,
    ):
        """Инициализация QSNControllerAgent.
        
        Args:
            agent_id: ID агента в orchestrator
            max_nodes: Максимальное количество QSN узлов
            auto_scale: Включить автомасштабирование
        """
        self.agent_id = agent_id
        self.max_nodes = max_nodes
        self.auto_scale = auto_scale
        
        self.state = "initialized"
        self._nodes: List[Any] = []  # List[QSNNode]
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        
        self._created_at = datetime.now(timezone.utc)
        self._tasks_processed = 0
        self._tasks_failed = 0
        
        logger.info(f"QSNControllerAgent {agent_id} initialized")
    
    async def start(self) -> None:
        """Запуск контроллера и рабочих процессов."""
        logger.info(f"Starting QSNControllerAgent {self.agent_id}")
        
        self.state = "running"
        
        # Создание начального узла
        from .qsn_node import QSNNode
        initial_node = QSNNode(max_queue_size=100)
        await initial_node.start()
        self._nodes.append(initial_node)
        
        # Запуск рабочих циклов
        self._worker_task = asyncio.create_task(self._worker_loop())
        self._metrics_task = asyncio.create_task(self._metrics_loop())
        
        logger.info(f"QSNControllerAgent {self.agent_id} started with 1 node")
    
    async def stop(self) -> None:
        """Остановка контроллера и всех узлов."""
        logger.info(f"Stopping QSNControllerAgent {self.agent_id}")
        
        self.state = "stopping"
        
        # Остановка рабочих циклов
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        if self._metrics_task:
            self._metrics_task.cancel()
            try:
                await self._metrics_task
            except asyncio.CancelledError:
                pass
        
        # Остановка всех узлов
        for node in self._nodes:
            await node.stop()
        
        self.state = "stopped"
        logger.info(f"QSNControllerAgent {self.agent_id} stopped")
    
    async def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение задачи через QSN mesh (интерфейс для orchestrator).
        
        Args:
            task_data: Данные задачи от orchestrator
            
        Returns:
            Результат выполнения задачи
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Добавление задачи в очередь
            result_future = asyncio.Future()
            await self._task_queue.put({
                "data": task_data,
                "future": result_future,
            })
            
            # Ожидание результата
            result = await asyncio.wait_for(result_future, timeout=30.0)
            
            self._tasks_processed += 1
            self._tasks_counter.labels(
                agent_id=self.agent_id,
                status="success"
            ).inc()
            
            latency = asyncio.get_event_loop().time() - start_time
            self._latency_histogram.labels(agent_id=self.agent_id).observe(latency)
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Task execution timeout: {task_data}")
            self._tasks_failed += 1
            self._tasks_counter.labels(
                agent_id=self.agent_id,
                status="timeout"
            ).inc()
            self._errors_counter.labels(
                agent_id=self.agent_id,
                error_type="timeout"
            ).inc()
            return {"error": "timeout", "status": "failed"}
            
        except Exception as e:
            logger.exception(f"Task execution error: {e}")
            self._tasks_failed += 1
            self._tasks_counter.labels(
                agent_id=self.agent_id,
                status="error"
            ).inc()
            self._errors_counter.labels(
                agent_id=self.agent_id,
                error_type=type(e).__name__
            ).inc()
            return {"error": str(e), "status": "failed"}
    
    async def _worker_loop(self) -> None:
        """Основной рабочий цикл обработки задач."""
        while self.state == "running":
            try:
                # Получение задачи из очереди
                task_item = await asyncio.wait_for(
                    self._task_queue.get(),
                    timeout=1.0
                )
                
                task_data = task_item["data"]
                result_future = task_item["future"]
                
                # Выбор узла с минимальной нагрузкой
                target_node = await self._select_node()
                
                if not target_node:
                    logger.error("No available nodes for task execution")
                    result_future.set_result({"error": "no_nodes", "status": "failed"})
                    continue
                
                # Выполнение задачи на узле
                result = await target_node.execute_task(task_data)
                result_future.set_result(result)
                
                # Проверка необходимости масштабирования
                if self.auto_scale:
                    await self._check_scaling()
                
            except asyncio.TimeoutError:
                # Нет задач — обновить метрики
                self._update_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Worker loop error: {e}")
                await asyncio.sleep(1.0)
    
    async def _select_node(self) -> Optional[Any]:
        """Выбор узла с минимальной нагрузкой.
        
        Returns:
            QSNNode с минимальной очередью или None
        """
        if not self._nodes:
            return None
        
        # Фильтрация здоровых узлов
        healthy_nodes = [
            node for node in self._nodes
            if node.state.value == "healthy"
        ]
        
        if not healthy_nodes:
            logger.warning("No healthy nodes available")
            return None
        
        # Выбор узла с минимальной очередью
        return min(
            healthy_nodes,
            key=lambda n: n.metrics.task_queue_size
        )
    
    async def _check_scaling(self) -> None:
        """Проверка необходимости автомасштабирования."""
        if len(self._nodes) >= self.max_nodes:
            return
        
        # Вычисление средней загрузки
        total_queue = sum(
            node.metrics.task_queue_size
            for node in self._nodes
        )
        avg_queue = total_queue / len(self._nodes) if self._nodes else 0
        
        # Масштабирование при высокой загрузке
        if avg_queue > 50:  # Порог для scaling up
            await self._scale_up()
        elif avg_queue < 10 and len(self._nodes) > 1:  # Порог для scaling down
            await self._scale_down()
    
    async def _scale_up(self) -> None:
        """Добавление нового узла в пул."""
        if len(self._nodes) >= self.max_nodes:
            logger.warning(f"Max nodes limit reached: {self.max_nodes}")
            return
        
        logger.info(f"Scaling up: adding new QSN node")
        
        from .qsn_node import QSNNode
        new_node = QSNNode(max_queue_size=100)
        await new_node.start()
        self._nodes.append(new_node)
        
        logger.info(f"Scaled up to {len(self._nodes)} nodes")
        self._update_metrics()
    
    async def _scale_down(self) -> None:
        """Удаление узла из пула при низкой загрузке."""
        if len(self._nodes) <= 1:
            return
        
        logger.info(f"Scaling down: removing idle node")
        
        # Удаление узла с минимальной очередью
        idle_node = min(
            self._nodes,
            key=lambda n: n.metrics.task_queue_size
        )
        
        await idle_node.stop()
        self._nodes.remove(idle_node)
        
        logger.info(f"Scaled down to {len(self._nodes)} nodes")
        self._update_metrics()
    
    async def _metrics_loop(self) -> None:
        """Периодическое обновление метрик."""
        while self.state == "running":
            try:
                await asyncio.sleep(5.0)
                self._update_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Metrics loop error: {e}")
    
    def _update_metrics(self) -> None:
        """Обновление Prometheus метрик."""
        self._active_nodes_gauge.labels(agent_id=self.agent_id).set(
            len(self._nodes)
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Получение текущего статуса контроллера.
        
        Returns:
            Словарь со статусом и метриками
        """
        return {
            "agent_id": self.agent_id,
            "state": self.state,
            "nodes_count": len(self._nodes),
            "tasks_processed": self._tasks_processed,
            "tasks_failed": self._tasks_failed,
            "queue_size": self._task_queue.qsize(),
            "nodes_status": [
                node.get_status()
                for node in self._nodes
            ],
            "uptime_seconds": (
                datetime.now(timezone.utc) - self._created_at
            ).total_seconds(),
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья контроллера (для orchestrator).
        
        Returns:
            Health check result
        """
        healthy_nodes = sum(
            1 for node in self._nodes
            if node.state.value == "healthy"
        )
        
        is_healthy = (
            self.state == "running"
            and len(self._nodes) > 0
            and healthy_nodes > 0
        )
        
        return {
            "healthy": is_healthy,
            "state": self.state,
            "nodes_total": len(self._nodes),
            "nodes_healthy": healthy_nodes,
            "tasks_queued": self._task_queue.qsize(),
        }
