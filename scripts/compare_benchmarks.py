#!/usr/bin/env python3
"""Compare benchmark results to detect performance regressions."""

import json
import sys
from pathlib import Path
from typing import Dict, Any


def load_benchmark(filepath: str) -> Dict[str, Any]:
    """Load benchmark results from JSON file."""
    path = Path(filepath)
    if not path.exists():
        return {}
    
    with open(path) as f:
        return json.load(f)


def compare_metrics(baseline: Dict, current: Dict, threshold: float = 0.15) -> bool:
    """Compare metrics and detect regressions.
    
    Args:
        baseline: Baseline benchmark results
        current: Current benchmark results
        threshold: Maximum acceptable degradation (15% by default)
    
    Returns:
        True if no regressions detected, False otherwise
    """
    if not baseline:
        print("⚠️  No baseline found, saving current as baseline")
        return True
    
    regressions = []
    improvements = []
    
    metrics_to_check = [
        ('throughput', 'higher_is_better'),
        ('latency_p50', 'lower_is_better'),
        ('latency_p95', 'lower_is_better'),
        ('latency_p99', 'lower_is_better'),
        ('error_rate', 'lower_is_better')
    ]
    
    print("\n" + "="*80)
    print("📊 BENCHMARK COMPARISON")
    print("="*80)
    
    for metric, direction in metrics_to_check:
        baseline_val = baseline.get(metric, 0)
        current_val = current.get(metric, 0)
        
        if baseline_val == 0:
            continue
            
        change_pct = ((current_val - baseline_val) / baseline_val) * 100
        
        if direction == 'higher_is_better':
            if change_pct < -threshold * 100:
                regressions.append((metric, change_pct))
                status = '🔴 REGRESSION'
            elif change_pct > threshold * 100:
                improvements.append((metric, change_pct))
                status = '🟢 IMPROVEMENT'
            else:
                status = '⚪ STABLE'
        else:  # lower_is_better
            if change_pct > threshold * 100:
                regressions.append((metric, change_pct))
                status = '🔴 REGRESSION'
            elif change_pct < -threshold * 100:
                improvements.append((metric, change_pct))
                status = '🟢 IMPROVEMENT'
            else:
                status = '⚪ STABLE'
        
        print(f"\n{metric:20} {status}")
        print(f"  Baseline: {baseline_val:.2f}")
        print(f"  Current:  {current_val:.2f}")
        print(f"  Change:   {change_pct:+.2f}%")
    
    print("\n" + "="*80)
    
    if regressions:
        print(f"\n❌ {len(regressions)} performance regression(s) detected:")
        for metric, change in regressions:
            print(f"   • {metric}: {change:+.2f}%")
        print("\n⚠️  Consider investigating before merging.")
        return False
    
    if improvements:
        print(f"\n✅ {len(improvements)} performance improvement(s):")
        for metric, change in improvements:
            print(f"   • {metric}: {change:+.2f}%")
    
    if not regressions and not improvements:
        print("\n✅ Performance is stable (within ±15% threshold)")
    
    return True


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: compare_benchmarks.py <baseline.json> <current.json>")
        sys.exit(1)
    
    baseline_file = sys.argv[1]
    current_file = sys.argv[2]
    
    baseline = load_benchmark(baseline_file)
    current = load_benchmark(current_file)
    
    success = compare_metrics(baseline, current)
    sys.exit(0 if success else 1)
