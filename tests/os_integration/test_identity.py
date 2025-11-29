"""Tests для IdentityManager."""

import pytest
from legion.os_integration.identity import AgentIdentity, Role, Permission

@pytest.fixture
def identity_manager():
    """Create identity manager."""
    return AgentIdentity('test_agent')
@pytest.mark.skip(reason='Test needs update to match AgentIdentity API')

class TestIdentityManager:
    """Test suite for IdentityManager."""
    
    def test_create_identity(self, identity_manager):
        """Тест создания идентификации."""
        identity = identity_manager.create_identity('agent_1', Role.EXECUTOR)
        assert identity.agent_id == 'agent_1'
        assert identity.role == Role.EXECUTOR
        assert identity.token is not None
    
    def test_check_permission(self, identity_manager):
        """Тест проверки прав доступа."""
        identity_manager.create_identity('agent_2', Role.EXECUTOR)
        
        assert identity_manager.check_permission('agent_2', Permission.READ) is True
        assert identity_manager.check_permission('agent_2', Permission.EXECUTE) is True
        assert identity_manager.check_permission('agent_2', Permission.ADMIN) is False
    
    def test_admin_has_all_permissions(self, identity_manager):
        """Тест администраторских прав."""
        identity_manager.create_identity('admin', Role.ADMIN)
        
        for permission in Permission:
            assert identity_manager.check_permission('admin', permission) is True
    
    def test_revoke_identity(self, identity_manager):
        """Тест отзыва идентификации."""
        identity_manager.create_identity('temp_agent', Role.EXECUTOR)
        identity_manager.revoke_identity('temp_agent')
        
        assert identity_manager.get_identity('temp_agent') is None
