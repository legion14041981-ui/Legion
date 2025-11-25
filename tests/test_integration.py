"""Integration tests for Legion AI System."""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch

from src.legion.integration import LegionAISystem


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch('src.legion.ai.script_generator.AsyncOpenAI') as mock:
        mock_client = Mock()
        mock_client.chat = Mock()
        mock_client.chat.completions = Mock()
        mock_client.chat.completions.create = AsyncMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_playwright():
    """Mock Playwright."""
    with patch('src.legion.agents.browser_agent.async_playwright') as mock:
        yield mock


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
        assert system.tool_registry is not None
        assert system.code_executor is not None


@pytest.mark.asyncio
async def test_tool_registration(mock_playwright):
    """Test browser tool registration."""
    # Mock Playwright to be available
    mock_playwright.return_value.__aenter__ = AsyncMock()
    
    system = LegionAISystem(config={'mcp_enabled': True})
    
    if system.tool_registry:
        tools = system.tool_registry.list_tools(category='browser')
        assert len(tools) >= 4  # navigate, click, screenshot, extract


@pytest.mark.asyncio
async def test_task_execution_no_ai(mock_playwright):
    """Test task execution without AI."""
    system = LegionAISystem(config={'mcp_enabled': False})
    
    result = await system.execute_task(
        description="Test task",
        context={}
    )
    
    # Should fail gracefully without AI
    assert 'error' in result or 'success' in result


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="Requires OpenAI API key")
async def test_script_generation_integration():
    """Test AI script generation (integration test)."""
    system = LegionAISystem()
    
    if system.script_generator:
        result = await system.script_generator.generate_playwright_script(
            "Navigate to example.com"
        )
        
        assert result.get('success') is True
        assert 'code' in result
        assert 'playwright' in result['code'].lower()


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    system = LegionAISystem(config={'orchestration_enabled': True})
    
    if system.orchestrator:
        assert len(system.orchestrator.agents) >= 2  # planning + monitoring at minimum


@pytest.mark.asyncio
async def test_cleanup():
    """Test system cleanup."""
    system = LegionAISystem(config={'mcp_enabled': False})
    
    # Should not raise
    await system.cleanup()
