"""
TTL Dictionary

Dictionary with automatic expiration of old entries.
"""

import time
import threading
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class TTLDict:
    """
    Dictionary с automatic TTL (Time To Live) cleanup.
    
    Features:
    - Automatic removal of expired entries
    - Background cleanup thread
    - Thread-safe
    
    Example:
        ttl_dict = TTLDict(ttl_seconds=3600)  # 1 hour TTL
        ttl_dict['task_123'] = result
        # After 1 hour, task_123 is auto-removed
    """
    
    def __init__(self, ttl_seconds: int = 3600, cleanup_interval: int = 300):
        """
        Initialize TTL dictionary.
        
        Args:
            ttl_seconds: Time to live for entries (default 1 hour)
            cleanup_interval: Cleanup interval in seconds (default 5 min)
        """
        self.ttl_seconds = ttl_seconds
        self.cleanup_interval = cleanup_interval
        
        self._data: Dict[str, tuple] = {}  # key -> (value, timestamp)
        self._lock = threading.RLock()
        
        # Statistics
        self.expired_count = 0
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def __setitem__(self, key: str, value: Any):
        """Set item with current timestamp"""
        with self._lock:
            self._data[key] = (value, time.time())
    
    def __getitem__(self, key: str) -> Any:
        """Get item if not expired"""
        with self._lock:
            if key not in self._data:
                raise KeyError(key)
            
            value, timestamp = self._data[key]
            
            # Check if expired
            if time.time() - timestamp > self.ttl_seconds:
                del self._data[key]
                self.expired_count += 1
                raise KeyError(f"{key} (expired)")
            
            return value
    
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """Get item with default if not found/expired"""
        try:
            return self[key]
        except KeyError:
            return default
    
    def __delitem__(self, key: str):
        """Delete item"""
        with self._lock:
            del self._data[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists and not expired"""
        try:
            _ = self[key]
            return True
        except KeyError:
            return False
    
    def __len__(self) -> int:
        """Get number of non-expired entries"""
        with self._lock:
            return len(self._data)
    
    def clear(self):
        """Clear all entries"""
        with self._lock:
            self._data.clear()
    
    def _cleanup_loop(self):
        """Background cleanup thread"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"TTL cleanup error: {e}")
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        
        with self._lock:
            expired_keys = [
                key for key, (_, timestamp) in self._data.items()
                if current_time - timestamp > self.ttl_seconds
            ]
            
            for key in expired_keys:
                del self._data[key]
                self.expired_count += 1
            
            if expired_keys:
                logger.debug(f"TTL cleanup: removed {len(expired_keys)} expired entries")
    
    def get_stats(self) -> dict:
        """Get statistics"""
        with self._lock:
            return {
                'size': len(self._data),
                'expired_total': self.expired_count,
                'ttl_seconds': self.ttl_seconds
            }
