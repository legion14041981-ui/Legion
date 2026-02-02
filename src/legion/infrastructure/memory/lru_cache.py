"""
LRU Cache Implementation

Memory-bounded cache with automatic eviction of least recently used items.
"""

from collections import OrderedDict
from typing import Any, Optional
import threading


class LRUCache:
    """
    Thread-safe LRU Cache с automatic memory management.
    
    Features:
    - Bounded size (automatic eviction)
    - O(1) get/set operations
    - Thread-safe
    - Memory efficient
    
    Example:
        cache = LRUCache(max_size=1000)
        cache.set("task_123", result)
        value = cache.get("task_123")  # Returns result or None
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items (default 1000)
        """
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.RLock()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        with self._lock:
            if key in self._cache:
                # Move to end (mark as recently used)
                self._cache.move_to_end(key)
                self.hits += 1
                return self._cache[key]
            else:
                self.misses += 1
                return None
    
    def set(self, key: str, value: Any):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            if key in self._cache:
                # Update existing
                self._cache.move_to_end(key)
            else:
                # Add new item
                if len(self._cache) >= self.max_size:
                    # Evict LRU item
                    self._cache.popitem(last=False)
                    self.evictions += 1
            
            self._cache[key] = value
    
    def delete(self, key: str):
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0
    
    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with hit rate, size, evictions
        """
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate_percent': hit_rate,
                'evictions': self.evictions,
                'memory_usage_mb': self._estimate_size_mb()
            }
    
    def _estimate_size_mb(self) -> float:
        """Estimate memory usage in MB"""
        import sys
        total_size = 0
        
        with self._lock:
            for key, value in self._cache.items():
                total_size += sys.getsizeof(key)
                total_size += sys.getsizeof(value)
        
        return total_size / (1024 * 1024)
