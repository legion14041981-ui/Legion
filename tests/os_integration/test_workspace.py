"""Tests для Workspace."""

import pytest
import tempfile
from pathlib import Path
from legion.os_integration import Workspace, WorkspaceConfig


@pytest.fixture
def temp_workspace():
    """Create temporary workspace."""
    config = WorkspaceConfig(
        max_disk_usage_mb=100,
        max_memory_mb=256,
        temp_dir=Path(tempfile.gettempdir())
    )
    workspace = Workspace('test_agent', config)
    yield workspace
    workspace.cleanup()


class TestWorkspace:
    """Test suite for Workspace."""
    
    def test_workspace_creation(self, temp_workspace):
        """Тест создания workspace."""
        assert temp_workspace.root.exists()
        assert (temp_workspace.root / 'input').exists()
        assert (temp_workspace.root / 'output').exists()
        assert (temp_workspace.root / 'temp').exists()
    
    def test_validate_path_inside_workspace(self, temp_workspace):
        """Тест валидации пути внутри workspace."""
        valid_path = temp_workspace.root / 'input' / 'test.txt'
        assert temp_workspace.validate_path(valid_path) is True
    
    def test_validate_path_outside_workspace(self, temp_workspace):
        """Тест запрета доступа за пределы workspace."""
        invalid_path = Path('/etc/passwd')
        assert temp_workspace.validate_path(invalid_path) is False
    
    def test_check_disk_usage(self, temp_workspace):
        """Тест проверки использования диска."""
        usage = temp_workspace.check_disk_usage()
        assert 'used_mb' in usage
        assert 'limit_mb' in usage
        assert usage['limit_mb'] == 100
    
    def test_resource_status(self, temp_workspace):
        """Тест получения статуса ресурсов."""
        status = temp_workspace.get_resource_status()
        assert status['agent_id'] == 'test_agent'
        assert 'disk' in status
        assert 'memory' in status
        assert 'cpu' in status
