"""Self-Improvement Engine - AI-powered самооптимизация системы.

Обеспечивает:
- Анализ производительности агентов
- Автоматическое выявление узких мест
- Генерация рекомендаций по оптимизации
- Применение улучшений в runtime
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class PerformanceSnapshot:
    """Снимок производительности системы."""
    
    def __init__(self, metrics: Dict[str, Any]):
        self.timestamp = datetime.now()
        self.metrics = metrics
        self.agent_timings = metrics.get('agent_timings', {})
        self.cache_hit_rate = metrics.get('cache_hit_rate', 0)
        self.memory_usage_mb = metrics.get('memory_usage_mb', 0)
        self.task_throughput = metrics.get('tasks_per_second', 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'metrics': self.metrics,
            'agent_timings': self.agent_timings,
            'cache_hit_rate': self.cache_hit_rate,
            'memory_usage_mb': self.memory_usage_mb,
            'task_throughput': self.task_throughput
        }


class OptimizationSuggestion:
    """Рекомендация по оптимизации."""
    
    def __init__(self, category: str, severity: str, description: str, 
                 action: str, expected_impact: str):
        self.category = category  # cache, async, memory, etc.
        self.severity = severity  # low, medium, high, critical
        self.description = description
        self.action = action
        self.expected_impact = expected_impact
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь."""
        return {
            'category': self.category,
            'severity': self.severity,
            'description': self.description,
            'action': self.action,
            'expected_impact': self.expected_impact,
            'created_at': self.created_at.isoformat()
        }


class SelfImprovementEngine:
    """AI-powered движок самооптимизации."""
    
    def __init__(self, core_instance=None):
        """
        Инициализация движка.
        
        Args:
            core_instance: Ссылка на LegionCore для доступа к метрикам
        """
        self.core = core_instance
        self.snapshots: List[PerformanceSnapshot] = []
        self.suggestions: List[OptimizationSuggestion] = []
        self.applied_optimizations: List[str] = []
        self.max_snapshots = 1000  # Хранить последние 1000 снимков
        
        logger.info("SelfImprovementEngine initialized")
    
    async def take_snapshot(self) -> PerformanceSnapshot:
        """
        Сделать снимок текущей производительности.
        
        Returns:
            PerformanceSnapshot: Снимок метрик
        """
        if not self.core:
            raise RuntimeError("Core instance not set")
        
        metrics = self.core.get_metrics()
        snapshot = PerformanceSnapshot(metrics)
        
        self.snapshots.append(snapshot)
        
        # Ограничить размер истории
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots:]
        
        logger.debug(f"Performance snapshot taken: {snapshot.task_throughput:.2f} tasks/s")
        return snapshot
    
    def analyze_performance(self) -> List[OptimizationSuggestion]:
        """
        Анализ производительности и генерация рекомендаций.
        
        Returns:
            List[OptimizationSuggestion]: Список рекомендаций
        """
        if len(self.snapshots) < 10:
            logger.info("Not enough data for analysis (need 10+ snapshots)")
            return []
        
        suggestions = []
        
        # Анализ 1: Cache hit rate
        recent_snapshots = self.snapshots[-100:]
        avg_hit_rate = statistics.mean([s.cache_hit_rate for s in recent_snapshots])
        
        if avg_hit_rate < 80:
            suggestions.append(OptimizationSuggestion(
                category='cache',
                severity='high',
                description=f'Low cache hit rate: {avg_hit_rate:.1f}% (target: >95%)',
                action='Increase hot_cache_size from 128 to 256',
                expected_impact='Cache hit rate: +10-15%, latency: -20%'
            ))
        
        # Анализ 2: Agent timing outliers
        agent_timings = defaultdict(list)
        for snapshot in recent_snapshots:
            for agent_id, timing in snapshot.agent_timings.items():
                agent_timings[agent_id].append(timing)
        
        for agent_id, timings in agent_timings.items():
            if len(timings) < 5:
                continue
            
            median_time = statistics.median(timings)
            p95_time = statistics.quantiles(timings, n=20)[18]  # 95th percentile
            
            if p95_time > median_time * 3:
                suggestions.append(OptimizationSuggestion(
                    category='async',
                    severity='medium',
                    description=f'Agent {agent_id} has high latency variance (p95: {p95_time:.1f}ms, median: {median_time:.1f}ms)',
                    action=f'Convert {agent_id} to fully async execution',
                    expected_impact='P95 latency: -40-60%'
                ))
        
        # Анализ 3: Memory usage trend
        memory_trend = [s.memory_usage_mb for s in recent_snapshots[-20:]]
        if len(memory_trend) >= 10:
            # Проверка роста памяти
            first_half_avg = statistics.mean(memory_trend[:10])
            second_half_avg = statistics.mean(memory_trend[10:])
            
            growth_rate = (second_half_avg - first_half_avg) / first_half_avg * 100
            
            if growth_rate > 20:
                suggestions.append(OptimizationSuggestion(
                    category='memory',
                    severity='critical',
                    description=f'Memory leak detected: {growth_rate:.1f}% growth in 20 snapshots',
                    action='Enable garbage collection profiling, check for circular references',
                    expected_impact='Memory usage: -30-50%'
                ))
        
        # Анализ 4: Task throughput degradation
        throughputs = [s.task_throughput for s in recent_snapshots[-50:]]
        if len(throughputs) >= 20:
            first_quarter = statistics.mean(throughputs[:10])
            last_quarter = statistics.mean(throughputs[-10:])
            
            degradation = (first_quarter - last_quarter) / first_quarter * 100
            
            if degradation > 15:
                suggestions.append(OptimizationSuggestion(
                    category='throughput',
                    severity='high',
                    description=f'Throughput degradation: -{degradation:.1f}% over last 50 snapshots',
                    action='Increase worker pool size or optimize task queue',
                    expected_impact='Throughput: +20-30%'
                ))
        
        self.suggestions.extend(suggestions)
        
        if suggestions:
            logger.info(f"Generated {len(suggestions)} optimization suggestions")
            for s in suggestions:
                logger.info(f"  [{s.severity.upper()}] {s.category}: {s.description}")
        
        return suggestions
    
    async def apply_optimization(self, suggestion: OptimizationSuggestion) -> bool:
        """
        Применить оптимизацию.
        
        Args:
            suggestion: Рекомендация для применения
        
        Returns:
            bool: True если применено успешно
        """
        if not self.core:
            logger.error("Core instance not available")
            return False
        
        try:
            # Применить оптимизацию в зависимости от категории
            if suggestion.category == 'cache':
                if 'Increase hot_cache_size' in suggestion.action:
                    old_size = self.core.cache.hot_cache_size
                    new_size = 256
                    self.core.cache.hot_cache_size = new_size
                    logger.info(f"✅ Applied: hot_cache_size {old_size} → {new_size}")
                    
            elif suggestion.category == 'throughput':
                if 'worker pool size' in suggestion.action:
                    # Добавить воркеров динамически
                    for _ in range(2):
                        task = asyncio.create_task(self.core._worker())
                        self.core._worker_tasks.add(task)
                    logger.info(f"✅ Applied: Added 2 workers")
            
            self.applied_optimizations.append(f"{suggestion.category}:{suggestion.action}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply optimization: {e}")
            return False
    
    async def auto_optimize(self, interval_seconds: int = 300):
        """
        Автоматическая оптимизация в фоновом режиме.
        
        Args:
            interval_seconds: Интервал между циклами оптимизации
        """
        logger.info(f"Started auto-optimization (interval: {interval_seconds}s)")
        
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                
                # Снять снимок
                await self.take_snapshot()
                
                # Проанализировать
                suggestions = self.analyze_performance()
                
                # Применить критичные и высокоприоритетные
                for suggestion in suggestions:
                    if suggestion.severity in ['critical', 'high']:
                        logger.info(f"Auto-applying: {suggestion.description}")
                        await self.apply_optimization(suggestion)
                
            except asyncio.CancelledError:
                logger.info("Auto-optimization stopped")
                break
            except Exception as e:
                logger.error(f"Auto-optimization error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
    
    def get_improvement_report(self) -> Dict[str, Any]:
        """
        Получить отчет о самооптимизации.
        
        Returns:
            Dict: Отчет с метриками улучшений
        """
        if len(self.snapshots) < 2:
            return {'status': 'insufficient_data'}
        
        first_snapshot = self.snapshots[0]
        last_snapshot = self.snapshots[-1]
        
        # Вычислить улучшения
        throughput_improvement = (
            (last_snapshot.task_throughput - first_snapshot.task_throughput) 
            / first_snapshot.task_throughput * 100
        ) if first_snapshot.task_throughput > 0 else 0
        
        cache_improvement = last_snapshot.cache_hit_rate - first_snapshot.cache_hit_rate
        
        return {
            'status': 'active',
            'total_snapshots': len(self.snapshots),
            'total_suggestions': len(self.suggestions),
            'applied_optimizations': len(self.applied_optimizations),
            'improvements': {
                'throughput_change_percent': throughput_improvement,
                'cache_hit_rate_change': cache_improvement,
                'memory_change_mb': last_snapshot.memory_usage_mb - first_snapshot.memory_usage_mb
            },
            'recent_optimizations': self.applied_optimizations[-10:]
        }
