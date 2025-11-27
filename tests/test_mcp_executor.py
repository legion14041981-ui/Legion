"""Unit tests for MCP Code Execution Engine."""

import pytest
import asyncio
from src.legion.mcp.tools import LegionToolRegistry
from src.legion.mcp.executor import CodeExecutionEngine


@pytest.fixture
def tool_registry():
    """Create a tool registry with some test tools."""
    registry = LegionToolRegistry()
    
    # Add test tools
    async def test_tool(message):
        return f"Echo: {message}"
    
    registry.register(
        name='test_echo',
        handler=test_tool,
        description='Echo a message',
        category='test'
    )
    
    return registry


@pytest.fixture
def executor(tool_registry):
    """Create code execution engine."""
    return CodeExecutionEngine(tool_registry, timeout=5)


@pytest.mark.asyncio
async def test_executor_initialization(executor):
    """Test that executor initializes correctly."""
    assert executor is not None
    assert executor.timeout == 5
    assert executor.tool_registry is not None


@pytest.mark.asyncio
async def test_execute_simple_code(executor):
    """Test executing simple Python code."""
    code = """
result = 2 + 2
"""
    result = await executor.execute(code)
    
    assert result['success'] is True
    assert result['result'] == 4
    assert result['error'] is None


@pytest.mark.asyncio
async def test_execute_code_with_print(executor):
    """Test that print output is captured."""
    code = """
print("Hello, World!")
result = 42
"""
    result = await executor.execute(code)
    
    assert result['success'] is True
    assert 'Hello, World!' in result['output']
    assert result['result'] == 42


@pytest.mark.asyncio
async def test_execute_code_with_tools(executor):
    """Test executing code that uses registered tools."""
    code = """
result = await tools.execute('test_echo', message='Hello')
"""
    result = await executor.execute(code)
    
    assert result['success'] is True
    assert 'Echo: Hello' in str(result['result'])


@pytest.mark.asyncio
async def test_execute_code_with_syntax_error(executor):
    """Test that syntax errors are caught."""
    code = """
if True
    print("Missing colon")
"""
    result = await executor.execute(code)
    
    assert result['success'] is False
    assert result['error'] is not None
    assert 'error' in result['error'].lower()


@pytest.mark.asyncio
async def test_execute_code_with_timeout(executor):
    """Test that timeout is enforced."""
    code = """
import time
time.sleep(10)  # Will be interrupted by timeout
result = 'completed'
"""
    result = await executor.execute(code)
    
    assert result['success'] is False
    assert 'timeout' in result['error'].lower()


@pytest.mark.asyncio
async def test_execute_code_with_forbidden_import(executor):
    """Test that RestrictedPython blocks dangerous imports."""
    code = """
import os
os.system('echo Dangerous')
"""
    result = await executor.execute(code)
    
    # RestrictedPython should prevent this
    assert result['success'] is False


@pytest.mark.asyncio
async def test_execute_with_context(executor):
    """Test executing code with additional context."""
    code = """
result = x + y
"""
    context = {'x': 10, 'y': 20}
    result = await executor.execute(code, context=context)
    
    assert result['success'] is True
    assert result['result'] == 30


@pytest.mark.asyncio
async def test_execute_code_with_runtime_error(executor):
    """Test that runtime errors are caught."""
    code = """
result = 1 / 0  # Division by zero
"""
    result = await executor.execute(code)
    
    assert result['success'] is False
    assert result['error'] is not None


@pytest.mark.asyncio
async def test_execute_code_with_list_tools(executor):
    """Test that code can list available tools."""
    code = """
available_tools = tools.list()
result = len(available_tools)
"""
    result = await executor.execute(code)
    
    assert result['success'] is True
    assert result['result'] >= 1  # At least test_echo


@pytest.mark.asyncio
async def test_execute_script_from_file(executor, tmp_path):
    """Test executing a script from a file."""
    # Create temporary script file
    script_path = tmp_path / "test_script.py"
    script_path.write_text("result = 100")
    
    result = await executor.execute_script(str(script_path))
    
    assert result['success'] is True
    assert result['result'] == 100


@pytest.mark.asyncio
async def test_execute_script_file_not_found(executor):
    """Test executing a non-existent script."""
    result = await executor.execute_script("/nonexistent/script.py")
    
    assert result['success'] is False
    assert 'not found' in result['error'].lower()


def test_validate_code_valid(executor):
    """Test validating syntactically correct code."""
    code = """
x = 10
y = 20
result = x + y
"""
    validation = executor.validate_code(code)
    
    assert validation['valid'] is True
    assert len(validation['errors']) == 0


def test_validate_code_invalid_syntax(executor):
    """Test validating code with syntax errors."""
    code = """
if True
    print("Missing colon")
"""
    validation = executor.validate_code(code)
    
    assert validation['valid'] is False
    assert len(validation['errors']) > 0


def test_validate_code_unsafe_imports(executor):
    """Test that unsafe imports generate warnings."""
    code = """
import os
import subprocess
result = 'test'
"""
    validation = executor.validate_code(code)
    
    # Should have warnings about unsafe imports
    assert len(validation['warnings']) > 0
    assert any('os' in w for w in validation['warnings'])
    assert any('subprocess' in w for w in validation['warnings'])


def test_executor_repr(executor):
    """Test CodeExecutionEngine string representation."""
    repr_str = repr(executor)
    assert 'CodeExecutionEngine' in repr_str
    assert 'timeout=5' in repr_str


@pytest.mark.asyncio
async def test_safe_globals_builtins(executor):
    """Test that safe builtins are available."""
    code = """
result = {
    'len_available': callable(len),
    'str_available': callable(str),
    'list_available': callable(list),
    'dict_available': callable(dict),
}
"""
    result = await executor.execute(code)
    
    assert result['success'] is True
    result_dict = result['result']
    assert all(result_dict.values())  # All should be True


@pytest.mark.asyncio
async def test_executor_no_file_access(executor):
    """Test that file access is restricted."""
    code = """
with open('/etc/passwd', 'r') as f:
    result = f.read()
"""
    result = await executor.execute(code)
    
    # Should fail due to RestrictedPython
    assert result['success'] is False
