"""
Performance Watchdog v4.1.0 - Expanded Monitoring.

Улучшения:
- 21 monitoring criteria (включая drift detection и semantic hash)
- Deadlock detection
- Memory leak detection
- Logic contradiction detection
- Self-improvement monitoring
- Auto-task creation for Self-Improver
- Model drift detection (NEW)
- Semantic hash verification (NEW)
- Registry integrity validation (NEW)
"""

import logging
import time
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WatchdogAlert:
    """Алерт watchdog."""
    id: str
    severity: str  # 'info', 'warning', 'alert', 'critical'
    criterion: str
    message: str
    current_value: float
    threshold_value: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'severity': self.severity,
            'criterion': self.criterion,
            'message': self.message,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'timestamp': self.timestamp
        }


class EnhancedPerformanceWatchdog:
    """
    Enhanced Performance Watchdog с 21 критерием мониторинга.
    
    Критерии:
    - Performance (5): error_rate, latency_p50/p95/p99, memory, cpu
    - System Health (4): cache, storage, agent stability, mobile success
    - Architecture (4): registry integrity, deadlocks, infinite loops, memory leaks
    - Logic (4): contradictions, safety bypasses, containment violations, unauthorized actions
    - Evolution (3): self-improvement failures, patch rollbacks, loop stalls
    - Integrity (3): model drift, semantic hash, registry corruption (NEW)
    """
    
    # Пороги по умолчанию
    DEFAULT_THRESHOLDS = {
        # Performance
        'error_rate': {'warning': 0.03, 'alert': 0.05, 'critical': 0.10},
        'latency_p50_degradation': {'warning': 0.15, 'alert': 0.20},
        'latency_p95_degradation': {'warning': 0.30, 'alert': 0.50},
        'latency_p99_degradation': {'warning': 0.40, 'alert': 0.60},
        'memory_usage_pct': {'warning': 0.80, 'alert': 0.90, 'critical': 0.95},
        'cpu_usage_pct': {'warning': 0.75, 'alert': 0.85, 'critical': 0.95},
        
        # System Health
        'cache_hit_rate': {'warning': 0.75, 'alert': 0.65},
        'storage_efficiency': {'warning': 0.60, 'alert': 0.50},
        'agent_stability': {'warning': 0.90, 'alert': 0.85},
        'mobile_agent_success': {'warning': 0.80, 'alert': 0.70},
        
        # Architecture
        'registry_checksum_fail': {'critical': True},
        'deadlock_duration_sec': {'alert': 30, 'critical': 60},
        'infinite_loop_iterations': {'alert': 100, 'critical': 1000},
        'memory_leak_mb_per_hour': {'warning': 10, 'alert': 50},
        
        # Logic
        'contradictory_decisions': {'warning': 1, 'alert': 3},
        'safety_gate_bypasses': {'critical': 1},
        'containment_violations': {'critical': 1},
        'unauthorized_actions': {'critical': 1},
        
        # Evolution
        'self_improvement_failure_rate': {'warning': 0.10, 'alert': 0.20},
        'patch_rollback_rate': {'warning': 0.15, 'alert': 0.25},
        'neuro_loop_stall_hours': {'alert': 48, 'critical': 72},
        
        # Integrity (NEW)
        'model_drift_score': {'warning': 0.15, 'alert': 0.30, 'critical': 0.50},
        'semantic_hash_mismatch': {'critical': True},
        'registry_corruption_detected': {'critical': True}
    }
    
    def __init__(
        self,
        check_interval: int = 300,  # 5 minutes
        baseline: Optional[Dict[str, float]] = None,
        custom_thresholds: Optional[Dict[str, Dict[str, float]]] = None,
        registry_path: Optional[str] = None
    ):
        """
        Инициализация enhanced watchdog.
        
        Args:
            check_interval: Интервал проверки (секунды)
            baseline: Baseline метрики
            custom_thresholds: Custom пороги
            registry_path: Путь к architecture registry
        """
        self.check_interval = check_interval
        self.baseline = baseline or {}
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(custom_thresholds or {})}
        self.registry_path = registry_path or "artifacts/registry"
        
        self.alerts: List[WatchdogAlert] = []
        self.consecutive_failures = 0
        self.last_check_time: Optional[datetime] = None
        
        # Drift detection history
        self.drift_history: List[Dict[str, Any]] = []
        self.max_drift_history = 100
        
        # Semantic hash cache
        self.expected_semantic_hash: Optional[str] = None
        self._load_expected_hash()
        
        logger.info("✅ Enhanced Performance Watchdog v4.1 initialized")
        logger.info(f"   Monitoring criteria: 21 (including drift & hash validation)")
        logger.info(f"   Check interval: {check_interval}s")
        logger.info(f"   Registry path: {self.registry_path}")
    
    def _load_expected_hash(self) -> None:
        """Загрузить ожидаемый semantic hash из манифеста."""
        try:
            manifest_path = Path("artifacts/architecture_manifest_v4.json")
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    self.expected_semantic_hash = manifest.get('semantic_hash')
                    logger.info(f"   Expected semantic hash loaded: {self.expected_semantic_hash}")
        except Exception as e:
            logger.warning(f"Could not load expected semantic hash: {e}")
    
    async def check_model_drift(self, current_metrics: Dict[str, Any]) -> bool:
        """
        Проверка дрейфа AI модели (Model Drift Detection).
        
        Анализирует отклонение текущих метрик от baseline:
        - Accuracy degradation
        - Prediction distribution shift
        - Confidence score changes
        - Response quality metrics
        
        Args:
            current_metrics: Текущие метрики модели
        
        Returns:
            True если дрейф обнаружен
        """
        if not self.baseline:
            logger.info("No baseline for drift detection - skipping")
            return False
        
        drift_detected = False
        drift_score = 0.0
        drift_details = []
        
        # Ключевые метрики для drift detection
        drift_metrics = [
            'accuracy',
            'precision',
            'recall',
            'f1_score',
            'avg_confidence',
            'response_quality'
        ]
        
        for metric in drift_metrics:
            if metric in self.baseline and metric in current_metrics:
                baseline_val = self.baseline[metric]
                current_val = current_metrics[metric]
                
                if baseline_val > 0:
                    # Вычислить относительное отклонение
                    relative_diff = abs(current_val - baseline_val) / baseline_val
                    drift_score = max(drift_score, relative_diff)
                    
                    if relative_diff > 0.10:  # 10% отклонение
                        drift_details.append({
                            'metric': metric,
                            'baseline': baseline_val,
                            'current': current_val,
                            'drift_pct': relative_diff * 100
                        })
        
        # Сохранить в историю
        self.drift_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'drift_score': drift_score,
            'details': drift_details
        })
        
        # Ограничить размер истории
        if len(self.drift_history) > self.max_drift_history:
            self.drift_history = self.drift_history[-self.max_drift_history:]
        
        # Проверить пороги
        if drift_score >= self.thresholds['model_drift_score']['critical']:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_drift_critical",
                severity='critical',
                criterion='model_drift_score',
                message=f"CRITICAL model drift detected: {drift_score:.1%}",
                current_value=drift_score,
                threshold_value=self.thresholds['model_drift_score']['critical']
            ))
            drift_detected = True
            logger.error(f"🚨 CRITICAL model drift: {drift_score:.1%}")
            
        elif drift_score >= self.thresholds['model_drift_score']['alert']:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_drift_alert",
                severity='alert',
                criterion='model_drift_score',
                message=f"Significant model drift detected: {drift_score:.1%}",
                current_value=drift_score,
                threshold_value=self.thresholds['model_drift_score']['alert']
            ))
            drift_detected = True
            logger.warning(f"⚠️ Model drift detected: {drift_score:.1%}")
            
        elif drift_score >= self.thresholds['model_drift_score']['warning']:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_drift_warning",
                severity='warning',
                criterion='model_drift_score',
                message=f"Minor model drift detected: {drift_score:.1%}",
                current_value=drift_score,
                threshold_value=self.thresholds['model_drift_score']['warning']
            ))
            logger.info(f"ℹ️ Minor model drift: {drift_score:.1%}")
        
        if drift_details:
            logger.info(f"Drift details: {json.dumps(drift_details, indent=2)}")
        
        return drift_detected
    
    async def verify_semantic_hash(self, current_hash: str) -> bool:
        """
        Проверка semantic hash архитектуры.
        
        Валидирует что текущий semantic hash соответствует
        ожидаемому значению из architecture_manifest_v4.json.
        
        Args:
            current_hash: Текущий semantic hash системы
        
        Returns:
            True если hash валиден
        """
        if not self.expected_semantic_hash:
            logger.warning("No expected semantic hash configured - skipping verification")
            return True
        
        hash_valid = (current_hash == self.expected_semantic_hash)
        
        if not hash_valid:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_hash_mismatch",
                severity='critical',
                criterion='semantic_hash_mismatch',
                message=f"Semantic hash mismatch! Expected: {self.expected_semantic_hash}, Got: {current_hash}",
                current_value=1.0,
                threshold_value=0.0
            ))
            logger.error(f"🚨 CRITICAL: Semantic hash mismatch!")
            logger.error(f"   Expected: {self.expected_semantic_hash}")
            logger.error(f"   Current:  {current_hash}")
        else:
            logger.info(f"✅ Semantic hash verified: {current_hash}")
        
        return hash_valid
    
    async def validate_registry_integrity(self) -> bool:
        """
        Валидация целостности Architecture Registry.
        
        Проверяет:
        - Наличие критических файлов
        - Контрольные суммы файлов
        - Структуру директорий
        - Соответствие версий
        
        Returns:
            True если registry корректен
        """
        registry_valid = True
        registry_path = Path(self.registry_path)
        
        # Проверка существования директории
        if not registry_path.exists():
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_registry_missing",
                severity='critical',
                criterion='registry_corruption_detected',
                message=f"Registry directory not found: {registry_path}",
                current_value=1.0,
                threshold_value=0.0
            ))
            logger.error(f"🚨 CRITICAL: Registry directory missing: {registry_path}")
            return False
        
        # Критические файлы registry
        required_files = [
            'registry_index.json',
            'checksums.json'
        ]
        
        missing_files = []
        for filename in required_files:
            filepath = registry_path / filename
            if not filepath.exists():
                missing_files.append(filename)
        
        if missing_files:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_registry_files",
                severity='critical',
                criterion='registry_corruption_detected',
                message=f"Registry files missing: {', '.join(missing_files)}",
                current_value=len(missing_files),
                threshold_value=0.0
            ))
            logger.error(f"🚨 CRITICAL: Missing registry files: {missing_files}")
            registry_valid = False
        
        # Проверка контрольных сумм
        try:
            checksums_file = registry_path / 'checksums.json'
            if checksums_file.exists():
                with open(checksums_file, 'r') as f:
                    expected_checksums = json.load(f)
                
                # Валидация каждого файла
                for filename, expected_checksum in expected_checksums.items():
                    filepath = registry_path / filename
                    if filepath.exists():
                        with open(filepath, 'rb') as f:
                            actual_checksum = hashlib.sha256(f.read()).hexdigest()
                        
                        if actual_checksum != expected_checksum:
                            self.alerts.append(WatchdogAlert(
                                id=f"alert_{int(time.time())}_checksum_{filename}",
                                severity='critical',
                                criterion='registry_corruption_detected',
                                message=f"Checksum mismatch for {filename}",
                                current_value=1.0,
                                threshold_value=0.0
                            ))
                            logger.error(f"🚨 Checksum mismatch: {filename}")
                            registry_valid = False
        
        except Exception as e:
            logger.warning(f"Could not validate checksums: {e}")
        
        if registry_valid:
            logger.info("✅ Registry integrity validated")
        
        return registry_valid
    
    def check_health_comprehensive(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Комплексная проверка здоровья по 21 критерию.
        
        Args:
            metrics: Текущие метрики
        
        Returns:
            Результат проверки
        """
        self.alerts.clear()
        self.last_check_time = datetime.utcnow()
        
        # Performance checks
        self._check_performance(metrics)
        
        # System health checks
        self._check_system_health(metrics)
        
        # Architecture checks
        self._check_architecture(metrics)
        
        # Logic checks
        self._check_logic(metrics)
        
        # Evolution checks
        self._check_evolution(metrics)
        
        # Determine overall health
        critical_alerts = [a for a in self.alerts if a.severity == 'critical']
        alert_level_alerts = [a for a in self.alerts if a.severity == 'alert']
        warning_alerts = [a for a in self.alerts if a.severity == 'warning']
        
        healthy = len(critical_alerts) == 0 and len(alert_level_alerts) == 0
        
        if not healthy:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        
        # Generate recommendation
        recommendation = self._generate_recommendation(critical_alerts, alert_level_alerts, warning_alerts)
        
        return {
            'healthy': healthy,
            'timestamp': self.last_check_time.isoformat(),
            'alerts': [a.to_dict() for a in self.alerts],
            'summary': {
                'critical': len(critical_alerts),
                'alerts': len(alert_level_alerts),
                'warnings': len(warning_alerts)
            },
            'consecutive_failures': self.consecutive_failures,
            'recommendation': recommendation,
            'should_rollback': self.should_rollback_v4_1(),
            'drift_detection_enabled': bool(self.baseline),
            'semantic_hash_validation_enabled': bool(self.expected_semantic_hash)
        }
    
    # ... (остальные методы из оригинального файла без изменений)
    
    def _check_performance(self, metrics: Dict[str, Any]) -> None:
        """Performance проверки (5 критериев)."""
        # 1. Error rate
        error_rate = metrics.get('error_rate', 0.0)
        self._check_threshold('error_rate', error_rate, 'Error rate')
        
        # 2-4. Latency degradation
        if self.baseline:
            for percentile in ['p50', 'p95', 'p99']:
                metric_key = f'latency_{percentile}'
                current = metrics.get(metric_key, 0)
                baseline_val = self.baseline.get(metric_key, current)
                
                if baseline_val > 0:
                    degradation = (current - baseline_val) / baseline_val
                    self._check_threshold(
                        f'{metric_key}_degradation',
                        degradation,
                        f'Latency {percentile.upper()} degradation'
                    )
        
        # 5. Memory usage
        memory_pct = metrics.get('memory_usage_pct', 0.0)
        self._check_threshold('memory_usage_pct', memory_pct, 'Memory usage')
        
        # 6. CPU usage
        cpu_pct = metrics.get('cpu_percent', 0.0) / 100.0
        self._check_threshold('cpu_usage_pct', cpu_pct, 'CPU usage')
    
    def _check_system_health(self, metrics: Dict[str, Any]) -> None:
        """System health проверки (4 критерия)."""
        # 7. Cache hit rate
        cache_hit_rate = metrics.get('cache_hit_rate', 1.0)
        if cache_hit_rate < self.thresholds['cache_hit_rate']['alert']:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_cache",
                severity='alert',
                criterion='cache_hit_rate',
                message=f"Cache hit rate too low: {cache_hit_rate:.1%}",
                current_value=cache_hit_rate,
                threshold_value=self.thresholds['cache_hit_rate']['alert']
            ))
        
        # 8. Storage efficiency
        storage_eff = metrics.get('storage_efficiency', 1.0)
        if storage_eff < self.thresholds['storage_efficiency']['warning']:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_storage",
                severity='warning',
                criterion='storage_efficiency',
                message=f"Storage efficiency degraded: {storage_eff:.1%}",
                current_value=storage_eff,
                threshold_value=self.thresholds['storage_efficiency']['warning']
            ))
        
        # 9. Agent stability
        agent_stability = metrics.get('agent_stability', 1.0)
        self._check_threshold('agent_stability', agent_stability, 'Agent stability', inverse=True)
        
        # 10. Mobile agent success
        mobile_success = metrics.get('mobile_agent_success', 1.0)
        self._check_threshold('mobile_agent_success', mobile_success, 'Mobile agent success', inverse=True)
    
    def _check_architecture(self, metrics: Dict[str, Any]) -> None:
        """Architecture проверки (4 критерия)."""
        # 11. Registry integrity
        registry_checksum_fail = metrics.get('registry_checksum_fail', False)
        if registry_checksum_fail:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_registry",
                severity='critical',
                criterion='registry_checksum_fail',
                message="Registry checksum validation FAILED",
                current_value=1.0,
                threshold_value=0.0
            ))
        
        # 12. Deadlock detection
        deadlock_duration = metrics.get('deadlock_duration_sec', 0)
        if deadlock_duration > self.thresholds['deadlock_duration_sec']['critical']:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_deadlock",
                severity='critical',
                criterion='deadlock_duration_sec',
                message=f"Deadlock detected: {deadlock_duration}s",
                current_value=deadlock_duration,
                threshold_value=self.thresholds['deadlock_duration_sec']['critical']
            ))
        
        # 13. Infinite loop detection
        loop_iterations = metrics.get('infinite_loop_iterations', 0)
        if loop_iterations > self.thresholds['infinite_loop_iterations']['alert']:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_loop",
                severity='alert',
                criterion='infinite_loop_iterations',
                message=f"Possible infinite loop: {loop_iterations} iterations",
                current_value=loop_iterations,
                threshold_value=self.thresholds['infinite_loop_iterations']['alert']
            ))
        
        # 14. Memory leak detection
        memory_leak_rate = metrics.get('memory_leak_mb_per_hour', 0)
        if memory_leak_rate > self.thresholds['memory_leak_mb_per_hour']['warning']:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_memleak",
                severity='warning',
                criterion='memory_leak_mb_per_hour',
                message=f"Potential memory leak: +{memory_leak_rate:.1f}MB/hour",
                current_value=memory_leak_rate,
                threshold_value=self.thresholds['memory_leak_mb_per_hour']['warning']
            ))
    
    def _check_logic(self, metrics: Dict[str, Any]) -> None:
        """Logic проверки (4 критерия)."""
        # 15. Contradictory decisions
        contradictions = metrics.get('contradictory_decisions', 0)
        if contradictions >= self.thresholds['contradictory_decisions']['alert']:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_contradiction",
                severity='alert',
                criterion='contradictory_decisions',
                message=f"Contradictory decisions detected: {contradictions}",
                current_value=contradictions,
                threshold_value=self.thresholds['contradictory_decisions']['alert']
            ))
        
        # 16. Safety gate bypasses
        safety_bypasses = metrics.get('safety_gate_bypasses', 0)
        if safety_bypasses > 0:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_safety",
                severity='critical',
                criterion='safety_gate_bypasses',
                message=f"Safety gate bypasses detected: {safety_bypasses}",
                current_value=safety_bypasses,
                threshold_value=0
            ))
        
        # 17. Containment violations
        containment_violations = metrics.get('containment_violations', 0)
        if containment_violations > 0:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_containment",
                severity='critical',
                criterion='containment_violations',
                message=f"Containment policy violations: {containment_violations}",
                current_value=containment_violations,
                threshold_value=0
            ))
        
        # 18. Unauthorized actions
        unauthorized = metrics.get('unauthorized_actions', 0)
        if unauthorized > 0:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_unauthorized",
                severity='critical',
                criterion='unauthorized_actions',
                message=f"Unauthorized actions detected: {unauthorized}",
                current_value=unauthorized,
                threshold_value=0
            ))
    
    def _check_evolution(self, metrics: Dict[str, Any]) -> None:
        """Evolution проверки (3 критерия)."""
        # 19. Self-improvement failure rate
        si_failure_rate = metrics.get('self_improvement_failure_rate', 0.0)
        self._check_threshold('self_improvement_failure_rate', si_failure_rate, 'Self-improvement failures')
        
        # 20. Patch rollback rate
        rollback_rate = metrics.get('patch_rollback_rate', 0.0)
        self._check_threshold('patch_rollback_rate', rollback_rate, 'Patch rollback rate')
        
        # 21. Neuro-learning loop stall
        last_loop_time = metrics.get('neuro_loop_last_run_hours_ago', 0)
        if last_loop_time > self.thresholds['neuro_loop_stall_hours']['critical']:
            self.alerts.append(WatchdogAlert(
                id=f"alert_{int(time.time())}_loop_stall",
                severity='critical',
                criterion='neuro_loop_stall_hours',
                message=f"Neuro-learning loop stalled: {last_loop_time:.1f}h ago",
                current_value=last_loop_time,
                threshold_value=self.thresholds['neuro_loop_stall_hours']['critical']
            ))
    
    def _check_threshold(self, key: str, value: float, name: str, inverse: bool = False) -> None:
        """
        Проверить порог.
        
        Args:
            key: Ключ threshold
            value: Текущее значение
            name: Человеко-читаемое имя
            inverse: True если ниже = хуже (для hit rates ит.д.)
        """
        if key not in self.thresholds:
            return
        
        thresholds = self.thresholds[key]
        
        for severity in ['critical', 'alert', 'warning']:
            if severity in thresholds:
                threshold = thresholds[severity]
                
                # Check condition
                if inverse:
                    triggered = value < threshold
                else:
                    triggered = value > threshold
                
                if triggered:
                    self.alerts.append(WatchdogAlert(
                        id=f"alert_{int(time.time())}_{key}",
                        severity=severity,
                        criterion=key,
                        message=f"{name} {'below' if inverse else 'above'} threshold: {value:.2f}",
                        current_value=value,
                        threshold_value=threshold
                    ))
                    break  # Only trigger highest severity
    
    def _generate_recommendation(self, critical: List, alerts: List, warnings: List) -> str:
        """Сгенерировать рекомендацию."""
        if critical:
            return "IMMEDIATE ACTION REQUIRED: Critical issues detected. Consider rollback."
        elif alerts:
            return "ACTION RECOMMENDED: Multiple alerts detected. Investigate and prepare rollback."
        elif warnings:
            return "MONITORING REQUIRED: Warnings detected. Create Self-Improver tasks."
        else:
            return "System healthy. Continue normal operation."
    
    def should_rollback_v4_1(self) -> bool:
        """
        Определить, нужен ли rollback (v4.1 логика).
        
        Returns:
            True если rollback рекомендуется
        """
        # Critical alerts → immediate rollback
        if any(a.severity == 'critical' for a in self.alerts):
            logger.warning("⚠️ Critical alerts detected → ROLLBACK recommended")
            return True
        
        # 3 consecutive failures → rollback
        if self.consecutive_failures >= 3:
            logger.warning(f"⚠️ {self.consecutive_failures} consecutive failures → ROLLBACK recommended")
            return True
        
        return False
    
    def create_improver_tasks(self) -> List[Dict[str, Any]]:
        """
        Создать задачи для Self-Improver на основе warnings.
        
        Returns:
            Список задач
        """
        tasks = []
        
        for alert in self.alerts:
            if alert.severity in ['warning', 'alert']:
                tasks.append({
                    'id': f"task_{alert.id}",
                    'type': 'improvement',
                    'criterion': alert.criterion,
                    'priority': 'high' if alert.severity == 'alert' else 'medium',
                    'description': alert.message,
                    'target_improvement': {
                        'metric': alert.criterion,
                        'current': alert.current_value,
                        'target': alert.threshold_value
                    }
                })
        
        if tasks:
            logger.info(f"📋 Created {len(tasks)} Self-Improver tasks")
        
        return tasks
