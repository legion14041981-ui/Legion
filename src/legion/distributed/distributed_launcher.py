"""Distributed Launcher - запуск distributed кластера."""

import logging
import argparse
from typing import Optional

try:
    import ray
    from ray.cluster_utils import Cluster
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False
    ray = None
    Cluster = None

logger = logging.getLogger(__name__)


def launch_cluster(
    num_workers: int = 4,
    num_cpus_per_worker: int = 2,
    redis_address: Optional[str] = None
) -> None:
    """
    Запустить Ray cluster для distributed выполнения.
    
    Args:
        num_workers: Количество workers
        num_cpus_per_worker: CPU на worker
        redis_address: Redis адрес (если подключение к существующему кластеру)
    """
    if not RAY_AVAILABLE:
        raise ImportError("Ray not installed")
    
    if redis_address:
        # Подключение к существующему кластеру
        logger.info(f"Connecting to existing cluster: {redis_address}")
        ray.init(address=redis_address)
    else:
        # Создать local cluster
        logger.info(f"Starting local cluster with {num_workers} workers")
        cluster = Cluster(
            initialize_head=True,
            head_node_args={'num_cpus': num_cpus_per_worker}
        )
        
        for i in range(num_workers - 1):
            cluster.add_node(num_cpus=num_cpus_per_worker)
        
        ray.init(address=cluster.address)
    
    logger.info("✅ Ray cluster started successfully")
    logger.info(f"   Nodes: {len(ray.nodes())}")
    logger.info(f"   Resources: {ray.cluster_resources()}")


def main():
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(description='Launch Legion Distributed Cluster')
    parser.add_argument('-w', '--workers', type=int, default=4, help='Number of workers')
    parser.add_argument('-c', '--cpus', type=int, default=2, help='CPUs per worker')
    parser.add_argument('-r', '--redis', type=str, help='Redis address for existing cluster')
    
    args = parser.parse_args()
    
    try:
        launch_cluster(
            num_workers=args.workers,
            num_cpus_per_worker=args.cpus,
            redis_address=args.redis
        )
        
        print("✅ Cluster is ready. Press Ctrl+C to stop.")
        
        import time
        while True:
            time.sleep(10)
    
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down cluster...")
        if ray.is_initialized():
            ray.shutdown()
        print("✅ Cluster stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        import sys
        sys.exit(1)


if __name__ == '__main__':
    main()
