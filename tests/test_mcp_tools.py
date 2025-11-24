"""Unit tests for MCP Tool Registry."""

import pytest
import asyncio
from src.legion.mcp.tools import LegionToolRegistry, ToolDefinition


@pytest.fixture
def registry():
    """Create a fresh tool registry for each test."""
    return LegionToolRegistry()


def test_registry_initialization(registry):
    """Test that registry initializes correctly."""
    assert registry is not None
    assert len(registry) == 0
    assert len(registry.list_tools()) == 0


def test_register_tool(registry):
    """Test tool registration."""
    def dummy_handler(x, y):
        return x + y
    
    registry.register(
        name='add',
        handler=dummy_handler,
        description='Add two numbers',
        category='math'
    )
    
    assert len(registry) == 1
    assert 'add' in registry
    tool = registry.get_tool('add')
    assert tool is not None
    assert tool.name == 'add'
    assert tool.category == 'math'


def test_register_duplicate_tool(registry):
    """Test that duplicate registration overwrites."""
    def handler1():
        return 1
    
    def handler2():
        return 2
    
    registry.register('test', handler1, 'First version')
    registry.register('test', handler2, 'Second version')
    
    assert len(registry) == 1
    tool = registry.get_tool('test')
    assert tool.description == 'Second version'


def test_unregister_tool(registry):
    """Test tool unregistration."""
    registry.register('temp', lambda: None, 'Temporary tool')
    assert 'temp' in registry
    
    result = registry.unregister('temp')
    assert result is True
    assert 'temp' not in registry
    assert len(registry) == 0


def test_unregister_nonexistent_tool(registry):
    """Test unregistering a tool that doesn't exist."""
    result = registry.unregister('nonexistent')
    assert result is False


def test_list_tools_by_category(registry):
    """Test filtering tools by category."""
    registry.register('add', lambda x, y: x + y, 'Add', category='math')
    registry.register('navigate', lambda url: None, 'Navigate', category='browser')
    registry.register('multiply', lambda x, y: x * y, 'Multiply', category='math')
    
    math_tools = registry.list_tools(category='math')
    assert len(math_tools) == 2
    assert all(t.category == 'math' for t in math_tools)
    
    browser_tools = registry.list_tools(category='browser')
    assert len(browser_tools) == 1


def test_list_categories(registry):
    """Test getting all categories."""
    registry.register('tool1', lambda: None, 'Tool 1', category='cat1')
    registry.register('tool2', lambda: None, 'Tool 2', category='cat2')
    registry.register('tool3', lambda: None, 'Tool 3', category='cat1')
    
    categories = registry.list_categories()
    assert len(categories) == 2
    assert 'cat1' in categories
    assert 'cat2' in categories


@pytest.mark.asyncio
async def test_execute_sync_tool(registry):
    """Test executing a synchronous tool."""
    def add(x, y):
        return x + y
    
    registry.register('add', add, 'Add two numbers')
    result = await registry.execute('add', x=2, y=3)
    assert result == 5


@pytest.mark.asyncio
async def test_execute_async_tool(registry):
    """Test executing an asynchronous tool."""
    async def async_add(x, y):
        await asyncio.sleep(0.01)
        return x + y
    
    registry.register('async_add', async_add, 'Async add')
    result = await registry.execute('async_add', x=10, y=20)
    assert result == 30


@pytest.mark.asyncio
async def test_execute_nonexistent_tool(registry):
    """Test executing a tool that doesn't exist."""
    with pytest.raises(KeyError, match="Tool 'missing' not found"):
        await registry.execute('missing')


def test_get_tool_schema(registry):
    """Test getting tool schema."""
    registry.register(
        name='test_tool',
        handler=lambda: None,
        description='Test tool',
        category='testing',
        examples=['example1', 'example2'],
        parameters={'param1': 'string'}
    )
    
    schema = registry.get_tool_schema('test_tool')
    assert schema is not None
    assert schema['name'] == 'test_tool'
    assert schema['description'] == 'Test tool'
    assert schema['category'] == 'testing'
    assert len(schema['examples']) == 2
    assert 'param1' in schema['parameters']


def test_export_schemas(registry):
    """Test exporting all tool schemas."""
    registry.register('tool1', lambda: None, 'Tool 1', category='cat1')
    registry.register('tool2', lambda: None, 'Tool 2', category='cat2')
    
    schemas = registry.export_schemas()
    assert len(schemas) == 2
    assert all('name' in s for s in schemas)
    assert all('description' in s for s in schemas)


def test_tool_definition_repr():
    """Test ToolDefinition string representation."""
    tool = ToolDefinition(
        name='test',
        handler=lambda: None,
        description='Test',
        category='general'
    )
    
    repr_str = repr(tool)
    assert 'test' in repr_str
    assert 'general' in repr_str


def test_registry_repr(registry):
    """Test LegionToolRegistry string representation."""
    registry.register('tool1', lambda: None, 'Tool 1')
    registry.register('tool2', lambda: None, 'Tool 2')
    
    repr_str = repr(registry)
    assert '2 tools' in repr_str
