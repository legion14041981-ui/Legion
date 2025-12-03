"""
Memory Management Module

Provides memory-efficient data structures and leak prevention.
"""

from .lru_cache import LRUCache
from .ttl_dict import TTLDict

__all__ = ['LRUCache', 'TTLDict']
