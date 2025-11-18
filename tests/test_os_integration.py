"""Automated Testing Suite for Legion v2.2 OS Integration.

Tests workspace isolation, identity management, OS interface, and audit trail.
"""

import asyncio
import pytest
import os
import tempfile
from pathlib import Path

# Test imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from legion.os_integration import (
    LegionAgentWorkspace,
    LegionAgentIdentity,
    LegionOSInterface,
    LegionAuditTrail
)


class TestAgentWorkspace:
    """Test suite for Agent Workspace isolation."""
    
    @pytest.mark.asyncio
    async def test_workspace_creation(self):
        """Test workspace directory creation."""
        workspace = LegionAgentWorkspace("test-agent-1")
        
        assert workspace.workspace_root.exists()
        assert (workspace.workspace_root / "documents").exists()
        assert (workspace.workspace_root / "temp").exists()
        
        await workspace.cleanup()
    
    @pytest.mark.asyncio
    async def test_permission_system(self):
        """Test permission grant/revoke."""
        workspace = LegionAgentWorkspace("test-agent-2")
        
        test_path = "/tmp/test"
        workspace.grant_permission(test_path, ["read", "write"])
        
        assert workspace._check_permission(test_path, "read")
        assert workspace._check_permission(test_path, "write")
        assert not workspace._check_permission(test_path, "delete")
        
        workspace.revoke_permission(test_path, ["write"])
        assert not workspace._check_permission(test_path, "write")
        
        await workspace.cleanup()
    
    @pytest.mark.asyncio
    async def test_file_operations(self):
        """Test read/write with permissions."""
        workspace = LegionAgentWorkspace("test-agent-3")
        
        # Create test file in workspace
        test_file = workspace.workspace_root / "test.txt"
        test_content = b"Hello Legion v2.2"
        
        # Write should work (workspace has full permissions)
        await workspace.write_file(str(test_file), test_content)
        
        # Read should work
        content = await workspace.read_file(str(test_file))
        assert content == test_content
        
        # Delete should work
        await workspace.delete_file(str(test_file))
        assert not test_file.exists()
        
        await workspace.cleanup()
    
    @pytest.mark.asyncio
    async def test_resource_limits(self):
        """Test disk quota enforcement."""
        workspace = LegionAgentWorkspace("test-agent-4", max_disk_mb=1)  # 1MB limit
        
        test_file = workspace.workspace_root / "large.txt"
        large_content = b"x" * (2 * 1024 * 1024)  # 2MB
        
        # Should fail due to quota
        with pytest.raises(ValueError, match="Disk quota exceeded"):
            await workspace.write_file(str(test_file), large_content)
        
        await workspace.cleanup()
    
    def test_audit_integrity(self):
        """Test tamper-evident audit log."""
        workspace = LegionAgentWorkspace("test-agent-5")
        
        # Perform some actions
        workspace.grant_permission("/test", ["read"])
        workspace.revoke_permission("/test")
        
        # Verify integrity
        assert workspace.verify_audit_integrity()
        
        # Try to tamper
        if workspace.audit_log:
            workspace.audit_log[0]["action"] = "TAMPERED"
            assert not workspace.verify_audit_integrity()


class TestAgentIdentity:
    """Test suite for Agent Identity & Authentication."""
    
    @pytest.mark.asyncio
    async def test_identity_creation(self):
        """Test agent identity initialization."""
        identity = LegionAgentIdentity("test-agent-100")
        
        assert identity.agent_id == "test-agent-100"
        assert identity.entra_id == "legion-agent-test-agent-100"
        assert len(identity.granted_scopes) == 0
    
    @pytest.mark.asyncio
    async def test_scope_request(self):
        """Test permission scope requests."""
        identity = LegionAgentIdentity("test-agent-101")
        
        # Request low-risk scope (auto-approve)
        granted = await identity.request_scope("files.read", "Test read access")
        assert granted
        assert "files.read" in identity.granted_scopes
    
    @pytest.mark.asyncio
    async def test_token_generation(self):
        """Test authentication token lifecycle."""
        identity = LegionAgentIdentity("test-agent-102")
        
        # Grant scope
        await identity.request_scope("files.read")
        
        # Generate token
        token = await identity.generate_token(["files.read"])
        
        assert token.is_valid()
        assert token.has_scope("files.read")
        assert token.token in identity.active_tokens
        
        # Validate token
        validated = identity.validate_token(token.token)
        assert validated is not None
        assert validated.agent_id == "test-agent-102"
    
    @pytest.mark.asyncio
    async def test_token_refresh(self):
        """Test token refresh mechanism."""
        identity = LegionAgentIdentity("test-agent-103")
        
        await identity.request_scope("files.read")
        old_token = await identity.generate_token(["files.read"])
        
        # Refresh
        new_token = await identity.refresh_token(old_token.refresh_token)
        
        assert new_token is not None
        assert new_token.token != old_token.token
        assert new_token.scopes == old_token.scopes
    
    def test_credential_management(self):
        """Test external credential storage."""
        identity = LegionAgentIdentity("test-agent-104")
        
        identity.set_credential("openai", "sk-test-key")
        
        retrieved = identity.get_credential("openai")
        assert retrieved == "sk-test-key"
        
        # Check audit log
        assert len(identity.auth_log) >= 2  # set + get


class TestOSInterface:
    """Test suite for OS Interface Layer."""
    
    @pytest.mark.asyncio
    async def test_terminal_tool(self):
        """Test terminal command execution."""
        workspace = LegionAgentWorkspace("test-agent-200")
        identity = LegionAgentIdentity("test-agent-200")
        
        # Grant system.execute scope
        await identity.request_scope("system.execute")
        
        interface = LegionOSInterface(workspace, identity)
        
        # Execute simple command
        result = await interface.execute_task({
            "tool": "terminal",
            "params": {"command": "echo 'Hello Legion'"}
        })
        
        assert result["success"]
        assert "Hello Legion" in result["stdout"]
        
        await workspace.cleanup()
    
    @pytest.mark.asyncio
    async def test_filesystem_tool(self):
        """Test filesystem operations via OS interface."""
        workspace = LegionAgentWorkspace("test-agent-201")
        identity = LegionAgentIdentity("test-agent-201")
        
        interface = LegionOSInterface(workspace, identity)
        
        test_file = workspace.workspace_root / "interface_test.txt"
        
        # Write
        result = await interface.execute_task({
            "tool": "filesystem",
            "params": {
                "operation": "write",
                "path": str(test_file),
                "content": "OS Interface Test"
            }
        })
        
        assert result["success"]
        
        # Read
        result = await interface.execute_task({
            "tool": "filesystem",
            "params": {
                "operation": "read",
                "path": str(test_file)
            }
        })
        
        assert result["success"]
        assert "OS Interface Test" in result["content"]
        
        await workspace.cleanup()
    
    @pytest.mark.asyncio
    async def test_python_interpreter(self):
        """Test Python code execution."""
        workspace = LegionAgentWorkspace("test-agent-202")
        identity = LegionAgentIdentity("test-agent-202")
        
        await identity.request_scope("system.execute")
        
        interface = LegionOSInterface(workspace, identity)
        
        result = await interface.execute_task({
            "tool": "python",
            "params": {
                "code": "print('Legion v2.2'); result = 2 + 2"
            }
        })
        
        assert result["success"]
        assert "Legion v2.2" in result["stdout"]
        
        await workspace.cleanup()


class TestAuditTrail:
    """Test suite for Audit Trail."""
    
    @pytest.mark.asyncio
    async def test_audit_logging(self):
        """Test basic audit logging."""
        audit = LegionAuditTrail("test-agent-300")
        
        hash1 = await audit.log_action(
            "file_read",
            target="/test/file.txt",
            risk_level="low"
        )
        
        hash2 = await audit.log_action(
            "file_write",
            target="/test/file.txt",
            risk_level="medium"
        )
        
        assert len(audit.entries) == 2
        assert hash1 != hash2
        assert audit.entries[1].previous_hash == hash1
    
    def test_integrity_verification(self):
        """Test blockchain-style integrity check."""
        audit = LegionAuditTrail("test-agent-301")
        
        asyncio.run(audit.log_action("test1", risk_level="low"))
        asyncio.run(audit.log_action("test2", risk_level="low"))
        asyncio.run(audit.log_action("test3", risk_level="low"))
        
        # Should be valid
        assert audit.verify_integrity()
        
        # Tamper with entry
        if len(audit.entries) > 1:
            audit.entries[1].action_type = "TAMPERED"
            # Integrity should fail
            assert not audit.verify_integrity()
    
    def test_compliance_report(self):
        """Test compliance report generation."""
        audit = LegionAuditTrail("test-agent-302")
        
        asyncio.run(audit.log_action("file_read", risk_level="low"))
        asyncio.run(audit.log_action("execute_command", risk_level="high"))
        asyncio.run(audit.log_action("api_call", risk_level="medium"))
        
        report = audit.generate_compliance_report()
        
        assert report["agent_id"] == "test-agent-302"
        assert report["total_actions"] == 3
        assert report["integrity_status"] == "VERIFIED"
        assert "SOC 2" in report["compliance_standards"]


class TestIntegration:
    """Integration tests combining all components."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow with all components."""
        # Setup
        workspace = LegionAgentWorkspace("integration-test")
        identity = LegionAgentIdentity("integration-test")
        audit = LegionAuditTrail("integration-test")
        
        # Request scopes
        await identity.request_scope("files.read")
        await identity.request_scope("files.write")
        
        # Generate token
        token = await identity.generate_token(["files.read", "files.write"])
        
        # Perform operations
        test_file = workspace.workspace_root / "integration.txt"
        
        await workspace.write_file(str(test_file), b"Integration test")
        await audit.log_action("file_write", target=str(test_file), risk_level="medium")
        
        content = await workspace.read_file(str(test_file))
        await audit.log_action("file_read", target=str(test_file), risk_level="low")
        
        # Verify
        assert content == b"Integration test"
        assert len(audit.entries) == 2
        assert audit.verify_integrity()
        assert workspace.verify_audit_integrity()
        
        # Cleanup
        await workspace.cleanup()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
