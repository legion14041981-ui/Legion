# Branch Protection Configuration

## Main Branch Protection Rules

This document specifies the required branch protection rules for the Legion repository's main branch to ensure code quality, security, and stability.

## GitHub UI Configuration

### How to Enable Branch Protection

1. Go to Repository → Settings → Branches
2. Under "Branch protection rules", click "Add rule"
3. Enter "main" as the branch name
4. Configure the following settings:

## Required Protection Settings

### 1. Require Pull Request Reviews
- **Enabled**: ✅ YES
- **Require code reviews before merging**: ✅ Checked
- **Number of approving reviews**: 1 (minimum)
- **Dismiss stale pull request approvals**: ✅ Checked
- **Require review from code owners**: ✅ Checked (uses CODEOWNERS file)

### 2. Require Status Checks to Pass
- **Enabled**: ✅ YES
- **Require branches to be up to date**: ✅ Checked
- **Required status checks**:
  - `ci/python-tests` (pytest)
  - `ci/code-quality` (flake8, black, mypy)
  - `ci/security-scan` (CodeQL)

### 3. Additional Protections
- **Require signed commits**: ⚠️ Optional (recommended for production)
- **Require branches to be up to date before merging**: ✅ YES
- **Include administrators**: ✅ YES (enforce rules on admins)
- **Allow force pushes**: ❌ NO
- **Allow deletions**: ❌ NO
- **Allow auto-merge**: ❌ NO (require manual review)

## GitHub API Configuration

### Using GitHub REST API

```bash
curl -X PUT https://api.github.com/repos/legion14041981-ui/Legion/branches/main/protection \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": [
        "ci/python-tests",
        "ci/code-quality",
        "ci/security-scan"
      ]
    },
    "required_pull_request_reviews": {
      "dismiss_stale_reviews": true,
      "require_code_owner_reviews": true,
      "required_approving_review_count": 1
    },
    "enforce_admins": true,
    "allow_force_pushes": false,
    "allow_deletions": false
  }'
```

## Verification

After configuration, verify protection rules are active by:

1. Attempting to push directly to main (should fail)
2. Creating a test branch and PR (should require reviews)
3. Checking branch settings page shows all protections enabled

## Bypass Procedures

### Emergency Override (Use with Caution)

If emergency bypass is required:
1. Contact repository administrator
2. Document the reason for override
3. Re-enable protection immediately after merge
4. Create issue documenting the emergency

## Status

**Current Status**: ⏳ PENDING IMPLEMENTATION
**Priority**: 🔴 CRITICAL
**Estimated Enable Date**: Immediately after this PR

---

*This configuration implements mandatory security requirements from INFRASTRUCTURE_AUDIT_REPORT.md*
