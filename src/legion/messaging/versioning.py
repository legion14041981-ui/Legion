"""
Event schema versioning for LEGION Message Bus.

STAGE 2A: Advanced Features
Component: Event Versioning
Strategy: Semantic Versioning (MAJOR.MINOR.PATCH)
Purpose: Schema evolution with backward compatibility

Features:
- Automatic schema migration
- Semantic versioning
- Migration registry
- Backward compatibility

Risk Level: 🟫 MEDIUM (migration testing required)
Status: 🔥 IN DEVELOPMENT
Timeline: Week 1 of STAGE 2A
"""

from typing import Callable, Dict, Optional
from enum import Enum


class EventVersion:
    """Event schema versioning support."""
    
    CURRENT_VERSION = "1.0"
    
    # Migration handlers: version → migration function
    MIGRATIONS: Dict[str, Callable] = {
        "0.9": lambda e: migrate_0_9_to_1_0(e),
        "1.0": lambda e: e,  # No-op for current version
    }


def migrate_0_9_to_1_0(event: 'Event') -> 'Event':
    """
    Migrate event from schema 0.9 to 1.0.
    
    Schema changes:
    - 'old_field' → 'new_field'
    - Add 'timestamp_ms' field
    """
    if 'old_field' in event.data:
        event.data['new_field'] = event.data.pop('old_field')
    
    if 'timestamp_ms' not in event.data:
        from datetime import datetime
        event.data['timestamp_ms'] = int(event.timestamp.timestamp() * 1000)
    
    return event
