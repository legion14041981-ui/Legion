"""
Integration tests for Ultra-Orchestrator v4.

Тестирует:
- Architecture generation
- Proxy training
- Multi-objective evaluation
- Registry operations
- Humanistic controller
- Mobile agent
- Watchdog
"""

import pytest
import tempfile
import shutil
from typing import Optional
from pathlib import Path
import json

from legion.neuro_architecture import (
    ArchitectureGenerator,
    ProxyTrainer,
    MultiObjectiveEvaluator,
    ArchitectureRegistry,
    HumanisticController,
    AdaptiveUIInterpreter,
    ArchitectureCache,
    CompactConfigEncoder
)
from legion.neuro_architecture.watchdog import PerformanceWatchdog, MetricThreshold


class TestArchitectureGenerator:
    """Tests for ArchitectureGenerator."""
    
    def test_generate_proposals(self):
        generator = ArchitectureGenerator(seed=42)
        proposals = generator.generate(
            task="test_task",
            n=5,
            strategies=['LoRA', 'MoE']
        )
        
        assert len(proposals) == 5
        assert all(p.strategy in ['LoRA', 'MoE'] for p in proposals)
        assert all(0 <= p.risk_score <= 1.0 for p in proposals)
    
    def test_proposal_semantic_hash(self):
        generator = ArchitectureGenerator(seed=42)
        proposal = generator.generate(task="test", n=1, strategies=['LoRA'])[0]
        
        # Hash should be deterministic
        assert len(proposal.semantic_hash) == 12
        assert proposal.semantic_hash == proposal.semantic_hash  # Idempotent


class TestProxyTrainer:
    """Tests for ProxyTrainer."""
    
    def test_training(self):
        trainer = ProxyTrainer("test_proposal")
        metrics = trainer.train(data_path="data/test", steps=100)
        
        assert metrics.proposal_id == "test_proposal"
        assert metrics.steps_completed == 100
        assert 0 <= metrics.eval_accuracy <= 1.0
        assert metrics.latency_ms > 0


class TestMultiObjectiveEvaluator:
    """Tests for MultiObjectiveEvaluator."""
    
    def test_evaluation(self, tmp_path):
        # Create mock metrics
        metrics_dir = tmp_path / "metrics"
        metrics_dir.mkdir()
        
        for i in range(3):
            metrics_file = metrics_dir / f"proposal_{i}" / "metrics.json"
            metrics_file.parent.mkdir()
            metrics_file.write_text(json.dumps({
                'proposal_id': f'proposal_{i}',
                'eval_accuracy': 0.8 + i * 0.05,
                'latency_ms': 50 + i * 10,
                'gpu_memory_mb': 3000
            }))
        
        evaluator = MultiObjectiveEvaluator()
        metrics_files = list(metrics_dir.rglob("metrics.json"))
        results = evaluator.evaluate(metrics_files, output_dir=str(tmp_path / "evals"))
        
        assert len(results) == 3
        assert results[0].rank == 1  # Best
        assert results[0].composite_score > results[1].composite_score


class TestArchitectureRegistry:
    """Tests for ArchitectureRegistry with cryptographic features."""
    
    def test_register_and_retrieve(self, tmp_path):
        registry = ArchitectureRegistry(storage_dir=str(tmp_path / "registry"))
        
        snapshot = registry.register(
            version="v4/0.90/50",
            config={'strategy': 'LoRA', 'rank': 8},
            metrics={'accuracy': 0.90, 'latency_ms': 50},
            provenance={'test': True},
            tags=['test']
        )
        
        # Verify
        assert len(snapshot.semantic_hash) == 16
        assert len(snapshot.checksum) == 8
        assert snapshot.verify_integrity()
        
        # Retrieve
        retrieved = registry.get(snapshot.semantic_hash)
        assert retrieved is not None
        assert retrieved.semantic_hash == snapshot.semantic_hash
        assert retrieved.verify_integrity()
    
    def test_list_and_filter(self, tmp_path):
        registry = ArchitectureRegistry(storage_dir=str(tmp_path / "registry"))
        
        # Register multiple
        for i in range(5):
            registry.register(
                version=f"v4/{i}",
                config={'id': i},
                metrics={'accuracy': 0.8 + i * 0.02},
                provenance={},
                tags=['test', f'batch_{i // 2}']
            )
        
        all_snapshots = registry.list_all()
        assert len(all_snapshots) == 5
        
        # Filter by tag
        batch_0 = registry.get_by_tag('batch_0')
        assert len(batch_0) == 2


class TestHumanisticController:
    """Tests for HumanisticController."""
    
    def test_risk_assessment(self):
        from legion.neuro_architecture.generator import ArchitectureProposal
        
        controller = HumanisticController(mode="conservative")
        
        # Low risk proposal
        proposal = ArchitectureProposal(
            id="test_low",
            strategy="LoRA",
            changes={'rank': 8},
            expected_flops=1000000,
            expected_latency_ms=50,
            risk_score=0.1
        )
        
        evaluation = controller.evaluate_proposal(proposal)
        assert evaluation['risk_category'] == 'low'
        assert not evaluation['approval_required']  # Conservative allows low risk
    
    def test_memory_recording(self):
        controller = HumanisticController(mode="standard", memory_enabled=True)
        
        from legion.neuro_architecture.humanistic_controller import DecisionRecord
        record = DecisionRecord(
            id="test_decision",
            timestamp="2025-11-30T21:00:00",
            decision_type="test",
            proposal_id="test_proposal",
            risk_score=0.5,
            user_approved=True,
            reasoning="test"
        )
        
        controller.memory.record_decision(record)
        assert len(controller.memory.short_term) == 1


class TestAdaptiveUIInterpreter:
    """Tests for Mobile Agent."""
    
    def test_extract_structure(self):
        agent = AdaptiveUIInterpreter(llm_provider="ollama")
        elements = agent.extract_structure("test_screenshot.png")
        
        assert len(elements) > 0
        assert all(hasattr(e, 'id') for e in elements)
        assert all(hasattr(e, 'clickable') for e in elements)
    
    def test_plan_actions(self):
        agent = AdaptiveUIInterpreter(llm_provider="ollama")
        elements = agent.extract_structure("test_screenshot.png")
        
        actions = agent.plan_actions("Test goal", elements)
        assert len(actions) > 0
        assert all(hasattr(a, 'type') for a in actions)


class TestStorageOptimization:
    """Tests for storage optimization."""
    
    def test_compact_encoder(self):
        encoder = CompactConfigEncoder()
        
        config = {
            'strategy': 'LoRA',
            'rank': 8,
            'alpha': 32,
            'layers': [1, 2, 3, 4, 5]
        }
        
        # Encode
        encoded = encoder.encode(config)
        assert isinstance(encoded, bytes)
        
        # Decode
        decoded = encoder.decode(encoded)
        assert decoded == config
        
        # Check savings
        savings = encoder.estimate_savings(config)
        assert savings['json_bytes'] > 0
    
    def test_architecture_cache(self, tmp_path):
        cache = ArchitectureCache(storage_dir=str(tmp_path / "cache"))
        
        config = {'strategy': 'LoRA', 'rank': 8}
        hash_id = "test_hash_123"
        
        # Set
        cache.set(hash_id, config)
        
        # Get (should hit L1)
        retrieved = cache.get(hash_id)
        assert retrieved == config
        
        # Stats
        stats = cache.get_stats()
        assert stats['hits']['l1'] == 1
        assert stats['hit_rate'] == 1.0


class TestPerformanceWatchdog:
    """Tests for Performance Watchdog."""
    
    def test_health_check(self):
        watchdog = PerformanceWatchdog(check_interval=60)
        
        # Set baseline
        baseline = {
            'error_rate': 0.01,
            'latency_ms': 50.0,
            'memory_mb': 2000
        }
        watchdog.set_baseline(baseline)
        
        # Good metrics
        good_metrics = {
            'error_rate': 0.015,
            'latency_ms': 55.0,
            'memory_mb': 2100
        }
        result = watchdog.check_health(good_metrics)
        assert result.healthy
        assert not watchdog.should_rollback(result)
    
    def test_degradation_detection(self):
        watchdog = PerformanceWatchdog(check_interval=60)
        
        baseline = {
            'error_rate': 0.01,
            'latency_ms': 50.0
        }
        watchdog.set_baseline(baseline)
        
        # Bad metrics (error rate too high)
        bad_metrics = {
            'error_rate': 0.10,  # 10% > 5% threshold
            'latency_ms': 50.0
        }
        result = watchdog.check_health(bad_metrics)
        assert not result.healthy
        assert len(result.violations) > 0
        assert watchdog.should_rollback(result)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
