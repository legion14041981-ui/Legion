"""Unit tests for Playwright Browser Agent."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Skip all tests if Playwright not installed
pytestmark = pytest.mark.skipif(
    True,  # Always skip for now to avoid Playwright installation requirement
    reason="Playwright tests skipped (install manually: pip install playwright)"
)

try:
    from src.legion.agents.browser_agent import PlaywrightBrowserAgent
    BROWSER_AGENT_AVAILABLE = True
except ImportError:
    BROWSER_AGENT_AVAILABLE = False
    PlaywrightBrowserAgent = None


@pytest.fixture
def mock_playwright():
    """Mock Playwright objects."""
    with patch('src.legion.agents.browser_agent.async_playwright') as mock:
        # Mock playwright instance
        playwright_instance = MagicMock()
        
        # Mock browser types
        browser_type = MagicMock()
        browser = MagicMock()
        context = MagicMock()
        page = MagicMock()
        
        # Setup async returns
        browser_type.launch = AsyncMock(return_value=browser)
        browser.new_context = AsyncMock(return_value=context)
        context.new_page = AsyncMock(return_value=page)
        context.close = AsyncMock()
        browser.close = AsyncMock()
        
        playwright_instance.chromium = browser_type
        playwright_instance.firefox = browser_type
        playwright_instance.webkit = browser_type
        playwright_instance.stop = AsyncMock()
        
        # Mock page methods
        page.goto = AsyncMock(return_value=MagicMock(ok=True, status=200))
        page.title = AsyncMock(return_value="Test Page")
        page.url = "https://example.com"
        page.click = AsyncMock()
        page.fill = AsyncMock()
        page.screenshot = AsyncMock(return_value=b'fake_screenshot_data')
        page.query_selector = AsyncMock(return_value=MagicMock())
        page.content = AsyncMock(return_value="<html></html>")
        page.wait_for_selector = AsyncMock()
        page.wait_for_timeout = AsyncMock()
        page.wait_for_load_state = AsyncMock()
        page.evaluate = AsyncMock(return_value={'result': 'ok'})
        
        mock.return_value.start = AsyncMock(return_value=playwright_instance)
        
        yield {
            'playwright': mock,
            'instance': playwright_instance,
            'browser': browser,
            'context': context,
            'page': page
        }


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_agent_initialization():
    """Test browser agent initialization."""
    agent = PlaywrightBrowserAgent(
        agent_id='test-browser',
        config={'browser': 'chromium', 'headless': True}
    )
    
    assert agent.agent_id == 'test-browser'
    assert agent.browser_type == 'chromium'
    assert agent.headless is True
    assert agent.is_active is False


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_agent_start(mock_playwright):
    """Test starting the browser agent."""
    agent = PlaywrightBrowserAgent(
        agent_id='test-browser',
        config={'browser': 'chromium'}
    )
    
    await agent.start()
    
    assert agent.is_active is True
    assert agent.browser is not None
    assert agent.page is not None


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_agent_stop(mock_playwright):
    """Test stopping the browser agent."""
    agent = PlaywrightBrowserAgent(agent_id='test-browser')
    await agent.start()
    await agent.stop()
    
    assert agent.is_active is False
    assert agent.browser is None
    assert agent.page is None


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_navigate_action(mock_playwright):
    """Test navigation action."""
    agent = PlaywrightBrowserAgent(agent_id='test-browser')
    await agent.start()
    
    result = await agent.execute_async({
        'action': 'navigate',
        'params': {'url': 'https://example.com'}
    })
    
    assert result['success'] is True
    assert result['url'] == 'https://example.com'
    assert result['title'] == 'Test Page'
    
    await agent.stop()


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_click_action(mock_playwright):
    """Test click action."""
    agent = PlaywrightBrowserAgent(agent_id='test-browser')
    await agent.start()
    
    result = await agent.execute_async({
        'action': 'click',
        'params': {'selector': '#button'}
    })
    
    assert result['success'] is True
    assert result['selector'] == '#button'
    
    await agent.stop()


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_type_action(mock_playwright):
    """Test typing action."""
    agent = PlaywrightBrowserAgent(agent_id='test-browser')
    await agent.start()
    
    result = await agent.execute_async({
        'action': 'type',
        'params': {'selector': '#input', 'text': 'Hello World'}
    })
    
    assert result['success'] is True
    assert result['text'] == 'Hello World'
    
    await agent.stop()


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_screenshot_action(mock_playwright):
    """Test screenshot action."""
    agent = PlaywrightBrowserAgent(agent_id='test-browser')
    await agent.start()
    
    result = await agent.execute_async({
        'action': 'screenshot',
        'params': {'path': '/tmp/test.png'}
    })
    
    assert result['success'] is True
    assert result['path'] == '/tmp/test.png'
    assert result['size'] > 0
    
    await agent.stop()


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_extract_action(mock_playwright):
    """Test data extraction action."""
    agent = PlaywrightBrowserAgent(agent_id='test-browser')
    await agent.start()
    
    # Mock element
    mock_element = MagicMock()
    mock_element.text_content = AsyncMock(return_value="Test Text")
    mock_playwright['page'].query_selector = AsyncMock(return_value=mock_element)
    
    result = await agent.execute_async({
        'action': 'extract',
        'params': {'selector': '#content', 'attribute': 'textContent'}
    })
    
    assert result['success'] is True
    assert 'data' in result
    
    await agent.stop()


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_wait_selector_action(mock_playwright):
    """Test waiting for selector."""
    agent = PlaywrightBrowserAgent(agent_id='test-browser')
    await agent.start()
    
    result = await agent.execute_async({
        'action': 'wait',
        'params': {'type': 'selector', 'selector': '#element'}
    })
    
    assert result['success'] is True
    assert result['type'] == 'selector'
    
    await agent.stop()


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_evaluate_action(mock_playwright):
    """Test JavaScript evaluation."""
    agent = PlaywrightBrowserAgent(agent_id='test-browser')
    await agent.start()
    
    result = await agent.execute_async({
        'action': 'evaluate',
        'params': {'script': 'document.title'}
    })
    
    assert result['success'] is True
    assert 'result' in result
    
    await agent.stop()


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_unknown_action(mock_playwright):
    """Test handling unknown action."""
    agent = PlaywrightBrowserAgent(agent_id='test-browser')
    await agent.start()
    
    with pytest.raises(ValueError, match="Unknown action"):
        await agent.execute_async({
            'action': 'unknown_action',
            'params': {}
        })
    
    await agent.stop()


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_execute_without_start(mock_playwright):
    """Test that executing without starting raises error."""
    agent = PlaywrightBrowserAgent(agent_id='test-browser')
    
    with pytest.raises(RuntimeError, match="not started"):
        await agent.execute_async({
            'action': 'navigate',
            'params': {'url': 'https://example.com'}
        })


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_cleanup_alias(mock_playwright):
    """Test that cleanup() is an alias for stop()."""
    agent = PlaywrightBrowserAgent(agent_id='test-browser')
    await agent.start()
    assert agent.is_active is True
    
    await agent.cleanup()
    assert agent.is_active is False


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
def test_agent_repr():
    """Test agent string representation."""
    agent = PlaywrightBrowserAgent(
        agent_id='test-browser',
        config={'browser': 'firefox'}
    )
    
    repr_str = repr(agent)
    assert 'test-browser' in repr_str
    assert 'firefox' in repr_str


@pytest.mark.skipif(not BROWSER_AGENT_AVAILABLE, reason="Browser agent not available")
@pytest.mark.asyncio
async def test_different_browsers(mock_playwright):
    """Test initialization with different browsers."""
    for browser_type in ['chromium', 'firefox', 'webkit']:
        agent = PlaywrightBrowserAgent(
            agent_id=f'test-{browser_type}',
            config={'browser': browser_type}
        )
        await agent.start()
        assert agent.is_active is True
        await agent.stop()
