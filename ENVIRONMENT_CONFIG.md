# 🔧 Environment Configuration Guide

## Overview
This document describes all environment variables required for the Grail Agent production deployment on GitHub Actions with Supabase backend.

## Critical Environment Variables

### Supabase Configuration (REQUIRED)

#### SUPABASE_URL
- **Description**: Base URL for your Supabase project
- **Type**: String (URL)
- **Example**: `https://tyrguimbbgfyrrtoluvd.supabase.co`
- **Source**: Supabase Dashboard → Project Settings → API Keys
- **Location**: GitHub Secret (Repository → Settings → Secrets → Actions)
- **Rotation**: Every 90 days or after security audit
- **Risk Level**: HIGH - Controls database access

#### SUPABASE_KEY
- **Description**: Anonymous JWT token for API authentication
- **Type**: String (JWT Token)
- **Example**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- **Source**: Supabase Dashboard → Project Settings → API Keys (anon key)
- **Location**: GitHub Secret (Repository → Settings → Secrets → Actions)
- **Rotation**: Every 30 days minimum, immediately if compromised
- **Risk Level**: CRITICAL - Controls write access to database
- **Security**: Never commit to version control, always use GitHub Secrets

## Optional Environment Variables

### Trading Mode Configuration

#### DEMO_MODE
- **Description**: Switch between demo (virtual) and live (real money) trading
- **Type**: Boolean
- **Allowed Values**: `true` (demo) or `false` (live)
- **Default**: `true` (safe default)
- **Usage**: Set to `false` only after successful 24-hour demo testing
- **Location**: Embedded in code or .env file (NOT in GitHub Secrets)

#### TRADING_BANKROLL
- **Description**: Virtual or real bankroll amount for trading
- **Type**: Float (USD)
- **Example**: `10000` (for $10,000)
- **Default**: `1000` (for demo mode)
- **Usage**: Set based on available capital
- **Location**: Code configuration or .env file

### Market Data API Keys (Future)

#### MARKET_DATA_API_KEY
- **Description**: API key for market data provider (e.g., Alpha Vantage, IEX Cloud)
- **Type**: String
- **Example**: `demo` (for demo mode), `pk_live...` (for production)
- **Location**: GitHub Secret (once market data integration added)
- **Rotation**: Every 60 days or per provider policy
- **Risk Level**: MEDIUM - Controls external data access

### Monitoring and Alerting (Future)

#### SLACK_WEBHOOK_URL
- **Description**: Slack webhook for critical alerts
- **Type**: String (URL)
- **Format**: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`
- **Location**: GitHub Secret (when alerts are configured)
- **Rotation**: Every 90 days, immediately if leaked
- **Risk Level**: HIGH - Controls external notification channel

#### PAGERDUTY_KEY
- **Description**: PagerDuty integration key for on-call escalation
- **Type**: String
- **Location**: GitHub Secret (when incident management is needed)
- **Risk Level**: HIGH - Controls incident response

#### SENDGRID_API_KEY (or email provider equivalent)
- **Description**: Email service API key for alert notifications
- **Type**: String
- **Location**: GitHub Secret (when email alerts are configured)
- **Risk Level**: HIGH - Controls email delivery

## Configuration by Environment

### Demo Mode (Safe for Testing)

```
SUPABASE_URL=https://tyrguimbbgfyrrtoluvd.supabase.co
SUPABASE_KEY=eyJ... (anon key for demo project)
DEMO_MODE=true
TRADING_BANKROLL=1000
```

**Purpose**: Test workflow execution, data logging, and monitoring without real money risk
**Duration**: Minimum 24 hours before production launch
**Verification**: All data is logged to `predictions`, `trades`, and `performance_metrics` tables

### Production Mode (Real Money)

```
SUPABASE_URL=https://tyrguimbbgfyrrtoluvd.supabase.co (same project)
SUPABASE_KEY=eyJ... (same anon key - now in production use!)
DEMO_MODE=false
TRADING_BANKROLL=50000 (or your actual bankroll)
MARKET_DATA_API_KEY=pk_live... (production market data key)
```

**Purpose**: Execute real trades with actual market data
**Prerequisites**:
- ✅ Demo mode testing completed successfully
- ✅ LAUNCH_CHECKLIST.md all items verified
- ✅ Monitoring infrastructure active
- ✅ Emergency stop procedure tested
- ✅ Risk controls in place (daily loss limits, etc.)

## Setting Environment Variables

### Method 1: GitHub Secrets (Recommended for Sensitive Data)

For secrets like `SUPABASE_KEY`:

1. Navigate to: Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `SUPABASE_KEY`
4. Value: `eyJ...` (paste the JWT token)
5. Click "Add secret"
6. In workflow YAML, access via: `${{ secrets.SUPABASE_KEY }}`

**Advantages**:
- Encrypted at rest in GitHub
- Masked in logs and UI
- Audit trail of access
- Can be rotated without code changes

### Method 2: .env File (For Local Development Only)

For local testing (not committed to version control):

1. Create `.env` file in repository root
2. Add variables: 
   ```
   SUPABASE_URL=https://tyrguimbbgfyrrtoluvd.supabase.co
   SUPABASE_KEY=eyJ...
   DEMO_MODE=true
   ```
3. Load in Python: `python-dotenv` package
4. **NEVER** commit `.env` to version control
5. **ALWAYS** add `.env` to `.gitignore`

**Verify .gitignore includes**:
```
.env
.env.local
.env.*.local
```

### Method 3: Inline in Workflow (NOT Recommended)

In `.github/workflows/grail_agent_deploy.yml`:

```yaml
- name: Run Grail Agent
  env:
    SUPABASE_URL: https://tyrguimbbgfyrrtoluvd.supabase.co
    SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}  # Use secrets, never inline!
  run: python grail_agent_production.py
```

**⚠️ WARNING**: Never hardcode sensitive values directly in workflow files

## Validation Checklist

Before deploying, verify:

- [ ] All REQUIRED variables are set
- [ ] No sensitive data is in version control
- [ ] GitHub Secrets are properly configured
- [ ] SUPABASE_URL points to correct project
- [ ] SUPABASE_KEY is valid JWT token (not expired)
- [ ] Secrets are marked as masked in GitHub logs
- [ ] Demo mode testing completed (if using live keys)
- [ ] Rotation schedule documented for each secret

## Rotation Schedule

| Variable | Frequency | Reason | Process |
|----------|-----------|--------|---------|
| SUPABASE_KEY | 30 days | Security best practice | Regenerate in Supabase, update GitHub secret |
| SUPABASE_URL | 90 days | Audit trail | Update if project URL changes |
| MARKET_DATA_API_KEY | 60 days | Vendor policy | Rotate with provider, update secret |
| SLACK_WEBHOOK_URL | 90 days | Security | Regenerate in Slack, update secret |

## Emergency Procedures

### If SUPABASE_KEY is Compromised

1. **Immediate** (within 5 minutes):
   - Activate Emergency Stop (see EMERGENCY_STOP.md)
   - Set `SUPABASE_KEY` to `DISABLED` in GitHub Secrets

2. **Within 15 minutes**:
   - Go to Supabase Dashboard
   - Project Settings → API Keys
   - Regenerate new anon key
   - Copy new key value

3. **Within 30 minutes**:
   - Update GitHub Secret `SUPABASE_KEY` with new value
   - Test workflow executes successfully with new key
   - Re-enable workflow if emergency stopped

4. **Within 2 hours**:
   - Audit Supabase logs for unauthorized access
   - Review GitHub Actions logs for compromised key usage
   - Document incident and remediation steps

### If GitHub Secrets are Accessible by Unauthorized User

1. Rotate all secrets immediately
2. Review GitHub Actions audit log
3. Revoke any API keys that were exposed
4. Update 2FA and access controls
5. File security incident report

## Troubleshooting

### "Authentication failed" errors in logs
- [ ] Verify SUPABASE_KEY is valid JWT token (not malformed)
- [ ] Check SUPABASE_KEY hasn't expired (see Supabase project settings)
- [ ] Confirm SUPABASE_URL is correct (matches project)
- [ ] Verify GitHub Secrets are properly masked and encrypted

### "Connection refused" to Supabase
- [ ] Check Supabase project is active (not paused)
- [ ] Verify network connectivity from GitHub Actions runner
- [ ] Check if Supabase is under maintenance
- [ ] Review Supabase status page

### Workflow runs but no data is logged
- [ ] Verify database table permissions (RLS policies)
- [ ] Check SUPABASE_KEY has INSERT permissions
- [ ] Confirm workflow has `SUPABASE_URL` and `SUPABASE_KEY` set
- [ ] Review application logs for INSERT statement errors

## Environment Variable Template (.env.example)

```
# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://[YOUR-PROJECT-ID].supabase.co
SUPABASE_KEY=eyJ... (copy from Supabase dashboard)

# Trading Configuration
DEMO_MODE=true
TRADING_BANKROLL=1000

# Optional: Market Data
# MARKET_DATA_API_KEY=pk_...

# Optional: Alerting
# SLACK_WEBHOOK_URL=https://hooks.slack.com/...
# SENDGRID_API_KEY=SG.xxx...
```

## Security Best Practices

1. **Never commit secrets** to version control
   - Use `.gitignore` to exclude `.env` files
   - Use GitHub Secrets for CI/CD environment variables

2. **Rotate secrets regularly**
   - Set rotation calendar reminders
   - Maintain audit trail of rotations
   - Use strong random key generation

3. **Principle of least privilege**
   - SUPABASE_KEY should have only INSERT/SELECT permissions
   - Avoid using admin keys in production workflows

4. **Monitor secret usage**
   - Review GitHub Actions logs regularly
   - Set up alerts for unusual API activity
   - Monitor Supabase project for unauthorized access

5. **Protect GitHub Secrets**
   - Enable 2FA for GitHub account
   - Limit who can modify repository secrets
   - Use branch protection rules

---
**Last Updated**: 2025-11-17
**Version**: 1.0
**Next Review**: Before moving to production mode
