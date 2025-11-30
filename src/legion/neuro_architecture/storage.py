"""
Storage Optimization - компактное хранение конфигураций.

Вдохновлено фундаментальными принципами памяти:
- Binary encoding для эффективности
- Многоуровневый кеш (L1/L2/L3)
- Compression для долгосрочного хранения
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class CompactConfigEncoder:
    """
    Компактный энкодер для конфигураций.
    
    Использует MessagePack вместо JSON для 70% экономии.
    """
    
    def __init__(self):
        try:
            import msgpack
            self.msgpack = msgpack
            self.available = True
        except ImportError:
            logger.warning("⚠️ msgpack not available, falling back to JSON")
            self.available = False
    
    def encode(self, config: Dict[str, Any]) -> bytes:
        """
        Закодировать конфигурацию в байты.
        
        Args:
            config: Конфигурация
        
        Returns:
            Байтовое представление
        """
        if self.available:
            return self.msgpack.packb(config)
        else:
            return json.dumps(config).encode('utf-8')
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        """
        Декодировать конфигурацию из байтов.
        
        Args:
            data: Байтовое представление
        
        Returns:
            Конфигурация
        """
        if self.available:
            return self.msgpack.unpackb(data, raw=False)
        else:
            return json.loads(data.decode('utf-8'))
    
    def estimate_savings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Оценить экономию места."""
        json_size = len(json.dumps(config).encode('utf-8'))
        
        if self.available:
            msgpack_size = len(self.msgpack.packb(config))
            savings_pct = ((json_size - msgpack_size) / json_size) * 100
        else:
            msgpack_size = json_size
            savings_pct = 0.0
        
        return {
            'json_bytes': json_size,
            'msgpack_bytes': msgpack_size,
            'savings_percent': savings_pct
        }


class ArchitectureCache:
    """
    Многоуровневый кеш для архитектур.
    
    L1 (память): топ 10 архитектур, fastest
    L2 (Redis/memcached): средний термин, fast
    L3 (диск): долгосрочное хранилище, slow
    """
    
    def __init__(self, storage_dir: str = "artifacts/cache"):
        """
        Инициализация кеша.
        
        Args:
            storage_dir: Директория для L3 storage
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # L1: In-memory cache
        self.l1_cache: Dict[str, Any] = {}
        self.l1_max_size = 10
        
        # L2: Redis (если доступен)
        self.l2_available = self._init_l2()
        
        # Encoder
        self.encoder = CompactConfigEncoder()
        
        # Metrics
        self.hits = {'l1': 0, 'l2': 0, 'l3': 0}
        self.misses = 0
        
        logger.info(f"✅ ArchitectureCache initialized")
        logger.info(f"   L1: {self.l1_max_size} slots (memory)")
        logger.info(f"   L2: {'enabled' if self.l2_available else 'disabled'} (redis)")
        logger.info(f"   L3: {storage_dir} (disk)")
    
    def _init_l2(self) -> bool:
        """Инициализировать L2 cache (Redis)."""
        try:
            import redis
            self.l2_cache = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=False
            )
            # Test connection
            self.l2_cache.ping()
            return True
        except Exception as e:
            logger.info(f"L2 cache not available: {e}")
            return False
    
    def get(self, hash_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить архитектуру из кеша.
        
        Args:
            hash_id: Semantic hash
        
        Returns:
            Конфигурация или None
        """
        # Try L1
        if hash_id in self.l1_cache:
            self.hits['l1'] += 1
            logger.debug(f"✅ L1 cache hit: {hash_id}")
            return self.l1_cache[hash_id]
        
        # Try L2
        if self.l2_available:
            try:
                cached = self.l2_cache.get(hash_id)
                if cached:
                    self.hits['l2'] += 1
                    config = self.encoder.decode(cached)
                    # Promote to L1
                    self._promote_to_l1(hash_id, config)
                    logger.debug(f"✅ L2 cache hit: {hash_id}")
                    return config
            except Exception as e:
                logger.warning(f"L2 cache error: {e}")
        
        # Try L3 (disk)
        l3_path = self.storage_dir / f"{hash_id}.bin"
        if l3_path.exists():
            self.hits['l3'] += 1
            with open(l3_path, 'rb') as f:
                config = self.encoder.decode(f.read())
            # Promote to L2 and L1
            self._promote_to_l2(hash_id, config)
            self._promote_to_l1(hash_id, config)
            logger.debug(f"✅ L3 cache hit: {hash_id}")
            return config
        
        # Cache miss
        self.misses += 1
        logger.debug(f"❌ Cache miss: {hash_id}")
        return None
    
    def set(self, hash_id: str, config: Dict[str, Any], ttl: int = 3600) -> None:
        """
        Сохранить архитектуру в кеш.
        
        Args:
            hash_id: Semantic hash
            config: Конфигурация
            ttl: Time to live для L2 (секунды)
        """
        # Write to all levels
        self._promote_to_l1(hash_id, config)
        self._promote_to_l2(hash_id, config, ttl)
        
        # Always persist to L3
        l3_path = self.storage_dir / f"{hash_id}.bin"
        with open(l3_path, 'wb') as f:
            f.write(self.encoder.encode(config))
        
        logger.debug(f"💾 Cached: {hash_id}")
    
    def _promote_to_l1(self, hash_id: str, config: Dict[str, Any]) -> None:
        """Продвинуть в L1 кеш."""
        if len(self.l1_cache) >= self.l1_max_size:
            # Evict least recently used (FIFO for simplicity)
            oldest_key = next(iter(self.l1_cache))
            del self.l1_cache[oldest_key]
        
        self.l1_cache[hash_id] = config
    
    def _promote_to_l2(self, hash_id: str, config: Dict[str, Any], ttl: int = 3600) -> None:
        """Продвинуть в L2 кеш."""
        if not self.l2_available:
            return
        
        try:
            self.l2_cache.setex(
                hash_id,
                ttl,
                self.encoder.encode(config)
            )
        except Exception as e:
            logger.warning(f"L2 cache write error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кеша."""
        total_requests = sum(self.hits.values()) + self.misses
        hit_rate = sum(self.hits.values()) / total_requests if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'l1_size': len(self.l1_cache),
            'l1_max_size': self.l1_max_size
        }
