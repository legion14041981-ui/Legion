#!/usr/bin/env python3
"""Generate security summary from multiple scan reports."""

import json
from pathlib import Path
from typing import Dict, List, Any


def load_json_report(filepath: str) -> Dict[str, Any]:
    """Load JSON report if it exists."""
    path = Path(filepath)
    if not path.exists():
        return {}
    
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def summarize_pip_audit(report: Dict) -> Dict[str, Any]:
    """Summarize pip-audit results."""
    if not report:
        return {'status': 'not_run', 'vulnerabilities': 0}
    
    vulns = report.get('vulnerabilities', [])
    return {
        'status': 'clean' if not vulns else 'issues_found',
        'vulnerabilities': len(vulns),
        'critical': sum(1 for v in vulns if v.get('severity') == 'critical'),
        'high': sum(1 for v in vulns if v.get('severity') == 'high')
    }


def summarize_bandit(report: Dict) -> Dict[str, Any]:
    """Summarize bandit results."""
    if not report:
        return {'status': 'not_run', 'issues': 0}
    
    results = report.get('results', [])
    return {
        'status': 'clean' if not results else 'issues_found',
        'issues': len(results),
        'high': sum(1 for r in results if r.get('issue_severity') == 'HIGH'),
        'medium': sum(1 for r in results if r.get('issue_severity') == 'MEDIUM')
    }


def main():
    """Generate comprehensive security summary."""
    print("="*80)
    print("🔒 SECURITY SCAN SUMMARY")
    print("="*80)
    
    # Load reports
    pip_audit = load_json_report('pip-audit-report.json')
    safety = load_json_report('safety-report.json')
    bandit = load_json_report('bandit-report.json')
    semgrep = load_json_report('semgrep-report.json')
    
    # Summarize each tool
    pip_audit_summary = summarize_pip_audit(pip_audit)
    bandit_summary = summarize_bandit(bandit)
    
    print(f"\n📦 pip-audit: {pip_audit_summary['status']}")
    if pip_audit_summary['vulnerabilities'] > 0:
        print(f"   Vulnerabilities: {pip_audit_summary['vulnerabilities']}")
        print(f"   Critical: {pip_audit_summary.get('critical', 0)}")
        print(f"   High: {pip_audit_summary.get('high', 0)}")
    
    print(f"\n🔍 Bandit: {bandit_summary['status']}")
    if bandit_summary['issues'] > 0:
        print(f"   Issues: {bandit_summary['issues']}")
        print(f"   High: {bandit_summary.get('high', 0)}")
        print(f"   Medium: {bandit_summary.get('medium', 0)}")
    
    total_issues = (
        pip_audit_summary['vulnerabilities'] +
        bandit_summary['issues']
    )
    
    print("\n" + "="*80)
    if total_issues == 0:
        print("✅ No security issues detected")
    else:
        print(f"⚠️  {total_issues} security issue(s) detected")
        print("   Review the detailed reports for more information")
    
    return 0 if total_issues == 0 else 1


if __name__ == '__main__':
    exit(main())
