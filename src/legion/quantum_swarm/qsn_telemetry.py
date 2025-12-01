"""QSNTelemetry — Prometheus Telemetry & Health Monitoring v4.5.0

Телеметрия и мониторинг здоровья QSN:
- Prometheus metrics export
- Health check endpoints
- Aggregated cluster metrics
- Performance dashboards integration
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

try:
    from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
    from prometheus_client import Counter, Gauge, Histogram, Info
except ImportError:
    class CollectorRegistry:
        def __init__(self): pass
    def generate_latest(registry): return b""
    CONTENT_TYPE_LATEST = "text/plain"
    class Counter:
        def __init__(self, *args, **kwargs): pass
    class Gauge:
        def __init__(self, *args, **kwargs): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass

logger = logging.getLogger(__name__)


class QSNTelemetry:
    """Телеметрия и мониторинг Quantum-Swarm.
    
    Attributes:
        registry: Prometheus CollectorRegistry
        
    Metrics:
        qsn_info: Информация о версии и конфигурации
        qsn_uptime_seconds: Uptime системы
        qsn_cluster_health: Здоровье кластера (0-1)
    """
    
    def __init__(self, version: str = "4.5.0"):
        self.version = version
        self.registry = CollectorRegistry()
        self._start_time = datetime.now(timezone.utc)
        
        # Metrics
        self._info = Info(
            "qsn_info",
            "QSN version and configuration",
            registry=self.registry
        )
        self._info.info({"version": version, "component": "quantum_swarm"})
        
        self._uptime = Gauge(
            "qsn_uptime_seconds",
            "QSN system uptime",
            registry=self.registry
        )
        
        self._cluster_health = Gauge(
            "qsn_cluster_health",
            "Cluster health score (0-1)",
            registry=self.registry
        )
        
        logger.info(f"QSNTelemetry initialized (version={version})")
    
    def export_metrics(self) -> bytes:
        """Export Prometheus metrics.
        
        Returns:
            Prometheus-formatted metrics
        """
        self._update_uptime()
        return generate_latest(self.registry)
    
    def _update_uptime(self) -> None:
        """Update uptime metric."""
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        self._uptime.set(uptime)
    
    def update_cluster_health(self, health_score: float) -> None:
        """Update cluster health metric.
        
        Args:
            health_score: Health score (0.0-1.0)
        """
        self._cluster_health.set(max(0.0, min(1.0, health_score)))
    
    def get_health_check(self, fabric_status: Dict[str, Any]) -> Dict[str, Any]:
        """Generate health check response.
        
        Args:
            fabric_status: Status from FabricEngine
            
        Returns:
            Health check result
        """
        nodes_count = fabric_status.get("nodes_count", 0)
        is_healthy = nodes_count > 0
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": self.version,
            "nodes_count": nodes_count,
            "uptime_seconds": (datetime.now(timezone.utc) - self._start_time).total_seconds(),
        }
