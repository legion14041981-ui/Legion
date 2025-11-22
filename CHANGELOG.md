# Changelog

All notable changes to Legion AI System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Pre-commit hooks configuration for automated code quality
- `pyproject.toml` for modern Python tooling configuration
- `Makefile` with 30+ development commands
- Docker production setup (Dockerfile, docker-compose.yml, .dockerignore)
- Dependabot configuration for automated dependency updates
- Code of Conduct (Contributor Covenant v2.1)

### Changed
- Migrated to `pyproject.toml` from `setup.py` (backwards compatible)

## [2.0.0] - 2025-11-15

### Added - AI Enhancements 🤖

#### MCP Protocol (CRITICAL)
- Model Context Protocol server implementation
- Tool registry supporting 100+ tools
- MCP client for external servers
- Sandboxed code execution engine with RestrictedPython
- HMAC-based security for tool calls

#### Browser Automation (HIGH PRIORITY)
- Playwright integration (Chromium, Firefox, WebKit)
- Cross-browser compatibility
- Auto-wait for elements
- Self-healing on selector changes
- Screenshot & PDF generation
- Session persistence

#### AI Script Generation (HIGH PRIORITY)
- GPT-5.1-Codex integration
- Natural language → Playwright script generation
- Syntax validation
- AI-powered script repair (self-healing)
- Context-aware code generation

#### Multi-Agent Orchestration (MEDIUM-HIGH)
- LangGraph-based orchestrator
- **Planning Agent** - task decomposition using GPT
- **Execution Agent** - browser automation execution
- **Monitoring Agent** - error detection & recovery
- 4 orchestration patterns: Sequential, Parallel, Hierarchical, Handoff

#### Integration System
- Unified `LegionAISystem` class
- Auto-initialization of all components
- Graceful degradation when optional deps missing
- Configuration-driven behavior

### Changed
- **BREAKING**: Minimum Python version now 3.9 (was 3.8)
- Updated architecture to support async/await patterns
- Enhanced logging with structured output

### Infrastructure
- New examples: `ai_automation_demo.py`
- Comprehensive integration tests
- Updated documentation in Notion
- CI/CD pipeline enhancements

### Dependencies
- Added: `playwright==1.45.0`
- Added: `openai>=1.0.0`
- Added: `langgraph>=0.1.0`
- Added: `fastapi==0.104.1`
- Added: `restrictedpython>=6.2`
- Added: `pytest-playwright>=0.4.0`

## [1.0.0] - 2025-10-30

### Added - Core Framework
- `LegionCore` - main coordinator for agent lifecycle
- `LegionAgent` - base class for creating custom agents
- `TaskQueue` - asynchronous task queue system
- `LegionDatabase` - Supabase integration
- Specialized agents:
  - `EmailAgent` - email automation
  - `GoogleSheetsAgent` - spreadsheet operations
  - `DataAgent` - data processing

### Infrastructure
- Supabase Edge Functions:
  - `process-task` - task processing
  - `get-pending-tasks` - queue retrieval
- GitHub Actions CI/CD pipeline
- Comprehensive test suite with pytest
- Documentation in Notion

### Dependencies
- `supabase==2.9.0`
- `python-dotenv==1.0.1`
- `httpx==0.27.0`
- Google Sheets integration packages

## [0.1.0] - 2025-10-15

### Added
- Initial project structure
- Basic agent framework
- README and LICENSE

---

## Migration Guides

### Upgrading to v2.0.0 from v1.0.0

#### Required Changes

1. **Update Python version**
   ```bash
   # Ensure Python 3.9+
   python --version
   ```

2. **Install new dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Update .env file**
   ```bash
   # Add new required variables
   OPENAI_API_KEY=your-key
   MCP_ENABLED=true
   MCP_SERVER_PORT=8001
   PLAYWRIGHT_BROWSER=chromium
   PLAYWRIGHT_HEADLESS=true
   ORCHESTRATION_PATTERN=hierarchical
   ```

4. **Update imports** (if using new features)
   ```python
   # Old (still works)
   from legion import LegionCore
   
   # New (for AI features)
   from legion.integration import LegionAISystem
   ```

#### Optional Enhancements

- Enable MCP server for Claude/AI integration
- Configure Playwright for browser automation
- Set up multi-agent orchestration patterns
- Integrate AI script generation

#### Backward Compatibility

✅ All v1.0.0 code continues to work  
✅ No breaking changes to core APIs  
✅ New features are opt-in via configuration

### Breaking Changes

None. Version 2.0.0 is fully backward compatible with v1.0.0.

---

## Release Notes Format

### Types of Changes

- **Added** - new features
- **Changed** - changes in existing functionality
- **Deprecated** - soon-to-be removed features
- **Removed** - removed features
- **Fixed** - bug fixes
- **Security** - vulnerability fixes

### Priority Levels

- 🔴 **CRITICAL** - security fixes, breaking changes
- 🟠 **HIGH** - major features, important fixes
- 🟡 **MEDIUM** - minor features, enhancements
- 🟢 **LOW** - documentation, refactoring

---

[Unreleased]: https://github.com/legion14041981-ui/Legion/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/legion14041981-ui/Legion/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/legion14041981-ui/Legion/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/legion14041981-ui/Legion/releases/tag/v0.1.0
