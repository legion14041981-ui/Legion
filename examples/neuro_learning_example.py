#!/usr/bin/env python3
"""
Пример использования Neuro-Learning Loop v4.1.0.

Демонстрирует:
- Запуск цикла самообучения
- Сбор метрик
- Анализ проблем
- Генерация и применение патчей
- Self-improvement
"""

import sys
from pathlib import Path
import logging
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from legion.neuro_architecture import (
    NeuroLearningLoop,
    SelfImprover,
    AdaptiveRefactorEngine
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("🧬 Neuro-Learning Loop v4.1.0 - Example")
    logger.info("="*60)
    
    # 1. Initialize components
    logger.info("\n[1] Initializing components...")
    
    neuro_loop = NeuroLearningLoop(
        cycle_interval_hours=1,  # 1 hour for demo (normally 12-24h)
        enable_auto_apply=True
    )
    
    self_improver = SelfImprover(
        src_dir="src/legion",
        min_quality_score=60.0
    )
    
    refactor_engine = AdaptiveRefactorEngine(
        src_dir="src/legion",
        preserve_compatibility=True
    )
    
    # 2. Analyze codebase
    logger.info("\n[2] Analyzing codebase...")
    
    code_metrics = self_improver.analyze_codebase()
    logger.info(f"   Analyzed {len(code_metrics)} files")
    
    refactor_proposals = refactor_engine.analyze_codebase()
    logger.info(f"   Found {len(refactor_proposals)} refactoring opportunities")
    
    # 3. Generate patches
    logger.info("\n[3] Generating improvement patches...")
    
    patches = self_improver.generate_patches(code_metrics)
    logger.info(f"   Generated {len(patches)} patches")
    
    # 4. Run one cycle (demo)
    logger.info("\n[4] Running one Neuro-Learning cycle (demo)...")
    logger.info("   (In production, this runs continuously every 12-24h)")
    
    # Collect metrics
    metrics = await neuro_loop._collect_metrics()
    logger.info(f"   Current metrics:")
    logger.info(f"     Error rate: {metrics.error_rate:.2%}")
    logger.info(f"     Latency p95: {metrics.latency_p95:.1f}ms")
    logger.info(f"     Cache hit rate: {metrics.cache_hit_rate:.1%}")
    logger.info(f"     Mobile agent success: {metrics.mobile_agent_success:.1%}")
    
    # Analyze issues
    issues = await neuro_loop._analyze_issues(metrics)
    logger.info(f"\n   Detected {len(issues)} issues:")
    for issue in issues:
        logger.info(f"     - [{issue.severity.upper()}] {issue.description}")
    
    # Generate patches for issues
    if issues:
        issue_patches = await neuro_loop._generate_patches(issues)
        logger.info(f"\n   Generated {len(issue_patches)} patches for issues")
        
        for patch in issue_patches:
            logger.info(f"     - {patch.patch_type} for {patch.target_component}")
            logger.info(f"       Expected improvement: {patch.expected_improvement}")
            logger.info(f"       Risk score: {patch.risk_score:.2f}")
    
    # 5. Summary
    logger.info("\n" + "="*60)
    logger.info("✅ DEMO COMPLETE")
    logger.info("="*60)
    logger.info("\nNext steps for production:")
    logger.info("  1. Run neuro_loop.run() for continuous improvement")
    logger.info("  2. Monitor artifacts/neuro_learning/ for results")
    logger.info("  3. Review patches before auto-apply")
    logger.info("  4. Track metrics improvements over time")
    logger.info("\nTo start continuous loop:")
    logger.info("  await neuro_loop.run()  # Runs indefinitely")


if __name__ == '__main__':
    asyncio.run(main())
