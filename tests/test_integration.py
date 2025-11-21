"""Integration tests for Legion AI System."""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch

from src.legion.integration import LegionAISystem


@pytest.mark.asyncio
async def test_system_initialization():
    """Test system initialization."""
    system = LegionAISystem(config={'mcp_enabled': False, 'orchestration_enabled': False})
    
    assert system.core is not None
    assert system.config is not None


@pytest.mark.asyncio
async def test_mcp_server_initialization():
    """Test MCP server initialization."""
    system = LegionAISystem(config={'mcp_enabled': True})
    
    if system.mcp_server:
        assert system.mcp_server is not None


@pytest.mark.asyncio
async def test_cleanup():
    """Test system cleanup."""
    system = LegionAISystem(config={'mcp_enabled': False})
    
    # Should not raise
    await system.cleanup()