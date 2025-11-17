# ✅ Live Launch Checklist (Production Go/No-Go)

**Important**: Complete ALL items in this checklist before launching with real money. Each section must be verified and signed off.

---

## Phase 1: Infrastructure Verification (30 minutes before launch)

### ✅ GitHub Actions
- [ ] Workflow file exists and is enabled: `.github/workflows/grail_agent_deploy.yml`
  - Verify cron schedule: `*/5 * * * *` (every 5 minutes)
  - Verify manual trigger available: `workflow_dispatch: true`
- [ ] Last 10 workflow runs show SUCCESS status (>90% success rate acceptable for demo→ >99% for live)
- [ ] Average workflow duration <60 seconds
- [ ] No ERROR messages in recent logs
- [ ] Artifacts are being uploaded successfully

**Verification Date**: ___________  
**Verified By**: ___________

### ✅ Supabase Connection
- [ ] Project is active and accessible: https://supabase.com/dashboard/project/tyrguimbbgfyrrtoluvd
- [ ] All 3 database tables exist with correct schema:
  - [ ] `predictions` table: id, created_at, event_name columns present
  - [ ] `trades` table: proper structure for trade records
  - [ ] `performance_metrics` table: exists and accessible
- [ ] Test data is present in predictions table (from previous runs)
- [ ] API keys are valid and not expired:
  - SUPABASE_URL: `https://tyrguimbbgfyrrtoluvd.supabase.co`
  - SUPABASE_KEY: valid JWT token (Secret masked in GitHub)
- [ ] Row-Level Security (RLS) policies allow inserts from authenticated users

**Verification Date**: ___________  
**Verified By**: ___________

### ✅ GitHub Secrets Configuration
- [ ] Navigate to: https://github.com/legion14041981-ui/Legion/settings/secrets/actions
- [ ] Secret `SUPABASE_URL` is set correctly (not "DISABLED")
- [ ] Secret `SUPABASE_KEY` is set correctly (not "DISABLED")
- [ ] Both secrets are marked as encrypted (green indicator)
- [ ] No test/placeholder values remain

**Verification Date**: ___________  
**Verified By**: ___________

---

## Phase 2: System Stability Testing (1 hour continuous test)

### ✅ Workflow Execution Stability
- [ ] Start timer for 1-hour stability test
- [ ] Monitor GitHub Actions page continuously
- [ ] Verify workflow runs appear every ~5 minutes (allow ±2 minutes variation)
- [ ] Count total runs during test period: Should be ≥11 runs (60 minutes ÷ 5 min interval)
- [ ] All runs show SUCCESS status (no RED failures)
- [ ] Document any runs that took >90 seconds

**Expected**: 11-12 successful runs in 60 minutes

**Actual Runs**: ___________  
**Success Count**: ___________  
**Failure Count**: ___________  

### ✅ Data Ingestion Verification
- [ ] Check Supabase `predictions` table row count before test
- [ ] Record: _________ rows at 13:00
- [ ] After 1 hour, check row count again
- [ ] Record: _________ rows at 14:00
- [ ] Calculate new rows: _________ (should be 11-12 for normal operation)
- [ ] Verify timestamps are recent (within last 5 minutes)
- [ ] Spot-check 3 random rows for data validity

**New Rows Added**: ___________  
**Average Rows Per Run**: ___________

### ✅ Performance Metrics
- [ ] Average workflow duration: ___________  seconds
- [ ] Min duration: ___________  seconds
- [ ] Max duration: ___________  seconds
- [ ] Any timeouts or connection errors? ☐ YES ☐ NO
  - If YES, describe: ___________________________
  - If YES, recommend: ☐ FIX ISSUE ☐ DELAY LAUNCH

**Stability Assessment**: ☐ PASS ☐ FAIL  
**Notes**: _________________________________

---

## Phase 3: Safety Limits Configuration (Production Mode Only)

### ✅ Trading Parameters Review
- [ ] Maximum daily loss limit is set: $_________ (recommended: -$1,000 minimum)
- [ ] Maximum trade size is set: $_________ (recommended: 2-5% of bankroll)
- [ ] Position limits are enforced: _________ concurrent positions max
- [ ] Circuit breaker is configured to auto-pause if:
  - Daily loss exceeds limit? ☐ YES ☐ NO
  - Win rate drops below threshold? ☐ YES ☐ NO
  - Drawdown exceeds limit? ☐ YES ☐ NO

### ✅ Risk Controls Active
- [ ] Slippage limits configured: __________%
- [ ] Correlation filters enabled? ☐ YES ☐ NO
- [ ] Market hours restrictions? ☐ YES (specify: _______) ☐ NO
- [ ] Volatility checks active? ☐ YES ☐ NO
- [ ] Emergency stop procedure has been tested? ☐ YES ☐ NO

**Risk Assessment**: ☐ ACCEPTABLE ☐ NEEDS REVISION  
**Notes**: _________________________________

---

## Phase 4: Monitoring & Alerting Validation

### ✅ Monitoring Infrastructure
- [ ] Monitoring plan has been created: MONITORING_PLAN.md ✓
- [ ] All alert thresholds defined and tested
- [ ] Email notifications are configured and working:
  - [ ] Test email sent to: _______________
  - [ ] Confirmation received? ☐ YES ☐ NO
- [ ] Slack/messaging alerts configured? ☐ YES ☐ NO (if applicable)
- [ ] 24/7 monitoring schedule assigned:
  - Primary monitor: ________________________
  - Backup monitor: ________________________

### ✅ Emergency Response Readiness
- [ ] Emergency Stop procedure has been reviewed: EMERGENCY_STOP.md ✓
- [ ] All team members know how to execute emergency stop
- [ ] Emergency stop has been tested successfully:
  - [ ] Workflow disable test ✓
  - [ ] Secret disable test ✓
  - [ ] Workflow re-enable test ✓
- [ ] Full system recovery time estimate: _________ minutes
- [ ] Contact list updated:
  - Primary contact: _____________ Phone: _____________
  - Secondary contact: _____________ Phone: _____________

**Readiness Assessment**: ☐ READY ☐ NOT READY

---

## Phase 5: Demo Mode → Live Mode Transition

### ✅ Switch From Demo to Live (If Applicable)
- [ ] Demo trading has completed successfully for _______ hours/days
- [ ] Demo performance metrics reviewed: Win rate ___%, P&L $________
- [ ] Bankroll available: $_________ (verified from broker/account)
- [ ] Bankroll is in dedicated live account (NOT mixed with other funds)
- [ ] API keys for live market data are configured
- [ ] Live trading API keys are stored securely and NOT in version control

### ✅ Code Deployment for Live Mode
- [ ] Switch demo=True to demo=False in code if needed
- [ ] Update API endpoints from demo/sandbox to live
- [ ] Commit and push changes to main branch
- [ ] Verify last workflow run uses LIVE configuration

**Go/No-Go Decision**: 
- ☐ PROCEED WITH LIVE LAUNCH
- ☐ DELAY - REQUIRES MORE TESTING (reason: ___________________)
- ☐ ABORT - ISSUES IDENTIFIED (reason: ___________________)

---

## Phase 6: Final Sign-Off

### ✅ Executive Review
- [ ] All previous phases completed and verified
- [ ] No critical issues remain
- [ ] Monitoring team briefed and ready
- [ ] Emergency stop procedure tested and ready
- [ ] Bankroll approved for deployment

### ✅ Launch Authorization

| Role | Name | Signature | Date | Time |
|------|------|-----------|------|------|
| Technical Lead | _____________ | _____ | _____ | _____ |
| Risk Manager | _____________ | _____ | _____ | _____ |
| Operations Lead | _____________ | _____ | _____ | _____ |

### ✅ Launch Configuration
- [ ] All systems in GREEN status (GitHub + Supabase + Monitoring)
- [ ] Confirmed time of launch: _______________ (UTC)
- [ ] First 24-hour monitoring plan activated
- [ ] Escalation contact on-call starting: _______________

---

## Post-Launch Actions (First 24 Hours)

### ✅ Hour 0-1: Initial Deployment
- [ ] Workflow executes successfully with live configuration
- [ ] First live data point appears in database within 5 minutes
- [ ] Monitor logs for any errors or warnings
- [ ] Verify P&L calculations are correct
- [ ] No emergency stop needed? ☐ YES ☐ NO

### ✅ Hour 1-4: Early Monitoring
- [ ] Check system every 30 minutes
- [ ] Verify data is being logged consistently
- [ ] Monitor performance metrics for anomalies
- [ ] No performance degradation? ☐ YES ☐ NO
- [ ] All workflows completing within target duration? ☐ YES ☐ NO

### ✅ Hour 4-24: Continuous Monitoring
- [ ] Check system every 1-2 hours
- [ ] Review any trade activity and profitability
- [ ] Monitor daily P&L against loss limits
- [ ] Document any alerts or issues encountered
- [ ] Assessment: ☐ STABLE ☐ NEEDS ADJUSTMENT ☐ EMERGENCY STOP REQUIRED

### ✅ Post 24-Hour Review
- [ ] Compile full first 24-hour report
- [ ] Success metrics achieved? ☐ YES ☐ PARTIAL ☐ NO
- [ ] Recommendations for next phase:
  1. ______________________________________
  2. ______________________________________
  3. ______________________________________

---

## Appendix: Quick Reference

**Critical URLs**:
- GitHub Actions: https://github.com/legion14041981-ui/Legion/actions
- Supabase Dashboard: https://supabase.com/dashboard/project/tyrguimbbgfyrrtoluvd
- GitHub Secrets: https://github.com/legion14041981-ui/Legion/settings/secrets/actions

**Emergency Contacts**:
- Tech Support: _______________
- Risk Management: _______________
- Executive Approval: _______________

**Key Documents**:
- [Monitoring Plan](MONITORING_PLAN.md)
- [Emergency Stop Procedure](EMERGENCY_STOP.md)
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)

---

**Checklist Version**: 1.0  
**Last Updated**: 2025-11-17  
**Status**: ☐ DRAFT ☐ APPROVED ☐ IN USE  
**Next Review**: After first 24 hours of live operation
