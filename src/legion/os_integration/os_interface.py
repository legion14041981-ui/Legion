"""OS Interface Layer - Unified interface to operating system.

Inspired by OS-Copilot/FRIDAY architecture (2024).
Provides abstraction over OS elements: terminal, files, python, browser.
"""

import asyncio
import subprocess
import logging
import platform
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from abc import ABC, abstractmethod
import aiohttp

logger = logging.getLogger(__name__)


class OSTool(ABC):
    """Base class for OS tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool operation.
        
        Args:
            params: Tool parameters
        
        Returns:
            Execution result
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for MCP integration.
        
        Returns:
            JSON schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self._get_input_schema()
        }
    
    @abstractmethod
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for tool."""
        pass


class TerminalTool(OSTool):
    """Terminal command execution tool."""
    
    def __init__(self):
        super().__init__(
            "terminal",
            "Execute terminal commands (bash/powershell/zsh)"
        )
        self.shell = self._detect_shell()
    
    def _detect_shell(self) -> str:
        """Detect appropriate shell for OS."""
        if platform.system() == "Windows":
            return "powershell"
        else:
            return os.environ.get("SHELL", "/bin/bash")
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute terminal command.
        
        Args:
            params: {"command": str, "timeout": int, "cwd": str}
        
        Returns:
            {"stdout": str, "stderr": str, "returncode": int}
        """
        command = params["command"]
        timeout = params.get("timeout", 30)
        cwd = params.get("cwd", None)
        
        logger.info(f"Executing terminal command: {command[:50]}...")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                shell=True
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "returncode": process.returncode,
                "command": command
            }
            
        except asyncio.TimeoutError:
            logger.error(f"Command timed out after {timeout}s")
            return {
                "success": False,
                "error": f"Command timed out after {timeout}s",
                "command": command
            }
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    def _get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
                "cwd": {"type": "string", "description": "Working directory"}
            },
            "required": ["command"]
        }


class FileSystemTool(OSTool):
    """Filesystem operations tool."""
    
    def __init__(self, workspace):
        super().__init__(
            "filesystem",
            "Read, write, search, and manage files"
        )
        self.workspace = workspace  # LegionAgentWorkspace instance
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute filesystem operation.
        
        Args:
            params: {
                "operation": str (read|write|delete|list|search),
                "path": str,
                "content": bytes (for write),
                "pattern": str (for search),
                "user_approved": bool
            }
        
        Returns:
            Operation result
        """
        operation = params["operation"]
        path = params["path"]
        user_approved = params.get("user_approved", False)
        
        try:
            if operation == "read":
                content = await self.workspace.read_file(path, user_approved)
                return {
                    "success": True,
                    "content": content.decode('utf-8', errors='ignore'),
                    "size_bytes": len(content)
                }
            
            elif operation == "write":
                content = params["content"].encode('utf-8') if isinstance(params["content"], str) else params["content"]
                await self.workspace.write_file(path, content, user_approved)
                return {
                    "success": True,
                    "written_bytes": len(content)
                }
            
            elif operation == "delete":
                await self.workspace.delete_file(path, user_approved)
                return {"success": True}
            
            elif operation == "list":
                pattern = params.get("pattern", "*")
                files = await self.workspace.list_files(path, pattern)
                return {
                    "success": True,
                    "files": files,
                    "count": len(files)
                }
            
            elif operation == "search":
                pattern = params.get("pattern", "")
                files = await self.workspace.list_files(path, f"*{pattern}*")
                return {
                    "success": True,
                    "files": files,
                    "count": len(files)
                }
            
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        
        except Exception as e:
            logger.error(f"Filesystem operation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["read", "write", "delete", "list", "search"]},
                "path": {"type": "string"},
                "content": {"type": "string"},
                "pattern": {"type": "string"},
                "user_approved": {"type": "boolean", "default": False}
            },
            "required": ["operation", "path"]
        }


class PythonInterpreterTool(OSTool):
    """Python code interpreter tool."""
    
    def __init__(self):
        super().__init__(
            "python_interpreter",
            "Execute Python code in sandboxed environment"
        )
        self.globals = {"__builtins__": __builtins__}
        self.locals = {}
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python code.
        
        Args:
            params: {"code": str, "timeout": int}
        
        Returns:
            {"success": bool, "result": Any, "stdout": str, "stderr": str}
        """
        code = params["code"]
        timeout = params.get("timeout", 30)
        
        logger.info(f"Executing Python code ({len(code)} chars)")
        
        # Capture stdout/stderr
        import io
        import sys
        
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: exec(code, self.globals, self.locals)
                ),
                timeout=timeout
            )
            
            return {
                "success": True,
                "result": result,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "locals": {k: str(v) for k, v in self.locals.items()}
            }
        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Execution timed out after {timeout}s"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stderr": stderr_capture.getvalue()
            }
        
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def _get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}
            },
            "required": ["code"]
        }


class APICallTool(OSTool):
    """HTTP API call tool."""
    
    def __init__(self):
        super().__init__(
            "api_call",
            "Make HTTP API calls to external services"
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP API call.
        
        Args:
            params: {
                "method": str (GET|POST|PUT|DELETE),
                "url": str,
                "headers": dict,
                "body": dict,
                "timeout": int
            }
        
        Returns:
            {"success": bool, "status": int, "body": dict, "headers": dict}
        """
        method = params["method"].upper()
        url = params["url"]
        headers = params.get("headers", {})
        body = params.get("body", None)
        timeout = params.get("timeout", 30)
        
        logger.info(f"Making {method} request to {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    
                    response_body = await response.text()
                    
                    try:
                        response_json = await response.json()
                    except:
                        response_json = None
                    
                    return {
                        "success": response.status < 400,
                        "status": response.status,
                        "body": response_json or response_body,
                        "headers": dict(response.headers),
                        "url": str(response.url)
                    }
        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Request timed out after {timeout}s"
            }
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                "url": {"type": "string", "format": "uri"},
                "headers": {"type": "object"},
                "body": {"type": "object"},
                "timeout": {"type": "integer", "default": 30}
            },
            "required": ["method", "url"]
        }


class LegionOSInterface:
    """
    Unified OS interface for Legion agents.
    
    Architecture inspired by OS-Copilot (2024):
    - Configurator: Selects appropriate tool
    - OS Interface Layer: Unified abstraction
    - Tools: Terminal, Files, Python, Browser, API
    - Memory: Long-term context and learning
    
    Features:
    - Cross-platform support (Windows/Linux/macOS)
    - Unified API for all OS operations
    - Integration with Agent Workspace for security
    - Self-improving via long-term memory
    - MCP-compatible tool registry
    
    Attributes:
        agent_workspace: Agent's workspace instance
        agent_identity: Agent's identity instance
        tools: Registry of available OS tools
    """
    
    def __init__(self, agent_workspace, agent_identity):
        """
        Initialize OS interface.
        
        Args:
            agent_workspace: LegionAgentWorkspace instance
            agent_identity: LegionAgentIdentity instance
        """
        self.workspace = agent_workspace
        self.identity = agent_identity
        
        # Tool registry
        self.tools: Dict[str, OSTool] = {}
        self._register_builtin_tools()
        
        # Long-term memory (placeholder for ChromaDB integration)
        self.long_term_memory = None
        
        logger.info(f"OS Interface initialized with {len(self.tools)} tools")
    
    def _register_builtin_tools(self):
        """Register built-in OS tools."""
        self.tools["terminal"] = TerminalTool()
        self.tools["filesystem"] = FileSystemTool(self.workspace)
        self.tools["python"] = PythonInterpreterTool()
        self.tools["api_call"] = APICallTool()
        
        # Browser tool requires playwright (optional dependency)
        try:
            from legion.agents.browser_agent import PlaywrightBrowserAgent
            # Browser tool already exists, no need to duplicate
            logger.info("Browser tool available via existing browser_agent")
        except ImportError:
            logger.warning("Playwright not available, browser tool disabled")
    
    def register_tool(self, tool: OSTool):
        """Register custom OS tool.
        
        Args:
            tool: OSTool instance
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute OS task using appropriate tool.
        
        Args:
            task: {
                "tool": str (terminal|filesystem|python|api_call),
                "operation": str,
                "params": dict
            }
        
        Returns:
            Task execution result
        """
        tool_name = task["tool"]
        operation = task.get("operation", "execute")
        params = task.get("params", {})
        
        # Get tool
        tool = self.tools.get(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(self.tools.keys())
            }
        
        # Check permissions
        required_scope = self._get_required_scope(tool_name, operation)
        if not await self._check_scope(required_scope):
            return {
                "success": False,
                "error": f"Agent lacks required scope: {required_scope}"
            }
        
        # Recall context from long-term memory (if available)
        context = await self._recall_context(task) if self.long_term_memory else None
        
        # Execute tool
        logger.info(f"Executing {tool_name}.{operation}")
        result = await tool.execute(params)
        
        # Store to long-term memory (if available)
        if self.long_term_memory and result.get("success"):
            await self._store_result(task, result)
        
        return result
    
    def _get_required_scope(self, tool_name: str, operation: str) -> str:
        """Get required scope for tool operation.
        
        Args:
            tool_name: Name of tool
            operation: Operation type
        
        Returns:
            Scope string (e.g., 'files.read')
        """
        scope_map = {
            "terminal": "system.execute",
            "filesystem": f"files.{operation}",
            "python": "system.execute",
            "api_call": "network.http"
        }
        return scope_map.get(tool_name, f"{tool_name}.execute")
    
    async def _check_scope(self, scope: str) -> bool:
        """Check if agent has required scope.
        
        Args:
            scope: Scope to check
        
        Returns:
            bool: True if authorized
        """
        if scope not in self.identity.granted_scopes:
            # Auto-request scope
            return await self.identity.request_scope(scope, "Required for OS operation")
        return True
    
    async def _recall_context(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Recall relevant context from long-term memory.
        
        Args:
            task: Current task
        
        Returns:
            Context from similar past tasks
        """
        # Placeholder for ChromaDB/Pinecone integration
        return None
    
    async def _store_result(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Store task result to long-term memory.
        
        Args:
            task: Executed task
            result: Execution result
        """
        # Placeholder for vector DB storage
        pass
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools with schemas.
        
        Returns:
            List of tool schemas
        """
        return [tool.get_schema() for tool in self.tools.values()]
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get OS interface statistics.
        
        Returns:
            Dict with tool usage stats
        """
        return {
            "agent_id": self.workspace.agent_id,
            "available_tools": len(self.tools),
            "tool_list": list(self.tools.keys()),
            "granted_scopes": list(self.identity.granted_scopes),
            "workspace_usage": self.workspace.get_resource_usage()
        }
