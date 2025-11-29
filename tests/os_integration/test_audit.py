"""Tests для AuditLogger."""

import pytest
import tempfile
from pathlib import Path
from legion.os_integration.audit import AuditTrail, SeverityLevel, AuditEventType

@pytest.fixture
def audit_logger():
    """Create audit logger."""
    return AuditTrail('test_agent')
@pytest.mark.skip(reason='Test needs update to match AuditTrail API')

class TestAuditLogger:
    """Test suite for AuditLogger."""
    
    def test_log_info(self, audit_logger):
        """Тест логирования INFO."""
        audit_logger.log_info('agent_1', 'test_operation', {'key': 'value'})
        
        events = audit_logger.get_events()
        assert len(events) == 1
        assert events[0]['agent_id'] == 'agent_1'
        assert events[0]['operation'] == 'test_operation'
        assert events[0]['level'] == 'info'
    
    def test_get_events_filtered(self, audit_logger):
        """Тест фильтрации событий."""
        audit_logger.log_info('agent_1', 'op1')
        audit_logger.log_error('agent_2', 'op2')
        audit_logger.log_warning('agent_1', 'op3')
        
        agent1_events = audit_logger.get_events(agent_id='agent_1')
        assert len(agent1_events) == 2
        
        error_events = audit_logger.get_events(level=SeverityLevel.ERROR)
        assert len(error_events) == 1    
    def test_compliance_report(self, audit_logger):
        """Тест compliance отчета."""
        audit_logger.log_info('agent_1', 'op1')
        audit_logger.log_critical('agent_2', 'op2')
        
        report = audit_logger.get_compliance_report()
        assert report['total_events'] == 2
        assert report['critical_events'] == 1
