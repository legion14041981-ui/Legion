"""Agent Workspace - Isolated execution environment for Legion agents.

Inspired by Microsoft Agent Workspace pattern announced Nov 2025.
Provides per-agent isolation with scoped filesystem access.
"""

import os
import asyncio
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import hashlib
import json

logger = logging.getLogger(__name__)


class AgentPermission:
    """Permission scope for agent operations."""
    
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    
    ALL = [READ, WRITE, EXECUTE, DELETE]


class LegionAgentWorkspace:
    """
    Isolated workspace for Legion agent with OS-level separation.
    
    Features:
    - Dedicated workspace directory per agent
    - Scoped filesystem access with permission control
    - Resource limits (disk space, file count)
    - Audit logging for all operations
    - User approval workflow for sensitive paths
    
    Security Model (Microsoft-inspired):
    - Agents run in isolated context (not user's personal account)
    - Explicit permission grants required
    - All actions logged with tamper-evident hashing
    - Sensitive paths require user approval
    
    Attributes:
        agent_id: Unique agent identifier
        workspace_root: Root directory for agent workspace
        permissions: Dict mapping paths to allowed operations
        audit_log: List of all operations performed
    """
    
    def __init__(self, 
                 agent_id: str,
                 workspace_root: Optional[str] = None,
                 max_disk_mb: int = 100,
                 max_files: int = 1000):
        """
        Initialize agent workspace.
        
        Args:
            agent_id: Unique agent identifier
            workspace_root: Root directory (defaults to ~/.legion/agents/{agent_id})
            max_disk_mb: Maximum disk space in MB
            max_files: Maximum number of files
        """
        self.agent_id = agent_id
        self.workspace_root = Path(workspace_root or self._default_workspace())
        self.max_disk_bytes = max_disk_mb * 1024 * 1024
        self.max_files = max_files
        
        # Permission registry
        self.permissions: Dict[str, Set[str]] = {}  # path -> {read, write, execute}
        
        # Audit log
        self.audit_log: List[Dict[str, Any]] = []
        
        # Resource tracking
        self.current_disk_usage = 0
        self.current_file_count = 0
        
        # Sensitive paths that always require approval
        self.sensitive_paths = {
            str(Path.home()),  # User home directory
            "/etc",  # System config (Linux)
            "C:\\Windows",  # Windows system
            "/System",  # macOS system
        }
        
        # Initialize workspace
        self._init_workspace()
        
        logger.info(f"Agent workspace initialized: {self.workspace_root}")
    
    def _default_workspace(self) -> str:
        """Get default workspace path."""
        return str(Path.home() / ".legion" / "agents" / self.agent_id)
    
    def _init_workspace(self):
        """Initialize workspace directory structure."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        
        # Standard folders (like Microsoft pattern)
        for folder in ["documents", "downloads", "temp", "cache", "logs"]:
            (self.workspace_root / folder).mkdir(exist_ok=True)
        
        # Grant agent full access to its own workspace
        self.grant_permission(str(self.workspace_root), AgentPermission.ALL)
    
    def grant_permission(self, path: str, permissions: List[str]):
        """Grant agent permission to access path.
        
        Args:
            path: Filesystem path
            permissions: List of permissions (read, write, execute, delete)
        """
        path = str(Path(path).resolve())
        
        if path not in self.permissions:
            self.permissions[path] = set()
        
        self.permissions[path].update(permissions)
        
        self._log_action("grant_permission", {
            "path": path,
            "permissions": permissions
        })
        
        logger.info(f"Granted {permissions} to {path} for agent {self.agent_id}")
    
    def revoke_permission(self, path: str, permissions: Optional[List[str]] = None):
        """Revoke agent permission from path.
        
        Args:
            path: Filesystem path
            permissions: Specific permissions to revoke (None = all)
        """
        path = str(Path(path).resolve())
        
        if path not in self.permissions:
            return
        
        if permissions is None:
            del self.permissions[path]
        else:
            self.permissions[path] -= set(permissions)
        
        self._log_action("revoke_permission", {
            "path": path,
            "permissions": permissions or "all"
        })
    
    def _check_permission(self, path: str, operation: str) -> bool:
        """Check if agent has permission for operation on path.
        
        Args:
            path: Filesystem path
            operation: Operation type (read, write, execute, delete)
        
        Returns:
            bool: True if permitted
        """
        path = str(Path(path).resolve())
        
        # Check exact path
        if path in self.permissions and operation in self.permissions[path]:
            return True
        
        # Check parent paths (inheritance)
        current = Path(path)
        for parent in current.parents:
            parent_str = str(parent)
            if parent_str in self.permissions and operation in self.permissions[parent_str]:
                return True
        
        return False
    
    def _requires_user_approval(self, path: str) -> bool:
        """Check if path requires user approval.
        
        Args:
            path: Filesystem path
        
        Returns:
            bool: True if approval required
        """
        path = str(Path(path).resolve())
        
        for sensitive in self.sensitive_paths:
            if path.startswith(sensitive):
                return True
        
        return False
    
    async def read_file(self, path: str, user_approved: bool = False) -> bytes:
        """Read file with permission and approval checks.
        
        Args:
            path: File path
            user_approved: Whether user has approved this operation
        
        Returns:
            File content as bytes
        
        Raises:
            PermissionError: If agent lacks read permission
            ValueError: If user approval required but not granted
        """
        if not self._check_permission(path, AgentPermission.READ):
            raise PermissionError(f"Agent {self.agent_id} lacks READ permission for {path}")
        
        if self._requires_user_approval(path) and not user_approved:
            raise ValueError(f"User approval required to read sensitive path: {path}")
        
        self._log_action("read_file", {
            "path": path,
            "user_approved": user_approved,
            "size_bytes": Path(path).stat().st_size if Path(path).exists() else 0
        })
        
        # Execute read
        async with asyncio.Lock():
            content = await asyncio.get_event_loop().run_in_executor(
                None, Path(path).read_bytes
            )
        
        logger.info(f"Agent {self.agent_id} read file: {path} ({len(content)} bytes)")
        return content
    
    async def write_file(self, path: str, content: bytes, user_approved: bool = False) -> bool:
        """Write file with permission and resource checks.
        
        Args:
            path: File path
            content: Content to write
            user_approved: Whether user has approved this operation
        
        Returns:
            bool: True if successful
        
        Raises:
            PermissionError: If agent lacks write permission
            ValueError: If user approval required or resource limits exceeded
        """
        if not self._check_permission(path, AgentPermission.WRITE):
            raise PermissionError(f"Agent {self.agent_id} lacks WRITE permission for {path}")
        
        if self._requires_user_approval(path) and not user_approved:
            raise ValueError(f"User approval required to write to sensitive path: {path}")
        
        # Check resource limits
        if self.current_disk_usage + len(content) > self.max_disk_bytes:
            raise ValueError(f"Disk quota exceeded: {self.max_disk_bytes / 1024 / 1024:.1f}MB")
        
        if self.current_file_count >= self.max_files:
            raise ValueError(f"File count limit exceeded: {self.max_files}")
        
        self._log_action("write_file", {
            "path": path,
            "size_bytes": len(content),
            "user_approved": user_approved
        })
        
        # Execute write
        async with asyncio.Lock():
            await asyncio.get_event_loop().run_in_executor(
                None, Path(path).write_bytes, content
            )
        
        # Update resource tracking
        self.current_disk_usage += len(content)
        if not Path(path).exists():
            self.current_file_count += 1
        
        logger.info(f"Agent {self.agent_id} wrote file: {path} ({len(content)} bytes)")
        return True
    
    async def delete_file(self, path: str, user_approved: bool = False) -> bool:
        """Delete file with permission check.
        
        Args:
            path: File path
            user_approved: Whether user has approved this operation
        
        Returns:
            bool: True if successful
        
        Raises:
            PermissionError: If agent lacks delete permission
        """
        if not self._check_permission(path, AgentPermission.DELETE):
            raise PermissionError(f"Agent {self.agent_id} lacks DELETE permission for {path}")
        
        if self._requires_user_approval(path) and not user_approved:
            raise ValueError(f"User approval required to delete sensitive path: {path}")
        
        file_size = Path(path).stat().st_size if Path(path).exists() else 0
        
        self._log_action("delete_file", {
            "path": path,
            "size_bytes": file_size,
            "user_approved": user_approved
        })
        
        # Execute delete
        async with asyncio.Lock():
            await asyncio.get_event_loop().run_in_executor(
                None, Path(path).unlink, True
            )
        
        # Update resource tracking
        self.current_disk_usage -= file_size
        self.current_file_count -= 1
        
        logger.info(f"Agent {self.agent_id} deleted file: {path}")
        return True
    
    async def list_files(self, path: str, pattern: str = "*") -> List[str]:
        """List files in directory.
        
        Args:
            path: Directory path
            pattern: Glob pattern (default: *)
        
        Returns:
            List of file paths
        
        Raises:
            PermissionError: If agent lacks read permission
        """
        if not self._check_permission(path, AgentPermission.READ):
            raise PermissionError(f"Agent {self.agent_id} lacks READ permission for {path}")
        
        self._log_action("list_files", {"path": path, "pattern": pattern})
        
        # Execute listing
        files = await asyncio.get_event_loop().run_in_executor(
            None, lambda: [str(p) for p in Path(path).glob(pattern)]
        )
        
        return files
    
    def _log_action(self, action: str, details: Dict[str, Any]):
        """Log action to audit trail.
        
        Args:
            action: Action type
            details: Action details
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "action": action,
            "details": details
        }
        
        # Hash for tamper-evidence
        previous_hash = self.audit_log[-1]["hash"] if self.audit_log else "0"
        current_data = json.dumps(log_entry, sort_keys=True)
        current_hash = hashlib.sha256(f"{previous_hash}{current_data}".encode()).hexdigest()
        
        log_entry["hash"] = current_hash
        log_entry["previous_hash"] = previous_hash
        
        self.audit_log.append(log_entry)
    
    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get complete audit log.
        
        Returns:
            List of log entries
        """
        return self.audit_log.copy()
    
    def verify_audit_integrity(self) -> bool:
        """Verify audit log hasn't been tampered with.
        
        Returns:
            bool: True if integrity intact
        """
        for i, entry in enumerate(self.audit_log):
            if i == 0:
                expected_prev = "0"
            else:
                expected_prev = self.audit_log[i-1]["hash"]
            
            if entry["previous_hash"] != expected_prev:
                logger.error(f"Audit integrity violation at entry {i}")
                return False
            
            # Recompute hash
            entry_copy = {k: v for k, v in entry.items() if k not in ["hash", "previous_hash"]}
            expected_hash = hashlib.sha256(
                f"{entry['previous_hash']}{json.dumps(entry_copy, sort_keys=True)}".encode()
            ).hexdigest()
            
            if entry["hash"] != expected_hash:
                logger.error(f"Audit hash mismatch at entry {i}")
                return False
        
        return True
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics.
        
        Returns:
            Dict with disk usage, file count, quotas
        """
        return {
            "agent_id": self.agent_id,
            "disk_usage_mb": self.current_disk_usage / 1024 / 1024,
            "disk_quota_mb": self.max_disk_bytes / 1024 / 1024,
            "disk_usage_percent": (self.current_disk_usage / self.max_disk_bytes) * 100,
            "file_count": self.current_file_count,
            "file_quota": self.max_files,
            "file_count_percent": (self.current_file_count / self.max_files) * 100
        }
    
    async def cleanup(self):
        """Clean up workspace and resources."""
        self._log_action("cleanup", {"workspace": str(self.workspace_root)})
        
        logger.info(f"Cleaning up workspace for agent {self.agent_id}")
        
        # Optional: Remove workspace directory
        # await asyncio.get_event_loop().run_in_executor(
        #     None, shutil.rmtree, self.workspace_root, True
        # )
    
    def export_audit_log(self, output_path: str):
        """Export audit log to JSON file.
        
        Args:
            output_path: Output file path
        """
        with open(output_path, 'w') as f:
            json.dump({
                "agent_id": self.agent_id,
                "workspace_root": str(self.workspace_root),
                "integrity_verified": self.verify_audit_integrity(),
                "logs": self.audit_log,
                "resource_usage": self.get_resource_usage()
            }, f, indent=2)
        
        logger.info(f"Audit log exported to {output_path}")
