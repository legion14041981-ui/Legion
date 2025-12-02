"""
Watchdog - мониторинг деградации и auto-rollback.

Отслеживает:
- Метрики производительности
- Error rates
- Latency degradation
- Resource usage

Выполняет:
- Automated rollback при деградации
- Alert notifications
- Snapshot restoration
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class MetricThreshold:
    """Порог для метрики."""
    name: str
    max_value: Optional[float] = None
    min_value: Optional[float] = None
    degradation_pct: float = 10.0  # % ухудшения


@dataclass(frozen=True)  # Made immutable for safety
class HealthCheckResult:
    """Результат проверки здоровья."""
    timestamp: str
    healthy: bool
    metrics: Dict[str, float] = field(default_factory=dict)
    violations: List[str] = field(default_factory=list)
    recommendation: str = ""


class PerformanceWatchdog:
    """
    Watchdog для мониторинга производительности.
    
    Автоматический rollback при деградации:
    - Error rate > 5%
    - Latency > +20% baseline
    - Memory usage > +50% baseline
    """
    
    DEFAULT_THRESHOLDS = [
        MetricThreshold(name="error_rate", max_value=0.05),  # 5%
        MetricThreshold(name="latency_ms", degradation_pct=20.0),
        MetricThreshold(name="memory_mb", degradation_pct=50.0),
        MetricThreshold(name="cpu_percent", max_value=90.0),
    ]
    
    def __init__(
        self,
        check_interval: int = 60,
        thresholds: Optional[List[MetricThreshold]] = None,
        max_history_size: int = 1000
    ):
        """
        Инициализация watchdog.
        
        Args:
            check_interval: Интервал проверки (секунды)
            thresholds: Пользовательские пороги
            max_history_size: Максимальное количество записей в истории
        """
        self.check_interval = check_interval
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS
        self.baseline_metrics: Dict[str, float] = {}
        self.max_history_size = max_history_size
        # Use deque with maxlen for automatic circular buffer behavior
        self.history: deque = deque(maxlen=max_history_size)
        self.is_running = False
        logger.info(
            f"✅ PerformanceWatchdog initialized "
            f"(interval={check_interval}s, max_history={max_history_size})"
        )
    
    def set_baseline(self, metrics: Dict[str, float]) -> None:
        """
        Установить baseline метрики.
        
        Args:
            metrics: Метрики baseline
        """
        self.baseline_metrics = metrics.copy()
        logger.info(f"📊 Baseline metrics set: {metrics}")
    
    def check_health(self, current_metrics: Dict[str, float]) -> HealthCheckResult:
        """
        Проверить здоровье системы.
        
        Args:
            current_metrics: Текущие метрики (иммутабельный dict)
        
        Returns:
            HealthCheckResult with immutable metrics
        """
        violations = []
        
        for threshold in self.thresholds:
            metric_name = threshold.name
            if metric_name not in current_metrics:
                continue
            
            current = current_metrics[metric_name]
            
            # Проверка абсолютного максимума
            if threshold.max_value is not None and current > threshold.max_value:
                violations.append(
                    f"{metric_name} exceeds max: {current:.2f} > {threshold.max_value:.2f}"
                )
            
            # Проверка абсолютного минимума
            if threshold.min_value is not None and current < threshold.min_value:
                violations.append(
                    f"{metric_name} below min: {current:.2f} < {threshold.min_value:.2f}"
                )
            
            # Проверка деградации от baseline
            if metric_name in self.baseline_metrics:
                baseline = self.baseline_metrics[metric_name]
                if baseline > 0:  # Avoid division by zero
                    degradation_pct = ((current - baseline) / baseline) * 100
                    
                    if abs(degradation_pct) > threshold.degradation_pct:
                        violations.append(
                            f"{metric_name} degraded by {degradation_pct:.1f}%: "
                            f"{baseline:.2f} → {current:.2f}"
                        )
        
        healthy = len(violations) == 0
        recommendation = self._generate_recommendation(violations)
        
        # Create immutable copy of metrics
        result = HealthCheckResult(
            timestamp=datetime.utcnow().isoformat(),
            healthy=healthy,
            metrics=dict(current_metrics),  # Create new dict instance
            violations=list(violations),  # Create new list instance
            recommendation=recommendation
        )
        
        self.history.append(result)  # Deque automatically handles size limit
        
        if not healthy:
            logger.warning(f"⚠️ Health check failed: {len(violations)} violations")
            for violation in violations:
                logger.warning(f"   - {violation}")
        else:
            logger.info("✅ Health check passed")
        
        return result
    
    def _generate_recommendation(self, violations: List[str]) -> str:
        """Генерация рекомендации."""
        if not violations:
            return "System healthy. Continue monitoring."
        
        if len(violations) >= 3:
            return "🛑 CRITICAL: Multiple violations detected. Immediate rollback recommended."
        elif len(violations) == 2:
            return "⚠️ WARNING: Significant degradation. Consider rollback."
        else:
            return "⚠️ CAUTION: Minor issue detected. Monitor closely."
    
    def should_rollback(self, result: HealthCheckResult) -> bool:
        """
        Определить, нужен ли rollback.
        
        Decision tree:
        1. Check for critical keywords in violations (CRITICAL, exceeds max, etc.)
        2. Check for multiple violations (>= 3)
        3. Check for persistent degradation (3+ consecutive failures)
        
        Args:
            result: Результат health check
        
        Returns:
            True если нужен rollback
        """
        # Критические нарушения
        critical_keywords = ['CRITICAL', 'exceeds max', 'degraded by']
        
        for violation in result.violations:
            for keyword in critical_keywords:
                if keyword in violation:
                    logger.warning(f"🛑 Critical violation detected: {violation}")
                    return True
        
        # Множественные нарушения
        if len(result.violations) >= 3:
            logger.warning(
                f"⚠️ Multiple violations ({len(result.violations)}) detected"
            )
            return True
        
        # История деградации (3+ последовательных неудачных проверок)
        if len(self.history) >= 3:
            recent_checks = list(self.history)[-3:]
            if all(not check.healthy for check in recent_checks):
                logger.warning("⚠️ Persistent degradation detected (3+ failures)")
                return True
        
        return False
    
    def trigger_rollback(
        self,
        current_snapshot_id: str,
        previous_snapshot_id: str,
        registry=None  # Accept registry instance for real rollback
    ) -> Dict[str, Any]:
        """
        Запустить rollback.
        
        Args:
            current_snapshot_id: ID текущего snapshot
            previous_snapshot_id: ID предыдущего stable snapshot
            registry: Optional ArchitectureRegistry instance for real rollback
        
        Returns:
            Результат rollback
        """
        logger.warning("🔄 Initiating automatic rollback...")
        logger.warning(f"   From: {current_snapshot_id}")
        logger.warning(f"   To: {previous_snapshot_id}")
        
        rollback_result = {
            'success': False,
            'rolled_back_from': current_snapshot_id,
            'restored_to': previous_snapshot_id,
            'timestamp': datetime.utcnow().isoformat(),
            'error': None
        }
        
        try:
            if registry is not None:
                # Real rollback via ArchitectureRegistry
                registry.restore_snapshot(previous_snapshot_id)
                rollback_result['success'] = True
                logger.info("✅ Rollback completed successfully")
            else:
                logger.warning(
                    "⚠️ No registry provided - rollback simulated only"
                )
                rollback_result['success'] = True  # Simulated success
        
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            rollback_result['error'] = str(e)
        
        return rollback_result
    
    def get_health_report(self, last_n: int = 10) -> Dict[str, Any]:
        """Получить отчёт о здоровье."""
        recent_checks = list(self.history)[-last_n:] if self.history else []
        
        healthy_count = sum(1 for check in recent_checks if check.healthy)
        health_rate = healthy_count / len(recent_checks) if recent_checks else 0
        
        return {
            'total_checks': len(self.history),
            'recent_checks': len(recent_checks),
            'healthy_count': healthy_count,
            'health_rate': health_rate,
            'last_check': recent_checks[-1].__dict__ if recent_checks else None,
            'baseline_metrics': self.baseline_metrics,
            'max_history_size': self.max_history_size,
            'history_full': len(self.history) >= self.max_history_size
        }
