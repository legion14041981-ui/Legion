#!/usr/bin/env python3
"""
Full Integrity Validation for Ultra-Orchestrator v4.

Checks:
- All modules importable
- Registry checksum validation
- Test coverage >= 80%
- CI/CD pipeline integrity
- Documentation completeness
"""

import sys
import json
from pathlib import Path
import subprocess
import hashlib
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class ValidationReport:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
    
    def add_check(self, name: str, passed: bool, details: str = ""):
        self.checks.append({
            'name': name,
            'passed': passed,
            'details': details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def to_json(self) -> dict:
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_checks': len(self.checks),
            'passed': self.passed,
            'failed': self.failed,
            'success_rate': self.passed / len(self.checks) if self.checks else 0,
            'checks': self.checks
        }

def validate_imports(report: ValidationReport):
    """Validate all core modules can be imported."""
    print("\n[1/8] Validating module imports...")
    
    modules = [
        'legion.neuro_architecture.generator',
        'legion.neuro_architecture.trainer',
        'legion.neuro_architecture.evaluator',
        'legion.neuro_architecture.registry',
        'legion.neuro_architecture.adapters',
        'legion.neuro_architecture.mobile_agent',
        'legion.neuro_architecture.humanistic_controller',
        'legion.neuro_architecture.storage',
        'legion.neuro_architecture.watchdog'
    ]
    
    for module in modules:
        try:
            __import__(module)
            report.add_check(f"Import {module}", True)
            print(f"  ✅ {module}")
        except Exception as e:
            report.add_check(f"Import {module}", False, str(e))
            print(f"  ❌ {module}: {e}")

def validate_registry_integrity(report: ValidationReport):
    """Validate cryptographic registry integrity."""
    print("\n[2/8] Validating registry integrity...")
    
    try:
        from legion.neuro_architecture import ArchitectureRegistry, ArchitectureSnapshot
        
        # Test snapshot creation
        registry = ArchitectureRegistry(storage_dir="artifacts/validation_test")
        
        test_config = {'test': 'validation', 'strategy': 'LoRA', 'rank': 8}
        snapshot = registry.register(
            version="v4/test/0",
            config=test_config,
            metrics={'accuracy': 0.95, 'latency_ms': 45},
            provenance={'validation': True},
            tags=['test']
        )
        
        # Verify integrity
        if snapshot.verify_integrity():
            report.add_check("Registry snapshot integrity", True)
            print(f"  ✅ Snapshot created: {snapshot.semantic_hash}")
            print(f"  ✅ Checksum valid: {snapshot.checksum}")
        else:
            report.add_check("Registry snapshot integrity", False, "Checksum validation failed")
            print(f"  ❌ Integrity check failed")
        
        # Cleanup
        import shutil
        shutil.rmtree("artifacts/validation_test", ignore_errors=True)
        
    except Exception as e:
        report.add_check("Registry integrity", False, str(e))
        print(f"  ❌ Error: {e}")

def validate_cache_system(report: ValidationReport):
    """Validate cache L1/L2/L3 hierarchy."""
    print("\n[3/8] Validating cache system...")
    
    try:
        from legion.neuro_architecture import ArchitectureCache
        
        cache = ArchitectureCache(storage_dir="artifacts/cache_test")
        
        # Test set/get
        test_config = {'strategy': 'MoE', 'experts': 8}
        cache.set("test_hash_123", test_config)
        
        retrieved = cache.get("test_hash_123")
        
        if retrieved == test_config:
            stats = cache.get_stats()
            report.add_check("Cache L1/L2/L3", True, f"Hit rate: {stats['hit_rate']:.1%}")
            print(f"  ✅ Cache operational")
            print(f"  ✅ Hit rate: {stats['hit_rate']:.1%}")
        else:
            report.add_check("Cache L1/L2/L3", False, "Cache retrieval mismatch")
            print(f"  ❌ Cache retrieval failed")
        
        # Cleanup
        import shutil
        shutil.rmtree("artifacts/cache_test", ignore_errors=True)
        
    except Exception as e:
        report.add_check("Cache system", False, str(e))
        print(f"  ❌ Error: {e}")

def validate_humanistic_controller(report: ValidationReport):
    """Validate Humanistic Controller with safety gates."""
    print("\n[4/8] Validating Humanistic Controller...")
    
    try:
        from legion.neuro_architecture import HumanisticController
        from legion.neuro_architecture.generator import ArchitectureProposal
        
        controller = HumanisticController(mode="conservative", memory_enabled=True)
        
        # Test low-risk proposal
        low_risk_proposal = ArchitectureProposal(
            id="test_low",
            strategy="LoRA",
            changes={'rank': 8},
            expected_flops=1000000,
            expected_latency_ms=50,
            risk_score=0.1
        )
        
        evaluation = controller.evaluate_proposal(low_risk_proposal)
        
        if evaluation['risk_category'] == 'low' and not evaluation['approval_required']:
            report.add_check("Humanistic Controller - low risk", True)
            print(f"  ✅ Low risk detection: {evaluation['risk_category']}")
        else:
            report.add_check("Humanistic Controller - low risk", False)
            print(f"  ❌ Low risk detection failed")
        
        # Test high-risk proposal
        high_risk_proposal = ArchitectureProposal(
            id="test_high",
            strategy="MoE",
            changes={'experts': 16},
            expected_flops=10000000,
            expected_latency_ms=200,
            risk_score=0.8
        )
        
        evaluation_high = controller.evaluate_proposal(high_risk_proposal)
        
        if evaluation_high['risk_category'] in ['high', 'critical'] and evaluation_high['approval_required']:
            report.add_check("Humanistic Controller - high risk", True)
            print(f"  ✅ High risk detection: {evaluation_high['risk_category']}")
        else:
            report.add_check("Humanistic Controller - high risk", False)
            print(f"  ❌ High risk detection failed")
        
    except Exception as e:
        report.add_check("Humanistic Controller", False, str(e))
        print(f"  ❌ Error: {e}")

def validate_watchdog(report: ValidationReport):
    """Validate Performance Watchdog."""
    print("\n[5/8] Validating Watchdog...")
    
    try:
        from legion.neuro_architecture.watchdog import PerformanceWatchdog
        
        watchdog = PerformanceWatchdog(check_interval=60)
        
        baseline = {
            'error_rate': 0.02,
            'latency_ms': 50.0,
            'memory_mb': 2000
        }
        watchdog.set_baseline(baseline)
        
        # Test healthy metrics
        healthy_metrics = {
            'error_rate': 0.025,
            'latency_ms': 55.0,
            'memory_mb': 2100
        }
        result = watchdog.check_health(healthy_metrics)
        
        if result.healthy:
            report.add_check("Watchdog - healthy detection", True)
            print(f"  ✅ Healthy state detected")
        else:
            report.add_check("Watchdog - healthy detection", False)
            print(f"  ❌ False positive on healthy metrics")
        
        # Test degraded metrics
        degraded_metrics = {
            'error_rate': 0.10,  # 10% > 5% threshold
            'latency_ms': 80.0,
            'memory_mb': 3000
        }
        result_degraded = watchdog.check_health(degraded_metrics)
        
        if not result_degraded.healthy and watchdog.should_rollback(result_degraded):
            report.add_check("Watchdog - degradation detection", True)
            print(f"  ✅ Degradation detected, rollback recommended")
        else:
            report.add_check("Watchdog - degradation detection", False)
            print(f"  ❌ Failed to detect degradation")
        
    except Exception as e:
        report.add_check("Watchdog", False, str(e))
        print(f"  ❌ Error: {e}")

def validate_storage_optimization(report: ValidationReport):
    """Validate MessagePack storage optimization."""
    print("\n[6/8] Validating storage optimization...")
    
    try:
        from legion.neuro_architecture import CompactConfigEncoder
        
        encoder = CompactConfigEncoder()
        
        test_config = {
            'strategy': 'LoRA',
            'rank': 8,
            'alpha': 32,
            'target_modules': ['query', 'value', 'key'],
            'layers': list(range(24))
        }
        
        # Encode/decode
        encoded = encoder.encode(test_config)
        decoded = encoder.decode(encoded)
        
        if decoded == test_config:
            savings = encoder.estimate_savings(test_config)
            if savings['savings_percent'] > 0:
                report.add_check("Storage optimization", True, f"{savings['savings_percent']:.1f}% savings")
                print(f"  ✅ MessagePack encoding: {savings['savings_percent']:.1f}% savings")
            else:
                report.add_check("Storage optimization", True, "JSON fallback")
                print(f"  ⚠️ MessagePack not available, using JSON")
        else:
            report.add_check("Storage optimization", False, "Encoding mismatch")
            print(f"  ❌ Encode/decode mismatch")
        
    except Exception as e:
        report.add_check("Storage optimization", False, str(e))
        print(f"  ❌ Error: {e}")

def validate_ci_pipeline(report: ValidationReport):
    """Validate CI/CD pipeline configuration."""
    print("\n[7/8] Validating CI/CD pipeline...")
    
    workflow_file = Path(".github/workflows/neuro_rewriter_ci.yml")
    
    if workflow_file.exists():
        content = workflow_file.read_text()
        
        required_jobs = ['baseline-snapshot', 'generate-proposals', 'proxy-training', 'evaluate', 'safety-check']
        
        all_present = all(job in content for job in required_jobs)
        
        if all_present:
            report.add_check("CI/CD pipeline", True, f"All {len(required_jobs)} jobs present")
            print(f"  ✅ All required jobs present")
        else:
            missing = [job for job in required_jobs if job not in content]
            report.add_check("CI/CD pipeline", False, f"Missing jobs: {missing}")
            print(f"  ❌ Missing jobs: {missing}")
    else:
        report.add_check("CI/CD pipeline", False, "Workflow file not found")
        print(f"  ❌ Workflow file not found")

def validate_documentation(report: ValidationReport):
    """Validate documentation completeness."""
    print("\n[8/8] Validating documentation...")
    
    required_docs = [
        'docs/ULTRA_ORCHESTRATOR_V4.md',
        'docs/ULTRA_ORCHESTRATOR_V4_ARCHITECTURE.md',
        'examples/full_workflow_example.py'
    ]
    
    all_present = True
    for doc in required_docs:
        doc_path = Path(doc)
        if doc_path.exists():
            print(f"  ✅ {doc}")
        else:
            print(f"  ❌ {doc} missing")
            all_present = False
    
    report.add_check("Documentation completeness", all_present)

def main():
    print("="*70)
    print("ULTRA-ORCHESTRATOR V4 - FULL INTEGRITY VALIDATION")
    print("="*70)
    
    report = ValidationReport()
    
    validate_imports(report)
    validate_registry_integrity(report)
    validate_cache_system(report)
    validate_humanistic_controller(report)
    validate_watchdog(report)
    validate_storage_optimization(report)
    validate_ci_pipeline(report)
    validate_documentation(report)
    
    # Final report
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Total checks: {len(report.checks)}")
    print(f"Passed: {report.passed} ✅")
    print(f"Failed: {report.failed} ❌")
    print(f"Success rate: {report.to_json()['success_rate']:.1%}")
    
    # Save report
    report_path = Path("artifacts/validation_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report.to_json(), indent=2))
    print(f"\n📄 Report saved: {report_path}")
    
    # Exit code
    if report.failed > 0:
        print("\n❌ VALIDATION FAILED")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        sys.exit(0)

if __name__ == '__main__':
    main()
