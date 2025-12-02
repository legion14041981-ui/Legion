# Changelog

All notable changes to Legion Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with 50+ tests
- Complete CI/CD pipeline with GitHub Actions
- Full documentation suite (README, CONTRIBUTING, SECURITY, etc.)
- Deployment guide with Docker and Kubernetes examples
- Troubleshooting guide

### Changed
- Updated README with detailed installation and usage instructions
- Enhanced security documentation

## [2.3.0] - 2025-12-02

### Added
- Task dispatching implementation with intelligent routing
- Agent capabilities system for smart task routing
- Task queue for unmatched tasks
- Custom exception hierarchy (LegionError, TaskDispatchError, etc.)
- Async task dispatching support
- Health check and metrics endpoints
- Comprehensive docstrings throughout codebase

### Fixed
- **SECURITY**: Subprocess injection vulnerability in dependency_doctor.py
- **PERFORMANCE**: Memory leak in watchdog.py history tracking
- Missing dispatch_task() implementation in core.py

### Changed
- Improved error handling with specific exception types
- Enhanced logging in safe_load_dotenv with encoding detection
- Renamed Patch.diff to Patch.new_content for clarity
- Made HealthCheckResult immutable (frozen dataclass)

### Security
- Added package whitelist validation
- Replaced unsafe subprocess.run with explicit args
- Improved input validation across all modules

## [2.2.0] - 2025-11-20

### Added
- OS Integration v2.2
- Async/await support for non-blocking execution
- Base agent class with async methods
- Performance monitoring with watchdog

### Changed
- Updated Python requirement to 3.9+
- Improved agent lifecycle management

## [2.1.0] - 2025-11-10

### Added
- CI Healer agent with dependency doctor
- Automated dependency fixing
- Database integration

### Fixed
- Various bug fixes and stability improvements

## [2.0.0] - 2025-11-01

### Added
- Multi-agent framework foundation
- Core dispatching system
- Basic agent implementation
- Docker support
- Initial CI/CD setup

### Changed
- Complete rewrite of architecture
- New agent registration system

## [1.0.0] - 2025-10-30

### Added
- Initial release
- Basic agent functionality
- Simple task execution

---

## Version History

- **2.3.0** (2025-12-02): Production-ready with tests, CI/CD, and docs
- **2.2.0** (2025-11-20): OS Integration and async support
- **2.1.0** (2025-11-10): CI Healer and dependency management
- **2.0.0** (2025-11-01): Multi-agent architecture
- **1.0.0** (2025-10-30): Initial release

## Migration Guides

### 2.2.x → 2.3.x

**Breaking Changes:**
- `Patch.diff` renamed to `Patch.new_content`
- Agent registration now requires explicit capabilities

**Migration Steps:**

```python
# Before
core.register_agent('my_agent', agent)

# After
core.register_agent('my_agent', agent, capabilities=['general'])
```

### 2.1.x → 2.2.x

**Breaking Changes:**
- Async methods added to base agent
- OS Integration configuration changed

**Migration Steps:**

Update .env file with new OS Integration settings.
