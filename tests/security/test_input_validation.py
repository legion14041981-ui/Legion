"""Security Tests - Input Validation"""

import pytest
from legion.infrastructure.validation import InputSanitizer


class TestInputSanitizer:
    """Test input sanitization against injection attacks"""
    
    @pytest.mark.parametrize("payload,expected", [
        ("'; DROP TABLE users--", " DROP TABLE users"),
        ("admin' OR '1'='1", "admin OR 11"),
        ("1; DELETE FROM tasks", "1 DELETE FROM tasks"),
        ("' UNION SELECT * FROM passwords--", "  SELECT  FROM passwords"),
    ])
    def test_sql_injection_prevention(self, payload, expected):
        result = InputSanitizer.sanitize_sql(payload)
        assert "'" not in result
        assert ";" not in result
        assert "--" not in result
    
    @pytest.mark.parametrize("payload", [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert('XSS')",
        "<iframe src='evil.com'></iframe>",
    ])
    def test_xss_prevention(self, payload):
        result = InputSanitizer.sanitize_html(payload)
        assert "<script" not in result.lower()
        assert "onerror" not in result.lower()
        assert "javascript:" not in result.lower()
    
    @pytest.mark.parametrize("payload", [
        "; rm -rf /",
        "& whoami",
        "| cat /etc/passwd",
        "`id`",
        "$(cat /etc/shadow)",
    ])
    def test_command_injection_prevention(self, payload):
        result = InputSanitizer.sanitize_command(payload)
        assert ";" not in result
        assert "&" not in result
        assert "|" not in result
        assert "`" not in result
        assert "$" not in result
    
    @pytest.mark.parametrize("payload", [
        "../../etc/passwd",
        "..\\..\\windows\\system32",
        "~/../../root/.ssh/id_rsa",
        "/etc/shadow",
    ])
    def test_path_traversal_prevention(self, payload):
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_path(payload)
