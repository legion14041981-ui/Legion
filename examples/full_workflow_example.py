#!/usr/bin/env python3
"""
Полный пример workflow Ultra-Orchestrator v4.

Демонстрирует:
1. Генерацию архитектур
2. Humanistic Controller с safety gates
3. Proxy training
4. Multi-objective evaluation
5. Cryptographic registry
6. Performance watchdog
7. Canary deployment simulation
"""

import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from legion.neuro_architecture import (
    ArchitectureGenerator,
    ProxyTrainer,
    MultiObjectiveEvaluator,
    ArchitectureRegistry,
    HumanisticController,
    ArchitectureCache
)
from legion.neuro_architecture.watchdog import PerformanceWatchdog

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("🚀 Starting Ultra-Orchestrator v4 Full Workflow Example")
    
    # 1. Initialize components
    logger.info("\n" + "="*60)
    logger.info("INITIALIZATION")
    logger.info("="*60)
    
    controller = HumanisticController(mode="standard", memory_enabled=True)
    generator = ArchitectureGenerator(seed=42)
    registry = ArchitectureRegistry(ipfs_enabled=False)
    watchdog = PerformanceWatchdog(check_interval=60)
    cache = ArchitectureCache()
    
    # 2. Generate proposals
    logger.info("\n" + "="*60)
    logger.info("STEP 1: GENERATE ARCHITECTURE PROPOSALS")
    logger.info("="*60)
    
    proposals = generator.generate(
        task="text_classification",
        n=8,
        strategies=['LoRA', 'MoE', 'Adapter']
    )
    
    logger.info(f"Generated {len(proposals)} proposals")
    for p in proposals[:3]:
        logger.info(f"  - {p.id}: {p.strategy} (risk={p.risk_score:.2f})")
    
    # 3. Evaluate and train
    logger.info("\n" + "="*60)
    logger.info("STEP 2: HUMANISTIC EVALUATION & TRAINING")
    logger.info("="*60)
    
    approved_proposals = []
    for proposal in proposals:
        # Risk assessment
        evaluation = controller.evaluate_proposal(proposal)
        
        logger.info(f"\nProposal: {proposal.id}")
        logger.info(f"  Risk: {evaluation['risk_category']} ({proposal.risk_score:.2f})")
        logger.info(f"  Approval required: {evaluation['approval_required']}")
        logger.info(f"  Recommendation: {evaluation['recommendation']}")
        
        # Auto-approve low risk for demo
        if not evaluation['approval_required']:
            approved_proposals.append(proposal)
            
            # Quick training
            trainer = ProxyTrainer(proposal.id)
            metrics = trainer.train(
                data_path="data/classification/",
                steps=500  # Quick for demo
            )
            
            logger.info(f"  Training completed:")
            logger.info(f"    Accuracy: {metrics.eval_accuracy:.3f}")
            logger.info(f"    Latency: {metrics.latency_ms:.1f}ms")
    
    logger.info(f"\n✅ Approved and trained {len(approved_proposals)} proposals")
    
    # 4. Multi-objective evaluation
    logger.info("\n" + "="*60)
    logger.info("STEP 3: MULTI-OBJECTIVE EVALUATION")
    logger.info("="*60)
    
    from glob import glob
    metrics_files = glob("artifacts/proxy_runs/*/metrics.json")
    
    if metrics_files:
        evaluator = MultiObjectiveEvaluator(weights={
            'accuracy': 0.5,
            'latency': 0.25,
            'cost': 0.15,
            'safety': 0.05,
            'robustness': 0.05
        })
        
        results = evaluator.evaluate(metrics_files)
        
        logger.info(f"\nTop 3 Architectures:")
        for result in results[:3]:
            logger.info(f"  {result.rank}. {result.proposal_id}")
            logger.info(f"     Score: {result.composite_score:.3f}")
            logger.info(f"     Accuracy: {result.accuracy:.3f}")
            logger.info(f"     Latency: {result.latency_ms:.1f}ms")
    
    # 5. Register in cryptographic registry
    logger.info("\n" + "="*60)
    logger.info("STEP 4: CRYPTOGRAPHIC REGISTRY")
    logger.info("="*60)
    
    if metrics_files:
        for i, result in enumerate(results[:3], 1):
            snapshot = registry.register(
                version=f"v4/{result.accuracy:.2f}/{result.latency_ms:.0f}",
                config={'proposal_id': result.proposal_id, 'rank': i},
                metrics={
                    'accuracy': result.accuracy,
                    'latency_ms': result.latency_ms,
                    'cost': result.resource_cost
                },
                provenance={
                    'workflow': 'full_example',
                    'timestamp': 'demo'
                },
                tags=['example', f'rank_{i}', 'production' if i == 1 else 'candidate']
            )
            
            logger.info(f"\nRegistered #{i}:")
            logger.info(f"  Hash: {snapshot.semantic_hash}")
            logger.info(f"  Checksum: {snapshot.checksum}")
            logger.info(f"  Version: {snapshot.version}")
            logger.info(f"  Integrity: {'OK' if snapshot.verify_integrity() else 'FAILED'}")
            
            # Cache for quick access
            cache.set(snapshot.semantic_hash, snapshot.config)
    
    # 6. Performance monitoring
    logger.info("\n" + "="*60)
    logger.info("STEP 5: PERFORMANCE WATCHDOG")
    logger.info("="*60)
    
    # Set baseline
    baseline_metrics = {
        'error_rate': 0.02,
        'latency_ms': 50.0,
        'memory_mb': 2000,
        'cpu_percent': 30.0
    }
    watchdog.set_baseline(baseline_metrics)
    logger.info(f"Baseline set: {baseline_metrics}")
    
    # Simulate monitoring
    scenarios = [
        ('Healthy', {'error_rate': 0.02, 'latency_ms': 52, 'memory_mb': 2100, 'cpu_percent': 32}),
        ('Degraded', {'error_rate': 0.04, 'latency_ms': 65, 'memory_mb': 2500, 'cpu_percent': 45}),
        ('Critical', {'error_rate': 0.08, 'latency_ms': 80, 'memory_mb': 3000, 'cpu_percent': 70})
    ]
    
    for scenario_name, current_metrics in scenarios:
        result = watchdog.check_health(current_metrics)
        
        logger.info(f"\nScenario: {scenario_name}")
        logger.info(f"  Healthy: {result.healthy}")
        logger.info(f"  Violations: {len(result.violations)}")
        for violation in result.violations:
            logger.info(f"    - {violation}")
        logger.info(f"  Recommendation: {result.recommendation}")
        
        if watchdog.should_rollback(result):
            logger.warning("⚠️ ROLLBACK RECOMMENDED")
    
    # 7. Registry stats
    logger.info("\n" + "="*60)
    logger.info("REGISTRY STATISTICS")
    logger.info("="*60)
    
    stats = registry.get_stats()
    logger.info(f"Total snapshots: {stats['total_snapshots']}")
    logger.info(f"Tags: {stats['tags']}")
    logger.info(f"IPFS enabled: {stats['ipfs_enabled']}")
    
    cache_stats = cache.get_stats()
    logger.info(f"\nCache hit rate: {cache_stats['hit_rate']:.1%}")
    logger.info(f"Cache hits: {cache_stats['hits']}")
    logger.info(f"Cache misses: {cache_stats['misses']}")
    
    logger.info("\n" + "="*60)
    logger.info("✅ WORKFLOW COMPLETED SUCCESSFULLY")
    logger.info("="*60)
    logger.info("\nNext steps:")
    logger.info("  1. Review top architectures in artifacts/evals/")
    logger.info("  2. Check registry snapshots in artifacts/architecture_registry/")
    logger.info("  3. Deploy canary: python tools/orchestrator_cli.py deploy --snapshot <hash>")
    logger.info("  4. Monitor with watchdog: python tools/orchestrator_cli.py monitor")


if __name__ == '__main__':
    main()
