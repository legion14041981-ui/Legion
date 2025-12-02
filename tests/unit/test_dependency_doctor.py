"""Unit tests for DependencyDoctor."""

import pytest
from unittest.mock import Mock, patch
from legion.agents.ci_healer.dependency_doctor import (
    DependencyDoctor,
    Patch,
    SAFE_PACKAGES
)


class TestDependencyDoctor:
    """Test suite for DependencyDoctor."""
    
    def test_initialization(self):
        """Test DependencyDoctor initialization."""
        doctor = DependencyDoctor()
        assert doctor.safe_packages == SAFE_PACKAGES
    
    def test_initialization_custom_packages(self):
        """Test initialization with custom safe packages."""
        custom = {'package1', 'package2'}
        doctor = DependencyDoctor(safe_packages=custom)
        assert doctor.safe_packages == custom
    
    def test_extract_module_name_simple(self):
        """Test extracting module name from error message."""
        doctor = DependencyDoctor()
        message = "No module named 'numpy'"
        result = doctor._extract_module_name(message)
        assert result == 'numpy'
    
    def test_extract_module_name_nested(self):
        """Test extracting base module from nested import."""
        doctor = DependencyDoctor()
        message = "No module named 'package.submodule.module'"
        result = doctor._extract_module_name(message)
        assert result == 'package'
    
    def test_extract_module_name_no_match(self):
        """Test module extraction with no match."""
        doctor = DependencyDoctor()
        message = "Some other error"
        result = doctor._extract_module_name(message)
        assert result is None
    
    def test_is_safe_package_in_whitelist(self):
        """Test package whitelist check."""
        doctor = DependencyDoctor()
        assert doctor._is_safe_package('numpy') is True
        assert doctor._is_safe_package('pandas') is True
    
    def test_is_safe_package_not_in_whitelist(self):
        """Test package not in whitelist."""
        doctor = DependencyDoctor()
        assert doctor._is_safe_package('malicious-package') is False
    
    def test_is_safe_package_normalized(self):
        """Test package name normalization."""
        doctor = DependencyDoctor()
        # python-dotenv should match despite dash/underscore
        assert doctor._is_safe_package('python_dotenv') is True
    
    def test_fix_non_module_error(self):
        """Test fix with non-module error returns None."""
        doctor = DependencyDoctor()
        problem = Mock(type='syntax_error', message='Syntax error')
        result = doctor.fix(problem, {})
        assert result is None
    
    def test_fix_unsafe_package(self):
        """Test fix with unsafe package returns None."""
        doctor = DependencyDoctor()
        problem = Mock(
            type='module_error',
            message="No module named 'unsafe_package'"
        )
        result = doctor.fix(problem, {'requirements.txt': ''})
        assert result is None
    
    def test_fix_python_dependency(self):
        """Test fixing Python dependency."""
        doctor = DependencyDoctor()
        problem = Mock(
            type='module_error',
            message="No module named 'numpy'"
        )
        tree = {'requirements.txt': 'pandas>=1.0.0\n'}
        
        with patch.object(doctor, '_get_latest_version', return_value='1.24.0'):
            result = doctor.fix(problem, tree)
        
        assert result is not None
        assert isinstance(result, Patch)
        assert result.file == 'requirements.txt'
        assert 'numpy>=1.24.0' in result.new_content
        assert result.risk_level == 1
        assert result.confidence == 0.80
    
    def test_fix_already_in_requirements(self):
        """Test fix when package already in requirements."""
        doctor = DependencyDoctor()
        problem = Mock(
            type='module_error',
            message="No module named 'numpy'"
        )
        tree = {'requirements.txt': 'numpy>=1.20.0\n'}
        result = doctor.fix(problem, tree)
        assert result is None
    
    @patch('subprocess.run')
    def test_get_latest_version_success(self, mock_run):
        """Test getting latest version successfully."""
        doctor = DependencyDoctor()
        mock_run.return_value = Mock(
            returncode=0,
            stdout='Available versions: 1.24.0, 1.23.0'
        )
        version = doctor._get_latest_version('numpy')
        assert version == '1.24.0'
    
    @patch('subprocess.run')
    def test_get_latest_version_failure(self, mock_run):
        """Test getting latest version with failure."""
        doctor = DependencyDoctor()
        mock_run.return_value = Mock(returncode=1, stdout='')
        version = doctor._get_latest_version('numpy')
        assert version is None
    
    @patch('subprocess.run')
    def test_get_latest_version_timeout(self, mock_run):
        """Test getting latest version with timeout."""
        doctor = DependencyDoctor()
        mock_run.side_effect = Exception("Timeout")
        version = doctor._get_latest_version('numpy')
        assert version is None


class TestPatch:
    """Test Patch dataclass."""
    
    def test_patch_creation(self):
        """Test creating Patch instance."""
        patch = Patch(
            file='requirements.txt',
            new_content='numpy>=1.24.0\n',
            risk_level=1,
            reason='Added numpy dependency',
            confidence=0.85
        )
        assert patch.file == 'requirements.txt'
        assert 'numpy' in patch.new_content
        assert patch.risk_level == 1
        assert patch.confidence == 0.85
