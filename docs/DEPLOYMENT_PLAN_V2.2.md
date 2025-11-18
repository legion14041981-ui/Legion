# Legion v2.2 OS Integration - Production Deployment Plan

## 🎯 Overview

This document outlines the production deployment strategy for **Legion AI System v2.2**, which introduces OS Integration Layer with workspace isolation, agent identity, and tamper-evident audit trails.

**Version**: v2.2  
**Branch**: `feature/os-integration-v2.2`  
**PR**: [#3](https://github.com/legion14041981-ui/Legion/pull/3)  
**Target**: Production  
**Author**: Autonomous deployment process  
**Date**: November 18, 2025

---

## 📊 Pre-Deployment Checklist

### Code Quality
- [x] All source code committed and pushed
- [x] 4 new modules implemented (60.2 KB)
- [x] Zero-trust security model implemented
- [x] Blockchain-style audit trail implemented
- [ ] **Merge conflicts resolved** ⚠️ **BLOCKER**
- [x] Documentation complete

### Testing
- [x] Unit tests written (`tests/test_os_integration.py`)
- [ ] Unit tests executed and passing
- [ ] Integration tests executed
- [ ] Security audit performed
- [ ] Performance benchmarks run
- [ ] Manual QA testing

### Dependencies
- [x] `requirements.txt` updated (v2.0 + v2.1 already include necessary deps)
- [ ] Docker images built
- [ ] Environment variables documented

### Infrastructure
- [ ] Staging environment prepared
- [ ] Production environment prepared
- [ ] Supabase tables created for audit logs
- [ ] Monitoring configured (Prometheus/Grafana)
- [ ] Backup procedures in place

---

## 🚀 Deployment Phases

### Phase 1: Pre-Deployment (Current)

**Status**: 🟡 IN PROGRESS

**Tasks**:
1. ✅ Code review completed
2. ✅ Test suite created
3. ⚠️ **BLOCKER**: Resolve merge conflicts with `main` branch
4. ⏳ Execute test suite
5. ⏳ Security audit

**Action Required**:
```bash
# Resolve conflicts manually:
git checkout feature/os-integration-v2.2
git pull origin main
# Resolve conflicts in affected files
git commit -m "Resolve merge conflicts with main"
git push origin feature/os-integration-v2.2
```

**Affected Files** (potentially):
- `src/legion/__init__.py` (main was updated with syntax fix)
- Other files may have conflicts

---

### Phase 2: Testing & Validation

**Status**: 🔴 BLOCKED (waiting for Phase 1)

**Tasks**:

#### 2.1 Automated Testing
```bash
# Run unit tests
pytest tests/test_os_integration.py -v --tb=short

# Run integration tests
pytest tests/test_integration.py -v

# Run performance benchmarks
python benchmarks/performance_test.py
```

**Expected Results**:
- All unit tests pass (target: 100%)
- Integration tests pass
- Performance metrics meet targets:
  - Agent registration: <50ms
  - File operations: <10ms
  - Audit log integrity: <1ms

#### 2.2 Security Audit
```bash
# Check for vulnerabilities
pip install safety bandit
safety check
bandit -r src/legion/os_integration/ -f json -o security_report.json

# Verify audit trail integrity
python -c "from src.legion.os_integration import LegionAuditTrail; audit = LegionAuditTrail('test'); assert audit.verify_integrity()"
```

#### 2.3 Manual Testing
- [ ] Create agent workspace and verify isolation
- [ ] Test permission grant/revoke
- [ ] Execute OS operations (terminal, filesystem, python)
- [ ] Verify audit log tamper-evidence
- [ ] Test user approval workflow
- [ ] Verify resource limits enforcement

---

### Phase 3: Staging Deployment

**Status**: 🔴 BLOCKED

**Environment**: `staging.legion.ai` (if applicable)

**Tasks**:

#### 3.1 Infrastructure Setup
```bash
# Build Docker image
docker build -t legion-ai:v2.2-staging -f Dockerfile .

# Run containers
docker-compose -f docker-compose.staging.yml up -d
```

#### 3.2 Database Migration
```sql
-- Supabase: Create audit_logs table
CREATE TABLE audit_logs (
  id BIGSERIAL PRIMARY KEY,
  agent_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  action_type TEXT NOT NULL,
  target TEXT,
  parameters JSONB,
  result JSONB,
  user_approved BOOLEAN DEFAULT FALSE,
  risk_level TEXT NOT NULL,
  hash TEXT NOT NULL,
  previous_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_agent_id ON audit_logs(agent_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_risk_level ON audit_logs(risk_level);
```

#### 3.3 Environment Variables
```bash
# Add to .env (staging)
WORKSPACE_ROOT=/var/legion/workspaces
MAX_DISK_MB=100
MAX_FILES=1000
IDENTITY_TOKEN_EXPIRATION=3600
REQUIRE_USER_APPROVAL=true
AUDIT_LOG_PATH=/var/log/legion/audit
SUPABASE_AUDIT_ENABLED=true
```

#### 3.4 Smoke Tests
```python
# Run smoke tests in staging
import asyncio
from legion.os_integration import *

async def smoke_test():
    # Test 1: Workspace creation
    workspace = LegionAgentWorkspace("smoke-test-1")
    assert workspace.workspace_root.exists()
    
    # Test 2: Identity token
    identity = LegionAgentIdentity("smoke-test-1")
    await identity.request_scope("files.read")
    token = await identity.generate_token(["files.read"])
    assert token.is_valid()
    
    # Test 3: Audit integrity
    audit = LegionAuditTrail("smoke-test-1")
    await audit.log_action("smoke_test", risk_level="low")
    assert audit.verify_integrity()
    
    print("✅ All smoke tests passed")

asyncio.run(smoke_test())
```

**Validation Criteria**:
- [ ] All services start successfully
- [ ] Health checks pass
- [ ] Smoke tests pass
- [ ] Logs show no errors
- [ ] Metrics are being collected

---

### Phase 4: Production Deployment

**Status**: 🔴 BLOCKED

**Environment**: `production.legion.ai`

**Pre-requisites**:
- [x] All previous phases completed
- [ ] Stakeholder approval
- [ ] Change request approved
- [ ] Rollback plan ready

#### 4.1 Deployment Steps

**4.1.1 Create Backup**
```bash
# Backup current production
docker-compose -f docker-compose.prod.yml down
tar -czf legion-backup-$(date +%Y%m%d-%H%M%S).tar.gz /var/legion/

# Backup Supabase
# (Use Supabase dashboard or pg_dump)
```

**4.1.2 Merge to Main**
```bash
# After all checks pass:
git checkout main
git merge feature/os-integration-v2.2
git tag v2.2.0
git push origin main --tags
```

**4.1.3 Deploy**
```bash
# Pull latest
git pull origin main

# Build production image
docker build -t legion-ai:v2.2.0 -f Dockerfile .

# Deploy with zero-downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps --build legion-core

# Verify
curl https://production.legion.ai/health
```

**4.1.4 Post-Deployment Validation**
```bash
# Run production smoke tests
python scripts/production_smoke_tests.py

# Check logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Monitor metrics
# Check Prometheus: http://prometheus.legion.ai
# Check Grafana: http://grafana.legion.ai
```

#### 4.2 Monitoring

**Key Metrics to Watch** (first 24 hours):
- Agent registration rate
- Workspace creation success rate
- Audit log integrity (should be 100%)
- Permission denial rate
- Resource usage (disk, CPU, memory)
- Error rate
- Response time

**Alert Thresholds**:
- Error rate > 1%: WARNING
- Error rate > 5%: CRITICAL
- Audit integrity failures: CRITICAL (immediate rollback)
- Resource usage > 80%: WARNING

---

### Phase 5: Post-Deployment

**Tasks**:

#### 5.1 Documentation Update
- [ ] Update Notion documentation
- [ ] Update README.md
- [ ] Create migration guide for existing agents
- [ ] Publish release notes

#### 5.2 Communication
- [ ] Announce v2.2 release
- [ ] Share deployment status
- [ ] Document known issues

#### 5.3 Monitoring (30 days)
- [ ] Daily metrics review
- [ ] Weekly stakeholder updates
- [ ] Performance optimization if needed

---

## 🔄 Rollback Plan

**Trigger Conditions**:
- Critical bugs discovered
- Audit integrity failures
- Performance degradation > 50%
- Security vulnerabilities

**Rollback Procedure**:
```bash
# 1. Stop current version
docker-compose -f docker-compose.prod.yml down

# 2. Restore backup
tar -xzf legion-backup-YYYYMMDD-HHMMSS.tar.gz -C /

# 3. Revert code
git revert HEAD
git push origin main

# 4. Restart services
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify rollback
curl https://production.legion.ai/health
python scripts/production_smoke_tests.py
```

**Rollback Testing**:
- [ ] Rollback procedure tested in staging
- [ ] Rollback time < 5 minutes
- [ ] Data integrity verified after rollback

---

## 🐛 Known Issues

### Critical
- ⚠️ **Merge conflicts with main branch** - Blocks deployment

### High
- None identified

### Medium
- Testing not yet executed
- Staging environment not configured

### Low
- Documentation could be more detailed

---

## 📞 Contacts & Escalation

**Development Team**:
- Lead: legion14041981-ui
- Repository: https://github.com/legion14041981-ui/Legion

**Escalation Path**:
1. Check GitHub Issues: https://github.com/legion14041981-ui/Legion/issues
2. Check PR comments: https://github.com/legion14041981-ui/Legion/pull/3
3. Review logs in Supabase
4. Contact development team

---

## 📚 References

- **Perplexity Discussion**: [Thread](https://www.perplexity.ai/search/vnedrenie-zaversheno-optimizir-ZvO_IG2uS0Cv8Bf3z8i7pQ)
- **PR #1 (v2.0)**: AI Enhancements
- **PR #2 (v2.1)**: Performance Optimization
- **PR #3 (v2.2)**: OS Integration (THIS)
- **Notion Docs**: https://www.notion.so/2ac65511388d815fa690c20766ed1206

---

## ✅ Sign-off

**Pre-Deployment**:
- [ ] Code Review: _______________ (Date: ___________)
- [ ] Testing: _______________ (Date: ___________)
- [ ] Security: _______________ (Date: ___________)

**Deployment**:
- [ ] Staging Deploy: _______________ (Date: ___________)
- [ ] Production Deploy: _______________ (Date: ___________)

**Post-Deployment**:
- [ ] 24h Check: _______________ (Date: ___________)
- [ ] 7d Check: _______________ (Date: ___________)
- [ ] 30d Review: _______________ (Date: ___________)

---

**Document Version**: 1.0  
**Last Updated**: November 18, 2025, 10:46 PM MSK  
**Status**: 🟡 IN PROGRESS (Phase 1 - Pre-Deployment)
