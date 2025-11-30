"""
Tests for Ultra-Orchestrator v4.1.0 - Neuro-Learning Loop.

Тестирует:
- Neuro-Learning Loop
- Self-Improver Engine
- Adaptive Refactor Engine
- Enhanced Storage (L4 cache)
- Mobile Agent v4.1
- Watchdog v4.1
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import json
import time

from legion.neuro_architecture import (
    NeuroLearningLoop,
    MetricsSnapshot,
    Issue,
    ImprovementPatch,
    SelfImprover,
    CodeMetrics,
    CodePatch
)

# Import from new v4.1 modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from legion.neuro_architecture.adaptive_refactor_engine import (
    AdaptiveRefactorEngine,
    RefactorProposal
)
from legion.neuro_architecture.storage_v4_1 import (
    L4SemanticCache,
    EnhancedArchitectureCache
)
from legion.neuro_architecture.mobile_agent_v4_1 import (
    EnhancedUIInterpreter,
    ActionPlan,
    PlannedAction
)
from legion.neuro_architecture.watchdog_v4_1 import (
    EnhancedPerformanceWatchdog,
    WatchdogAlert
)


class TestNeuroLearningLoop:
    """Tests for Neuro-Learning Loop."""
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test metrics collection."""
        loop = NeuroLearningLoop(cycle_interval_hours=1)
        
        metrics = await loop._collect_metrics()
        
        assert isinstance(metrics, MetricsSnapshot)
        assert 0 <= metrics.error_rate <= 1.0
        assert metrics.latency_p50 > 0
        assert metrics.cache_hit_rate >= 0
    
    @pytest.mark.asyncio
    async def test_issue_analysis(self):
        """Test issue analysis."""
        loop = NeuroLearningLoop(cycle_interval_hours=1)
        
        # High error rate
        metrics = MetricsSnapshot(
            timestamp="2025-11-30T23:00:00Z",
            error_rate=0.10,  # High
            latency_p50=50.0,
            latency_p95=100.0,
            latency_p99=150.0,
            memory_mb=2000.0,
            cpu_percent=30.0,
            cache_hit_rate=0.80,
            agent_stability=0.95,
            mobile_agent_success=0.70,  # Low
            watchdog_alerts=2
        )
        
        issues = await loop._analyze_issues(metrics)
        
        assert len(issues) > 0
        assert any(i.category == 'stability' for i in issues)
    
    @pytest.mark.asyncio
    async def test_patch_generation(self):
        """Test patch generation."""
        loop = NeuroLearningLoop(cycle_interval_hours=1)
        
        issues = [
            Issue(
                id="issue_test",
                severity='medium',
                category='performance',
                description="Cache hit rate low",
                affected_component='storage',
                metrics={'cache_hit_rate': 0.70},
                detected_at="2025-11-30T23:00:00Z"
            )
        ]
        
        patches = await loop._generate_patches(issues)
        
        assert len(patches) > 0
        assert patches[0].target_component == 'storage'


class TestSelfImprover:
    """Tests for Self-Improver Engine."""
    
    def test_code_analysis(self, tmp_path):
        """Test code analysis."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def complex_function():
    if True:
        if True:
            if True:
                if True:
                    pass
""")
        
        improver = SelfImprover(src_dir=str(tmp_path))
        metrics = improver._analyze_file(test_file)
        
        assert isinstance(metrics, CodeMetrics)
        assert metrics.cyclomatic_complexity > 1
    
    def test_patch_generation(self, tmp_path):
        """Test patch generation."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        improver = SelfImprover(src_dir=str(tmp_path), min_quality_score=90.0)
        
        metrics = {str(test_file): improver._analyze_file(test_file)}
        patches = improver.generate_patches(metrics)
        
        # Should generate patches for low quality
        assert isinstance(patches, list)


class TestAdaptiveRefactorEngine:
    """Tests for Adaptive Refactor Engine."""
    
    def test_refactor_analysis(self, tmp_path):
        """Test refactoring analysis."""
        # Create test file without type hints
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def function_without_types(x, y):
    return x + y
""")
        
        engine = AdaptiveRefactorEngine(src_dir=str(tmp_path))
        proposals = engine._analyze_file(test_file)
        
        # Should detect missing type hints
        assert len(proposals) > 0
        assert any(p.refactor_type == 'document' for p in proposals)


class TestL4SemanticCache:
    """Tests for L4 Semantic Cache."""
    
    def test_exact_match(self):
        """Test exact key match."""
        cache = L4SemanticCache(max_size=100)
        
        cache.set("test_key", "test_value")
        value = cache.get("test_key")
        
        assert value == "test_value"
    
    def test_semantic_search(self):
        """Test semantic similarity search."""
        cache = L4SemanticCache(max_size=100, similarity_threshold=0.80)
        
        # Store with embedding
        cache.set("key1", "value1", embedding=[1.0, 0.5, 0.2])
        
        # Search with similar embedding
        similar = cache.get("key2", query_embedding=[0.9, 0.5, 0.3])
        
        # Should find similar entry
        assert similar == "value1"
    
    def test_cleanup_stale(self):
        """Test stale entry cleanup."""
        cache = L4SemanticCache(max_size=100)
        
        # Add old entry
        cache.set("old_key", "old_value")
        cache.cache["old_key"].accessed_at = time.time() - (25 * 3600)  # 25 hours ago
        
        # Add fresh entry
        cache.set("new_key", "new_value")
        
        # Cleanup
        removed = cache.cleanup_stale(max_age_hours=24.0)
        
        assert removed == 1
        assert "new_key" in cache.cache
        assert "old_key" not in cache.cache


class TestEnhancedUIInterpreter:
    """Tests for Enhanced Mobile Agent v4.1."""
    
    def test_multi_step_planning(self):
        """Test multi-step action planning."""
        interpreter = EnhancedUIInterpreter(lookahead_depth=3)
        
        plan = interpreter.plan_actions_multi_step(
            goal="Open settings",
            ui_elements=[]
        )
        
        assert isinstance(plan, ActionPlan)
        assert len(plan.steps) == 3  # lookahead_depth
        assert all(isinstance(s, PlannedAction) for s in plan.steps)
    
    def test_adaptive_retry(self):
        """Test adaptive retry logic."""
        interpreter = EnhancedUIInterpreter(max_retries=5)
        
        # Create simple plan
        plan = ActionPlan(
            goal="Test",
            steps=[PlannedAction(
                type='click',
                target='button',
                params={},
                expected_outcome='clicked',
                success_probability=0.7
            )],
            confidence=0.8
        )
        
        result = interpreter.execute_with_adaptive_retry(plan)
        
        assert 'success' in result
        assert 'completed_steps' in result


class TestEnhancedWatchdog:
    """Tests for Enhanced Watchdog v4.1."""
    
    def test_comprehensive_health_check(self):
        """Test comprehensive health check (20 criteria)."""
        watchdog = EnhancedPerformanceWatchdog()
        
        # Good metrics
        metrics = {
            'error_rate': 0.02,
            'latency_p50': 50.0,
            'latency_p95': 90.0,
            'latency_p99': 140.0,
            'memory_usage_pct': 0.60,
            'cpu_percent': 40.0,
            'cache_hit_rate': 0.85,
            'storage_efficiency': 0.75,
            'agent_stability': 0.95,
            'mobile_agent_success': 0.85,
            'registry_checksum_fail': False,
            'deadlock_duration_sec': 0,
            'infinite_loop_iterations': 0,
            'memory_leak_mb_per_hour': 0,
            'contradictory_decisions': 0,
            'safety_gate_bypasses': 0,
            'containment_violations': 0,
            'unauthorized_actions': 0,
            'self_improvement_failure_rate': 0.05,
            'patch_rollback_rate': 0.10,
            'neuro_loop_last_run_hours_ago': 6
        }
        
        result = watchdog.check_health_comprehensive(metrics)
        
        assert result['healthy'] == True
        assert result['summary']['critical'] == 0
    
    def test_critical_alert_detection(self):
        """Test critical alert detection."""
        watchdog = EnhancedPerformanceWatchdog()
        
        # Critical: safety bypass
        metrics = {
            'safety_gate_bypasses': 1,
            'error_rate': 0.02,
            'cache_hit_rate': 0.85
        }
        
        result = watchdog.check_health_comprehensive(metrics)
        
        assert result['healthy'] == False
        assert result['summary']['critical'] > 0
        assert result['should_rollback'] == True
    
    def test_improver_task_creation(self):
        """Test Self-Improver task creation."""
        watchdog = EnhancedPerformanceWatchdog()
        
        # Warning: low cache hit rate
        metrics = {
            'cache_hit_rate': 0.70,  # Below warning threshold
            'error_rate': 0.02
        }
        
        result = watchdog.check_health_comprehensive(metrics)
        tasks = watchdog.create_improver_tasks()
        
        assert len(tasks) > 0
        assert tasks[0]['type'] == 'improvement'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
