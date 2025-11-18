"""
Legion Core Module - руководящая работа многоагентного система.

Этот модуль отвечает за:
- Координацию эксекуции агентов
- Диспетчеризацию задач
- Логирование и мониторинг
- Оптимизацию производительности через async/await и кэширование
"""

import asyncio
import logging
import weakref
from functools import lru_cache
from typing import List, Dict, Any, Optional, Set
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from collections import defaultdict
import time

from .database import LegionDatabase
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурация логирования
logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Сбор метрик производительности системы."""
    
    def __init__(self):
        self.task_timings: Dict[str, List[float]] = defaultdict(list)
        self.agent_call_counts: Dict[str, int] = defaultdict(int)
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.start_time: float = time.time()
    
    def record_task(self, task_id: str, duration: float):
        """Записать время выполнения задачи."""
        self.task_timings[task_id].append(duration)
    
    def record_agent_call(self, agent_id: str):
        """Записать вызов агента."""
        self.agent_call_counts[agent_id] += 1
    
    def record_cache_hit(self):
        """Записать попадание в кэш."""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Записать промах кэша."""
        self.cache_misses += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Получить сводку метрик."""
        uptime = time.time() - self.start_time
        cache_total = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / cache_total * 100) if cache_total > 0 else 0
        
        return {
            'uptime_seconds': uptime,
            'total_tasks': sum(len(timings) for timings in self.task_timings.values()),
            'agent_calls': dict(self.agent_call_counts),
            'cache_hit_rate': f"{cache_hit_rate:.2f}%",
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses
        }


class AgentCache:
    """Tiered caching для агентов с hot/cold context разделением."""
    
    def __init__(self, hot_cache_size: int = 128, ttl_seconds: int = 3600):
        self.hot_cache: Dict[str, Any] = {}  # In-memory, sub-millisecond
        self.cold_cache: weakref.WeakValueDictionary = weakref.WeakValueDictionary()  # Weak refs
        self.hot_cache_size = hot_cache_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self.access_times: Dict[str, datetime] = {}
        self.access_counts: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()
    
    async def get(self, agent_id: str) -> Optional[Any]:
        """Получить агента из кэша (hot -> cold)."""
        async with self._lock:
            # Check hot cache first (sub-millisecond)
            if agent_id in self.hot_cache:
                self._update_access(agent_id)
                return self.hot_cache[agent_id]
            
            # Check cold cache
            agent = self.cold_cache.get(agent_id)
            if agent:
                # Promote to hot if frequently accessed
                if self.access_counts[agent_id] >= 3:
                    await self._promote_to_hot(agent_id, agent)
                self._update_access(agent_id)
                return agent
            
            return None
    
    async def set(self, agent_id: str, agent: Any):
        """Добавить агента в кэш."""
        async with self._lock:
            self.access_times[agent_id] = datetime.now()
            self.access_counts[agent_id] = 1
            
            # Add to hot cache if space available
            if len(self.hot_cache) < self.hot_cache_size:
                self.hot_cache[agent_id] = agent
            else:
                # Add to cold cache
                self.cold_cache[agent_id] = agent
    
    async def _promote_to_hot(self, agent_id: str, agent: Any):
        """Продвинуть агента в hot cache."""
        if len(self.hot_cache) >= self.hot_cache_size:
            # Evict least recently used
            lru_id = min(self.access_times.items(), key=lambda x: x[1])[0]
            removed_agent = self.hot_cache.pop(lru_id)
            self.cold_cache[lru_id] = removed_agent
        
        self.hot_cache[agent_id] = agent
        if agent_id in self.cold_cache:
            del self.cold_cache[agent_id]
    
    def _update_access(self, agent_id: str):
        """Обновить статистику доступа."""
        self.access_times[agent_id] = datetime.now()
        self.access_counts[agent_id] += 1
    
    async def cleanup_expired(self):
        """Очистить устаревшие записи."""
        async with self._lock:
            now = datetime.now()
            expired = [
                agent_id for agent_id, access_time in self.access_times.items()
                if now - access_time > self.ttl
            ]
            
            for agent_id in expired:
                self.hot_cache.pop(agent_id, None)
                self.cold_cache.pop(agent_id, None)
                self.access_times.pop(agent_id, None)
                self.access_counts.pop(agent_id, None)
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired cache entries")


class LegionCore:
    """
    Основное ядро Legion Framework с оптимизацией производительности.
    
    Отвечает за запуск и управление экосистемой агентов:
    - Асинхронная координация эксекуции
    - Оптимизированная диспетчеризация задач
    - Tiered caching для агентов
    - Connection pooling для БД
    - Сбор метрик производительности
    
    Attributes:
        agents (Dict[str, Any]): Словарь зарегистрированных агентов
        is_running (bool): Флаг статуса работы ядра
        metrics (PerformanceMetrics): Метрики производительности
        cache (AgentCache): Многоуровневый кэш агентов
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация LegionCore с оптимизацией.
        
        Args:
            config (Dict[str, Any], optional): Конфигурация системы.
        """
        self.agents: Dict[str, Any] = {}
        self.is_running: bool = False
        self.config: Dict[str, Any] = config or {}
        
        # Performance optimizations
        self.metrics = PerformanceMetrics()
        self.cache = AgentCache(
            hot_cache_size=self.config.get('hot_cache_size', 128),
            ttl_seconds=self.config.get('cache_ttl', 3600)
        )
        
        # Async task queue for batch processing
        self._task_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._worker_tasks: Set[asyncio.Task] = set()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Database connection pool
        self.db: Optional[LegionDatabase] = None
        self._init_database()
        
        logger.info("LegionCore initialized with performance optimizations")
    
    def _init_database(self):
        """Инициализация подключения к БД с обработкой ошибок."""
        try:
            self.db = LegionDatabase()
            logger.info("Database connection established")
        except Exception as e:
            logger.warning(f"Database not available: {e}")
            self.db = None
    
    async def register_agent(self, agent_id: str, agent: Any) -> None:
        """
        Асинхронная регистрация агента с кэшированием.
        
        Args:
            agent_id (str): Уникальный идентификатор агента
            agent (Any): Объект агента
        """
        # Register in main storage
        self.agents[agent_id] = agent
        
        # Add to cache
        await self.cache.set(agent_id, agent)
        
        logger.info(f"Agent '{agent_id}' registered")
        
        # Async DB sync (non-blocking)
        if self.db:
            asyncio.create_task(self._sync_agent_to_db(agent_id, agent))
    
    async def register_agents_batch(self, agents: Dict[str, Any]) -> None:
        """
        Batch registration для уменьшения overhead.
        
        Args:
            agents (Dict[str, Any]): Словарь {agent_id: agent}
        """
        tasks = [self.register_agent(agent_id, agent) for agent_id, agent in agents.items()]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Batch registered {len(agents)} agents")
    
    async def _sync_agent_to_db(self, agent_id: str, agent: Any):
        """Синхронизация агента с БД (async)."""
        try:
            if hasattr(agent, 'config'):
                config = agent.config
            else:
                config = {}
            
            # Assuming db operations can be made async
            self.db.register_agent(
                agent_id=agent_id,
                name=agent.__class__.__name__,
                config=config
            )
        except Exception as e:
            logger.error(f"Failed to sync agent to database: {e}")
    
    async def dispatch_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """
        Асинхронная диспетчеризация задачи с метриками.
        
        Args:
            task_id (str): Идентификатор задачи
            task_data (Dict[str, Any]): Данные задачи
        
        Returns:
            Any: Результат выполнения задачи
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Dispatching task '{task_id}' with data: {task_data}")
            
            # Get target agent
            agent_id = task_data.get('agent_id')
            if not agent_id:
                raise ValueError("agent_id required in task_data")
            
            agent = await self.get_agent_cached(agent_id)
            if not agent:
                raise ValueError(f"Agent not found: {agent_id}")
            
            self.metrics.record_agent_call(agent_id)
            
            # Execute task (assuming agent has async execute method)
            if hasattr(agent, 'execute_async'):
                result = await agent.execute_async(task_data)
            elif hasattr(agent, 'execute'):
                # Fallback to sync execution in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, agent.execute, task_data)
            else:
                raise AttributeError(f"Agent {agent_id} has no execute method")
            
            duration = time.time() - start_time
            self.metrics.record_task(task_id, duration)
            
            logger.info(f"Task '{task_id}' completed in {duration:.3f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Task '{task_id}' failed after {duration:.3f}s: {e}")
            raise
    
    async def dispatch_tasks_parallel(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """
        Параллельная диспетчеризация задач для максимальной производительности.
        
        Args:
            tasks (List[Dict[str, Any]]): Список задач с полями task_id и task_data
        
        Returns:
            List[Any]: Результаты выполнения задач
        """
        dispatch_tasks = [
            self.dispatch_task(task['task_id'], task['task_data'])
            for task in tasks
        ]
        
        results = await asyncio.gather(*dispatch_tasks, return_exceptions=True)
        logger.info(f"Completed {len(tasks)} parallel tasks")
        return results
    
    async def get_agent_cached(self, agent_id: str) -> Optional[Any]:
        """
        Получить агента с использованием tiered cache.
        
        Args:
            agent_id (str): Идентификатор агента
        
        Returns:
            Optional[Any]: Объект агента или None
        """
        # Try cache first
        agent = await self.cache.get(agent_id)
        if agent:
            self.metrics.record_cache_hit()
            return agent
        
        # Cache miss - get from main storage
        self.metrics.record_cache_miss()
        agent = self.agents.get(agent_id)
        
        if agent:
            # Add to cache for future access
            await self.cache.set(agent_id, agent)
        
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """
        Синхронный метод получения агента (legacy support).
        
        Args:
            agent_id (str): Идентификатор агента
        
        Returns:
            Optional[Any]: Объект агента или None
        """
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, Any]:
        """
        Получить всех зарегистрированных агентов.
        
        Returns:
            Dict[str, Any]: Словарь агентов
        """
        return self.agents.copy()
    
    async def start(self) -> None:
        """
        Асинхронный запуск экосистемы агентов с worker pool.
        """
        if self.is_running:
            logger.warning("LegionCore already running")
            return
        
        self.is_running = True
        
        # Start worker pool for task processing
        num_workers = self.config.get('num_workers', 4)
        for i in range(num_workers):
            task = asyncio.create_task(self._worker())
            self._worker_tasks.add(task)
        
        # Start periodic cache cleanup
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info(f"LegionCore started with {num_workers} workers")
    
    async def _worker(self):
        """Worker для обработки задач из очереди."""
        while self.is_running:
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                await self.dispatch_task(task['task_id'], task['task_data'])
                self._task_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    async def _periodic_cleanup(self):
        """Периодическая очистка кэша."""
        while self.is_running:
            await asyncio.sleep(300)  # Every 5 minutes
            await self.cache.cleanup_expired()
            logger.debug("Cache cleanup completed")
    
    async def stop(self) -> None:
        """
        Graceful shutdown с очисткой ресурсов.
        """
        if not self.is_running:
            return
        
        logger.info("Stopping LegionCore...")
        self.is_running = False
        
        # Wait for queue to drain
        await self._task_queue.join()
        
        # Cancel workers
        for task in self._worker_tasks:
            task.cancel()
        
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("LegionCore stopped gracefully")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Получить метрики производительности.
        
        Returns:
            Dict[str, Any]: Сводка метрик
        """
        return self.metrics.get_summary()
    
    @asynccontextmanager
    async def lifespan(self):
        """Context manager для управления lifecycle."""
        await self.start()
        try:
            yield self
        finally:
            await self.stop()
