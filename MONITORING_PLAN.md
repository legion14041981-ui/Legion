# 📊 Grail Agent Monitoring Plan

## Overview
This document defines the 24-hour monitoring strategy for the Legion Grail Agent production system running on GitHub Actions with Supabase backend.

## 1. Key Metrics to Monitor

### Workflow Execution Metrics
- **Workflow Run Frequency**: Expected every 5 minutes (cron: `*/5 * * * *`)
- **Workflow Duration**: Target <60 seconds per run
- **Workflow Success Rate**: Target >99% success rate
- **Error Rate**: Track failed runs and categorize by error type

### Data Ingestion Metrics
- **Predictions Logged**: Rows inserted into `predictions` table per hour
- **Trades Executed**: Rows inserted into `trades` table per hour
- **Performance Data**: Rows inserted into `performance_metrics` table per hour
- **Data Freshness**: Latest timestamp in each table vs. current time

### System Health Metrics
- **Supabase Connectivity**: Connection success rate (Target: 100%)
- **API Response Time**: Average response time from Supabase API (<500ms target)
- **Workflow Job Duration**: Breakdown of setup, execution, and upload times
- **Dependency Health**: All Python packages installed successfully

### Business Metrics (Production Mode Only)
- **Trade Volume**: Number of trades executed per day
- **Win Rate**: Percentage of profitable vs. losing trades
- **Daily P&L**: Daily profit/loss in real-money mode
- **Maximum Drawdown**: Peak-to-trough decline during day

## 2. Alert Thresholds

| Metric | Alert Threshold | Severity | Action |
|--------|-----------------|----------|--------|
| Workflow not run in 7 minutes | Red Alert | CRITICAL | Immediate investigation + emergency stop standby |
| Workflow failure rate >5% in 1 hour | Yellow Alert | WARNING | Check logs, monitor closely |
| Supabase connection failure | Red Alert | CRITICAL | Emergency stop, rollback mode |
| Response time >2 seconds | Orange Alert | WARNING | Monitor performance, consider optimization |
| No data logged in 30 minutes | Red Alert | CRITICAL | System failure, manual intervention needed |
| Daily P&L < -$1000 (Production) | Red Alert | CRITICAL | Emergency stop + market investigation |
| Max drawdown >20% (Production) | Orange Alert | WARNING | Review trading strategy parameters |

## 3. Monitoring Tools & Dashboard

### GitHub Actions Monitoring
- **Location**: https://github.com/legion14041981-ui/Legion/actions/workflows/grail_agent_deploy.yml
- **Check**: Every 10 minutes for new workflow runs
- **Logs**: Review last 10 runs for errors and performance trends

### Supabase Monitoring
- **Location**: https://supabase.com/dashboard/project/tyrguimbbgfyrrtoluvd/
- **Tables to Check**: predictions, trades, performance_metrics
- **Query**: View table sizes and row counts every 30 minutes
- **Real-time**: Monitor for connection errors in API logs

### Log Aggregation
- **Artifact Location**: GitHub Actions automatically uploads `grail_agent.log`
- **Log Pattern**: Search for ERROR, WARNING, exception keywords
- **Retention**: Keep last 7 days of logs for trend analysis

## 4. Monitoring Schedule

### Every 5 Minutes (Automated)
- GitHub Actions runs workflow automatically
- Workflow logs are generated and uploaded
- Supabase tables are updated with new data

### Every 30 Minutes (Manual Check)
- Verify latest workflow run status (green checkmark)
- Spot-check Supabase table row counts
- Scan logs for WARNING or ERROR keywords

### Every 1 Hour (Detailed Review)
- Download and review latest `grail_agent.log` artifact
- Calculate metrics: workflow success rate, data ingestion rate
- Verify all 3 database tables have recent entries
- Check for any failed authentication or API errors

### Every 4 Hours (Comprehensive Analysis)
- Full trend analysis of workflow performance
- Review P&L metrics if in production mode
- Analyze data distribution and quality
- Document any anomalies or patterns

### Daily (Complete Report)
- Generate daily summary report
- Aggregate statistics: total runs, success rate, average duration
- Review 24-hour data logs for system stability
- Plan for any maintenance or adjustments needed

## 5. Response Procedures

### For Workflow Failures
1. **Step 1**: Check GitHub Actions logs for specific error message
2. **Step 2**: Verify Supabase credentials are still valid
3. **Step 3**: Check network connectivity to Supabase
4. **Step 4**: If persistent, activate Emergency Stop (see below)

### For Data Ingestion Gaps
1. **Step 1**: Verify Supabase tables exist and have correct schema
2. **Step 2**: Check table row counts - should increase every 5 minutes
3. **Step 3**: Review error logs for INSERT/UPDATE failures
4. **Step 4**: If unresolved >15 minutes, activate Emergency Stop

### For High Latency
1. **Step 1**: Check Supabase project status page
2. **Step 2**: Review API response times in logs
3. **Step 3**: Consider reducing workflow frequency if bottleneck
4. **Step 4**: Contact Supabase support if issue persists

### For Production P&L Issues
1. **Step 1**: Review latest trades and their profitability
2. **Step 2**: Analyze market conditions vs. strategy parameters
3. **Step 3**: Check if trading limits are being respected
4. **Step 4**: Consider pausing trading for manual investigation

## 6. Alerting Channels
- **Primary**: Email notifications (will be configured in GitHub)
- **Secondary**: Slack webhook integration (optional)
- **Tertiary**: Manual dashboard checks every 30 minutes
- **Emergency**: Phone alert for critical failures (configured separately)

## 7. Documentation
- Keep running log of all alerts and responses
- Document root causes for every incident
- Update this plan based on lessons learned
- Archive daily reports for compliance and analysis

---
**Last Updated**: 2025-11-17
**Next Review**: After first 24 hours of production operation
