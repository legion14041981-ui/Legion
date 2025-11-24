# 🛑 Emergency Stop Procedure

## Purpose
This document provides detailed instructions for immediately halting the Grail Agent system in case of critical failures, security breaches, or uncontrolled trading losses.

**Time-Sensitive**: This procedure must be executable in <5 minutes to minimize risk.

## Quick Stop (Immediate Action)

### Phase 1: Disable Workflow (30 seconds)
1. **Navigate to GitHub Actions Settings**
   - URL: https://github.com/legion14041981-ui/Legion/settings/actions
   - Or: Repository → Settings → Actions → General

2. **Disable the Workflow**
   - Find "Grail Agent Auto-Deploy" workflow in the list
   - Click the three-dot menu (⋯)
   - Select "Disable workflow"
   - Confirm the action

**Result**: Workflow will stop executing on its 5-minute schedule. Already-running executions will complete but no new runs will start.

### Phase 2: Kill In-Flight Executions (1 minute)
1. **Stop Current Workflow Runs**
   - URL: https://github.com/legion14041981-ui/Legion/actions/workflows/grail_agent_deploy.yml
   - Look for any runs with status "In progress"

2. **Cancel Each Running Job**
   - Click on the run that's in progress
   - Click "Cancel workflow run" button
   - Confirm cancellation
   - Repeat for any other running workflows

**Result**: All active workflow jobs will be terminated immediately.

### Phase 3: Disable Secrets (2 minutes)
To ensure the system cannot automatically restart with valid credentials:

1. **Navigate to Secrets Settings**
   - URL: https://github.com/legion14041981-ui/Legion/settings/secrets/actions
   - Or: Repository → Settings → Secrets and variables → Actions

2. **Deactivate Critical Secrets**
   - Delete or temporarily set to invalid value:
     - `SUPABASE_URL`: Set to `DISABLED`
     - `SUPABASE_KEY`: Set to `DISABLED`
   - This prevents any workflow from authenticating with Supabase

**Result**: Even if workflow runs, it cannot connect to database or execute trades.

## Advanced Stop (Database Level)

### Phase 4: Stop Supabase Ingestion (Optional but Recommended)
If you need to prevent any database writes:

1. **Navigate to Supabase Project**
   - URL: https://supabase.com/dashboard/project/tyrguimbbgfyrrtoluvd
   - Or: Supabase Dashboard → Your Project

2. **Disable Row-Level Security (RLS)**
   - Go to Table Editor → Select `trades` table
   - Click menu (⋯) → Edit
   - Disable insert/update permissions temporarily
   - Repeat for `predictions` and `performance_metrics` tables

**Alternative: Disable Table Access**
   - Go to SQL Editor
   - Execute: `REVOKE INSERT ON public.trades FROM authenticated;`
   - Execute: `REVOKE INSERT ON public.predictions FROM authenticated;`
   - Execute: `REVOKE INSERT ON public.performance_metrics FROM authenticated;`

**Result**: No new data can be written to database even if system connects.

### Phase 5: Revoke API Keys (Maximum Security)
For production emergencies where complete lockdown is needed:

1. **Rotate Supabase API Keys**
   - Supabase Dashboard → Project Settings → API Keys
   - Click the key icon next to `anon` key
   - Generate new key
   - Update GitHub secret `SUPABASE_KEY` with new value (or set to DISABLED)

**Result**: Old API key becomes invalid, preventing any connections with compromised credentials.

## Rollback Procedures

### Reactivating After Brief Emergency Stop (for testing or brief pauses)

1. **Restore Secrets**
   - GitHub → Settings → Secrets → Actions
   - Restore SUPABASE_URL: `https://tyrguimbbgfyrrtoluvd.supabase.co`
   - Restore SUPABASE_KEY: `<your-valid-anon-key>`

2. **Re-enable Workflow**
   - GitHub → Actions → Workflows → Grail Agent Auto-Deploy
   - Click menu (⋯) → Enable

3. **Verify Operation**
   - Manually trigger workflow via "Run workflow" button
   - Wait for execution (should take ~30-60 seconds)
   - Verify new entry in `predictions` table

### Complete System Reset (After Major Incident)

If you need to completely reset the system:

1. **Delete All Data (WARNING: IRREVERSIBLE)**
   - Supabase → Table Editor
   - For each table (predictions, trades, performance_metrics):
     - Right-click → Truncate/Clear
     - Or use SQL: `DELETE FROM public.predictions;`

2. **Reset API Keys**
   - Generate new Supabase keys in Project Settings
   - Update all GitHub secrets

3. **Clear GitHub History**
   - GitHub Actions → Click on workflow run
   - Delete artifact logs if needed (optional)

4. **Redeploy Workflow**
   - Re-enable workflow
   - Verify first run completes successfully

## Emergency Contact & Escalation

| Severity | Action | Timeline |
|----------|--------|----------|
| Workflow Failure | Review logs, attempt restart | 5 minutes |
| Supabase Connection Error | Disable secrets, check status | 2 minutes |
| Uncontrolled Trading Loss | FULL EMERGENCY STOP (Phase 1-5) | <5 minutes |
| Security Breach | Revoke all keys, full reset | <2 minutes |
| System Unavailable >15min | Escalate to Supabase support + vendor | Immediate |

## Testing the Emergency Stop

**Schedule**: Test this procedure monthly or after any production incidents.

1. **Controlled Test Steps**
   - Deploy test workflow to development branch
   - Trigger Phase 1-2 (disable and cancel)
   - Verify workflow doesn't run
   - Re-enable and verify it starts again

2. **Time Measurement**
   - Record time from "start" to each phase completion
   - Goal: <5 minutes from alert to full stop
   - Document any delays or issues

3. **Failure Scenarios to Test**
   - Workflow stuck in running state
   - Secrets corrupted
   - Supabase connection hanging
   - GitHub UI unresponsive (use API/CLI as backup)

## Monitoring After Emergency Stop

After activating emergency stop, monitor:
- **No new workflow runs** (should be 0 runs for 10+ minutes)
- **No new table entries** in Supabase (predictions, trades, metrics should freeze)
- **No errors in logs** (should stabilize after current run finishes)
- **Database connections drop** to zero

## Prevention Measures

To avoid needing emergency stop:

1. **Monitor Continuously** (see MONITORING_PLAN.md)
2. **Set Trading Limits** (max daily loss, max trade size)
3. **Use Circuit Breakers** (auto-pause if P&L < threshold)
4. **Test Regularly** (monthly emergency stop drills)
5. **Maintain Alerts** (email/Slack for critical failures)

---
**Last Updated**: 2025-11-17
**Test Status**: Ready for production
**Time to Full Stop**: <5 minutes (measured)
