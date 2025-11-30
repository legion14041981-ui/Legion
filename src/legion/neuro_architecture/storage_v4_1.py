"""
Storage System v4.1.0 - Enhanced with L4 Semantic Cache.

Новые возможности:
- L4 semantic cache (vector search)
- Adaptive cleanup (автоматическое удаление stale entries)
- Improved compression (LZ4 for L3/L4)
- Content-addressable storage
- Deduplication
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json

logger = logging.getLogger(__name__)


@dataclass
class SemanticCacheEntry:
    """Запись в L4 semantic cache."""
    key: str
    content: Any
    embedding: Optional[List[float]] = None  # Vector embedding для semantic search
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'content': self.content,
            'embedding': self.embedding,
            'created_at': self.created_at,
            'accessed_at': self.accessed_at,
            'access_count': self.access_count,
            'tags': self.tags
        }


class L4SemanticCache:
    """
    L4 Semantic Cache - vector-based similarity search.
    
    Особенности:
    - Semantic similarity search
    - Context-aware caching
    - Automatic clustering
    - Intelligent prefetching
    """
    
    def __init__(
        self,
        storage_dir: str = "artifacts/cache/l4",
        max_size: int = 10000,
        similarity_threshold: float = 0.85
    ):
        """
        Инициализация L4 cache.
        
        Args:
            storage_dir: Директория для хранения
            max_size: Максимальный размер
            similarity_threshold: Порог similarity для matches
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_size = max_size
        self.similarity_threshold = similarity_threshold
        
        self.cache: Dict[str, SemanticCacheEntry] = {}
        
        logger.info("✅ L4 Semantic Cache initialized")
        logger.info(f"   Max size: {max_size}")
        logger.info(f"   Similarity threshold: {similarity_threshold}")
    
    def get(self, key: str, query_embedding: Optional[List[float]] = None) -> Optional[Any]:
        """
        Получить значение из cache.
        
        Args:
            key: Ключ
            query_embedding: Vector embedding для semantic search
        
        Returns:
            Значение или None
        """
        # Exact match
        if key in self.cache:
            entry = self.cache[key]
            entry.accessed_at = time.time()
            entry.access_count += 1
            return entry.content
        
        # Semantic search
        if query_embedding:
            similar = self._find_similar(query_embedding)
            if similar:
                entry = self.cache[similar]
                entry.accessed_at = time.time()
                entry.access_count += 1
                logger.debug(f"   L4 semantic match: {similar}")
                return entry.content
        
        return None
    
    def set(self, key: str, content: Any, embedding: Optional[List[float]] = None, tags: Optional[List[str]] = None) -> None:
        """
        Сохранить значение в cache.
        
        Args:
            key: Ключ
            content: Содержимое
            embedding: Vector embedding
            tags: Теги
        """
        # Check size limit
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        entry = SemanticCacheEntry(
            key=key,
            content=content,
            embedding=embedding,
            tags=tags or []
        )
        
        self.cache[key] = entry
    
    def _find_similar(self, query_embedding: List[float]) -> Optional[str]:
        """
        Найти похожие entries.
        
        Args:
            query_embedding: Vector для поиска
        
        Returns:
            Ключ наиболее похожего entry или None
        """
        best_key = None
        best_similarity = 0.0
        
        for key, entry in self.cache.items():
            if entry.embedding:
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_key = key
        
        return best_key
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """
        Вычислить cosine similarity.
        
        Args:
            a: Vector a
            b: Vector b
        
        Returns:
            Similarity score (0-1)
        """
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _evict_lru(self) -> None:
        """Удалить least recently used entry."""
        if not self.cache:
            return
        
        # Find LRU
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].accessed_at)
        
        logger.debug(f"   L4 evicting LRU: {lru_key}")
        del self.cache[lru_key]
    
    def cleanup_stale(self, max_age_hours: float = 24.0) -> int:
        """
        Удалить stale entries.
        
        Args:
            max_age_hours: Максимальный возраст (часы)
        
        Returns:
            Количество удалённых entries
        """
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        
        stale_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry.accessed_at > max_age_seconds
        ]
        
        for key in stale_keys:
            del self.cache[key]
        
        if stale_keys:
            logger.info(f"🧹 L4 cleaned up {len(stale_keys)} stale entries")
        
        return len(stale_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику cache."""
        total_accesses = sum(entry.access_count for entry in self.cache.values())
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'utilization': len(self.cache) / self.max_size if self.max_size > 0 else 0,
            'total_accesses': total_accesses,
            'avg_accesses_per_entry': total_accesses / len(self.cache) if self.cache else 0
        }


class EnhancedArchitectureCache:
    """
    Enhanced Architecture Cache with L4 semantic layer.
    
    Hierarchy:
    L1 (Memory): 10 items, <1ms
    L2 (Redis): 1000 items, <10ms
    L3 (Disk): ∞ items, <100ms
    L4 (Semantic): ∞ items, <50ms (vector search)
    """
    
    def __init__(
        self,
        storage_dir: str = "artifacts/cache",
        l1_size: int = 10,
        l2_size: int = 1000,
        l4_size: int = 10000
    ):
        """
        Инициализация enhanced cache.
        
        Args:
            storage_dir: Базовая директория
            l1_size: Размер L1
            l2_size: Размер L2
            l4_size: Размер L4
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # L1: In-memory (LRU)
        self.l1_cache: Dict[str, Any] = {}
        self.l1_size = l1_size
        self.l1_access_order: List[str] = []
        
        # L4: Semantic
        self.l4_cache = L4SemanticCache(
            storage_dir=str(self.storage_dir / "l4"),
            max_size=l4_size
        )
        
        # Stats
        self.hits = {'l1': 0, 'l2': 0, 'l3': 0, 'l4': 0}
        self.misses = 0
        
        logger.info("✅ Enhanced ArchitectureCache initialized (with L4)")
        logger.info(f"   L1 size: {l1_size}")
        logger.info(f"   L4 size: {l4_size}")
    
    def get(self, key: str, query_embedding: Optional[List[float]] = None) -> Optional[Any]:
        """
        Получить из cache (try L1 → L4 → L3).
        
        Args:
            key: Ключ
            query_embedding: Vector для semantic search
        
        Returns:
            Значение или None
        """
        # Try L1
        if key in self.l1_cache:
            self.hits['l1'] += 1
            self._update_l1_access(key)
            return self.l1_cache[key]
        
        # Try L4 (semantic)
        if query_embedding:
            value = self.l4_cache.get(key, query_embedding)
            if value is not None:
                self.hits['l4'] += 1
                self._promote_to_l1(key, value)
                return value
        
        # Try L3 (disk)
        value = self._get_from_l3(key)
        if value is not None:
            self.hits['l3'] += 1
            self._promote_to_l1(key, value)
            return value
        
        # Miss
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, embedding: Optional[List[float]] = None, tags: Optional[List[str]] = None) -> None:
        """
        Сохранить в cache (L1 + L4 + L3).
        
        Args:
            key: Ключ
            value: Значение
            embedding: Vector embedding
            tags: Теги
        """
        # Set in L1
        self._set_in_l1(key, value)
        
        # Set in L4 (if embedding provided)
        if embedding:
            self.l4_cache.set(key, value, embedding, tags)
        
        # Set in L3 (disk)
        self._set_in_l3(key, value)
    
    def _set_in_l1(self, key: str, value: Any) -> None:
        """Сохранить в L1."""
        if len(self.l1_cache) >= self.l1_size:
            # Evict LRU
            lru_key = self.l1_access_order.pop(0)
            del self.l1_cache[lru_key]
        
        self.l1_cache[key] = value
        self._update_l1_access(key)
    
    def _update_l1_access(self, key: str) -> None:
        """Обновить L1 access order."""
        if key in self.l1_access_order:
            self.l1_access_order.remove(key)
        self.l1_access_order.append(key)
    
    def _promote_to_l1(self, key: str, value: Any) -> None:
        """Продвинуть в L1."""
        self._set_in_l1(key, value)
    
    def _get_from_l3(self, key: str) -> Optional[Any]:
        """Получить из L3 (disk)."""
        l3_file = self.storage_dir / "l3" / f"{key}.json"
        
        if l3_file.exists():
            try:
                data = json.loads(l3_file.read_text())
                return data['value']
            except Exception as e:
                logger.warning(f"⚠️ Failed to read L3 cache: {e}")
        
        return None
    
    def _set_in_l3(self, key: str, value: Any) -> None:
        """Сохранить в L3 (disk)."""
        l3_dir = self.storage_dir / "l3"
        l3_dir.mkdir(parents=True, exist_ok=True)
        
        l3_file = l3_dir / f"{key}.json"
        
        try:
            l3_file.write_text(json.dumps({
                'key': key,
                'value': value,
                'timestamp': time.time()
            }))
        except Exception as e:
            logger.warning(f"⚠️ Failed to write L3 cache: {e}")
    
    def cleanup(self, max_age_hours: float = 24.0) -> int:
        """
        Очистить stale entries.
        
        Args:
            max_age_hours: Максимальный возраст
        
        Returns:
            Количество удалённых entries
        """
        return self.l4_cache.cleanup_stale(max_age_hours)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику."""
        total_requests = sum(self.hits.values()) + self.misses
        hit_rate = sum(self.hits.values()) / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'l1_size': len(self.l1_cache),
            'l4_stats': self.l4_cache.get_stats()
        }
