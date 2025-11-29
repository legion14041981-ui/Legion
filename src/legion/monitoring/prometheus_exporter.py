"""Prometheus Exporter - экспорт метрик в Prometheus.

Полный набор метрик:
- Agent registration performance
- Cache hit rates
- Task execution latency
- Memory usage
- Error rates
- Throughput metrics
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, Info, Summary,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from prometheus_client.exposition import generate_latest

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Коллектор метрик Prometheus."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Инициализация коллектора.
        
        Args:
            registry: Prometheus registry (используется дефолтный, если None)
        """
        self.registry = registry or CollectorRegistry()
        
        # Метрики регистрации агентов
        self.agent_registrations = Counter(
            'legion_agent_registrations_total',
            'Общее количество регистраций агентов',
            ['agent_type'],
            registry=self.registry
        )
        
        self.agent_registration_duration = Histogram(
            'legion_agent_registration_duration_seconds',
            'Время регистрации агента',
            ['agent_type'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )
        
        # Метрики кэширования
        self.cache_hits = Counter(
            'legion_cache_hits_total',
            'Количество попаданий в кэш',
            ['cache_tier'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'legion_cache_misses_total',
            'Количество промахов кэша',
            registry=self.registry
        )
        
        self.cache_hit_rate = Gauge(
            'legion_cache_hit_rate_percent',
            'Cache hit rate в процентах',
            registry=self.registry
        )
        
        self.cache_size = Gauge(
            'legion_cache_size_bytes',
            'Размер кэша в байтах',
            ['cache_tier'],
            registry=self.registry
        )
        
        # Метрики выполнения задач
        self.tasks_total = Counter(
            'legion_tasks_total',
            'Общее количество задач',
            ['status', 'agent_type'],
            registry=self.registry
        )
        
        self.task_duration = Histogram(
            'legion_task_duration_seconds',
            'Время выполнения задачи',
            ['agent_type'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )
        
        self.task_queue_size = Gauge(
            'legion_task_queue_size',
            'Размер очереди задач',
            registry=self.registry
        )
        
        # Метрики ресурсов
        self.memory_usage = Gauge(
            'legion_memory_usage_bytes',
            'Использование памяти',
            ['component'],
            registry=self.registry
        )
        
        self.cpu_usage = Gauge(
            'legion_cpu_usage_percent',
            'Использование CPU',
            ['component'],
            registry=self.registry
        )
        
        self.active_agents = Gauge(
            'legion_active_agents',
            'Количество активных агентов',
            ['agent_type'],
            registry=self.registry
        )
        
        # Метрики ошибок
        self.errors_total = Counter(
            'legion_errors_total',
            'Общее количество ошибок',
            ['error_type', 'agent_type'],
            registry=self.registry
        )
        
        self.recoveries_attempted = Counter(
            'legion_recoveries_attempted_total',
            'Количество попыток восстановления',
            ['recovery_type'],
            registry=self.registry
        )
        
        self.recoveries_successful = Counter(
            'legion_recoveries_successful_total',
            'Успешные восстановления',
            ['recovery_type'],
            registry=self.registry
        )
        
        # Метрики браузерной автоматизации
        self.browser_actions = Counter(
            'legion_browser_actions_total',
            'Количество браузерных действий',
            ['action_type', 'status'],
            registry=self.registry
        )
        
        self.browser_sessions = Gauge(
            'legion_browser_sessions_active',
            'Активные браузерные сессии',
            ['browser_type'],
            registry=self.registry
        )
        
        self.page_load_duration = Histogram(
            'legion_page_load_duration_seconds',
            'Время загрузки страницы',
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
            registry=self.registry
        )
        
        # Метрики оркестрации
        self.orchestration_workflows = Counter(
            'legion_orchestration_workflows_total',
            'Количество запусков workflow',
            ['pattern_type', 'status'],
            registry=self.registry
        )
        
        self.agent_handoffs = Counter(
            'legion_agent_handoffs_total',
            'Количество передач между агентами',
            ['from_agent', 'to_agent'],
            registry=self.registry
        )
        
        # System info
        self.system_info = Info(
            'legion_system',
            'Информация о системе',
            registry=self.registry
        )
        
        self.system_info.info({
            'version': '2.2.0',
            'mode': 'production'
        })
        
        # Метрики самооптимизации
        self.optimization_suggestions = Counter(
            'legion_optimization_suggestions_total',
            'Количество рекомендаций по оптимизации',
            ['category', 'severity'],
            registry=self.registry
        )
        
        self.optimizations_applied = Counter(
            'legion_optimizations_applied_total',
            'Примененные оптимизации',
            ['category'],
            registry=self.registry
        )
        
        logger.info("MetricsCollector initialized")
    
    # Methods for recording metrics
    
    def record_agent_registration(self, agent_type: str, duration: float):
        """Зарегистрировать регистрацию агента."""
        self.agent_registrations.labels(agent_type=agent_type).inc()
        self.agent_registration_duration.labels(agent_type=agent_type).observe(duration)
    
    def record_cache_hit(self, tier: str = 'hot'):
        """Зарегистрировать попадание в кэш."""
        self.cache_hits.labels(cache_tier=tier).inc()
    
    def record_cache_miss(self):
        """Зарегистрировать промах кэша."""
        self.cache_misses.inc()
    
    def update_cache_hit_rate(self, rate: float):
        """Обновить cache hit rate."""
        self.cache_hit_rate.set(rate)
    
    def record_task(self, agent_type: str, status: str, duration: float):
        """Зарегистрировать выполнение задачи."""
        self.tasks_total.labels(status=status, agent_type=agent_type).inc()
        self.task_duration.labels(agent_type=agent_type).observe(duration)
    
    def record_browser_action(self, action_type: str, status: str):
        """Зарегистрировать браузерное действие."""
        self.browser_actions.labels(action_type=action_type, status=status).inc()
    
    def record_error(self, error_type: str, agent_type: str):
        """Зарегистрировать ошибку."""
        self.errors_total.labels(error_type=error_type, agent_type=agent_type).inc()
    
    def record_optimization(self, category: str, severity: str, applied: bool = False):
        """Зарегистрировать оптимизацию."""
        self.optimization_suggestions.labels(category=category, severity=severity).inc()
        if applied:
            self.optimizations_applied.labels(category=category).inc()


class PrometheusExporter:
    """Экспортер метрик в Prometheus."""
    
    def __init__(self, core_instance=None, port: int = 9090):
        """
        Инициализация экспортера.
        
        Args:
            core_instance: Ссылка на LegionCore
            port: Порт для HTTP сервера метрик
        """
        self.core = core_instance
        self.port = port
        self.collector = MetricsCollector()
        self._server_task: Optional[Any] = None
        
        logger.info(f"PrometheusExporter initialized on port {port}")
    
    async def start_server(self):
        """Запустить HTTP сервер для экспорта метрик."""
        try:
            from aiohttp import web
            
            async def metrics_handler(request):
                """Обработчик /metrics endpoint."""
                metrics_output = generate_latest(self.collector.registry)
                return web.Response(body=metrics_output, content_type=CONTENT_TYPE_LATEST)
            
            app = web.Application()
            app.router.add_get('/metrics', metrics_handler)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', self.port)
            await site.start()
            
            logger.info(f"✅ Prometheus metrics server started on http://0.0.0.0:{self.port}/metrics")
            
            # Keep running
            while True:
                await asyncio.sleep(3600)
                
        except ImportError:
            logger.error("❌ aiohttp not installed. Install with: pip install aiohttp")
        except Exception as e:
            logger.error(f"❌ Failed to start metrics server: {e}")
    
    def update_metrics_from_core(self):
        """Обновить метрики из LegionCore."""
        if not self.core:
            return
        
        try:
            # Получить метрики
            core_metrics = self.core.get_metrics()
            
            # Обновить cache hit rate
            cache_hit_rate_str = core_metrics.get('cache_hit_rate', '0%')
            cache_hit_rate = float(cache_hit_rate_str.rstrip('%'))
            self.collector.update_cache_hit_rate(cache_hit_rate)
            
            # Обновить размер очереди
            if hasattr(self.core, '_task_queue'):
                self.collector.task_queue_size.set(self.core._task_queue.qsize())
            
            # Обновить активных агентов
            agent_counts = {}
            for agent_id, agent in self.core.agents.items():
                agent_type = agent.__class__.__name__
                agent_counts[agent_type] = agent_counts.get(agent_type, 0) + 1
            
            for agent_type, count in agent_counts.items():
                self.collector.active_agents.labels(agent_type=agent_type).set(count)
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    async def start_periodic_update(self, interval: int = 15):
        """
        Запустить периодическое обновление метрик.
        
        Args:
            interval: Интервал в секундах
        """
        logger.info(f"Started periodic metrics update (interval: {interval}s)")
        
        while True:
            try:
                self.update_metrics_from_core()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics update error: {e}")
                await asyncio.sleep(interval)
    
    def get_metrics_text(self) -> bytes:
        """
        Получить метрики в формате Prometheus.
        
        Returns:
            bytes: Метрики в text формате
        """
        return generate_latest(self.collector.registry)
