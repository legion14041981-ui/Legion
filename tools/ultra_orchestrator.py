#!/usr/bin/env python3
"""
Ultra-Orchestrator v4 CLI - командный интерфейс.

Использование:
    python tools/ultra_orchestrator.py generate --task summarization --n 10
    python tools/ultra_orchestrator.py train --proposal lora_v1_abc123 --steps 2000
    python tools/ultra_orchestrator.py evaluate --runs artifacts/proxy_runs/*
    python tools/ultra_orchestrator.py integrate --top 3
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from legion.neuro_architecture import (
    ArchitectureGenerator,
    ProxyTrainer,
    MultiObjectiveEvaluator,
    ArchitectureRegistry
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_generate(args):
    """Генерировать архитектурные proposals."""
    generator = ArchitectureGenerator(seed=args.seed)
    strategies = args.strategies.split(',')
    
    proposals = generator.generate(
        task=args.task,
        n=args.n,
        strategies=strategies
    )
    
    # Сохранить proposals
    output_dir = args.output or "orchestrator/proposals"
    generator.save_proposals(proposals, output_dir)
    
    logger.info(f"✅ Generated {len(proposals)} proposals")
    for p in proposals[:3]:
        logger.info(f"  - {p.id}: {p.strategy} (risk={p.risk_score:.2f})")


def cmd_train(args):
    """Запустить proxy training."""
    trainer = ProxyTrainer(args.proposal)
    
    metrics = trainer.train(
        data_path=args.data,
        steps=args.steps,
        output_dir=args.output or "artifacts/proxy_runs"
    )
    
    logger.info(f"✅ Training completed for {args.proposal}")
    logger.info(f"  Accuracy: {metrics.eval_accuracy:.3f}")
    logger.info(f"  Latency: {metrics.latency_ms:.1f}ms")


def cmd_evaluate(args):
    """Оценить архитектуры."""
    from glob import glob
    
    # Найти все metrics.json
    metrics_files = []
    for pattern in args.runs:
        metrics_files.extend(glob(f"{pattern}/metrics.json"))
    
    if not metrics_files:
        logger.error("❌ No metrics files found")
        return
    
    # Parse weights
    weights = {}
    if args.weights:
        for pair in args.weights.split(','):
            key, value = pair.split(':')
            weights[key.strip()] = float(value.strip())
    
    evaluator = MultiObjectiveEvaluator(weights or None)
    results = evaluator.evaluate(
        metrics_files=metrics_files,
        output_dir=args.output or "artifacts/evals"
    )
    
    logger.info(f"✅ Evaluated {len(results)} architectures")
    logger.info("\nTop 3:")
    for r in results[:3]:
        logger.info(f"  {r.rank}. {r.proposal_id}: score={r.composite_score:.3f}")


def cmd_integrate(args):
    """Интегрировать лучшие архитектуры."""
    import json
    from pathlib import Path
    
    # Читать evaluation results
    eval_dir = Path(args.eval_dir or "artifacts/evals")
    summary_file = eval_dir / "evaluation_summary.json"
    
    if not summary_file.exists():
        logger.error(f"❌ Summary file not found: {summary_file}")
        return
    
    with open(summary_file, 'r') as f:
        summary = json.load(f)
    
    top_k = summary['top_3'][:args.top]
    
    logger.info(f"🔧 Integrating top {args.top} architectures:")
    for i, arch in enumerate(top_k, 1):
        logger.info(f"  {i}. {arch['proposal_id']} (score={arch['composite_score']:.3f})")
    
    # TODO: Реальная интеграция: применить patches, создать PR
    logger.info("⚠️ Integration not yet implemented - use manual process")


def main():
    parser = argparse.ArgumentParser(
        description='Ultra-Orchestrator v4 - Neuro-Rewriter CLI'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate architecture proposals')
    gen_parser.add_argument('--task', required=True, help='Task name (e.g., summarization)')
    gen_parser.add_argument('--n', type=int, default=10, help='Number of proposals')
    gen_parser.add_argument('--strategies', default='LoRA,MoE,Adapter', help='Comma-separated strategies')
    gen_parser.add_argument('--seed', type=int, help='Random seed')
    gen_parser.add_argument('--output', help='Output directory')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Run proxy training')
    train_parser.add_argument('--proposal', required=True, help='Proposal ID')
    train_parser.add_argument('--data', required=True, help='Data directory')
    train_parser.add_argument('--steps', type=int, default=2000, help='Training steps')
    train_parser.add_argument('--output', help='Output directory')
    
    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate architectures')
    eval_parser.add_argument('--runs', nargs='+', required=True, help='Proxy run directories')
    eval_parser.add_argument('--weights', help='Weights (e.g., accuracy:0.5,latency:0.2)')
    eval_parser.add_argument('--output', help='Output directory')
    
    # Integrate command
    int_parser = subparsers.add_parser('integrate', help='Integrate best architectures')
    int_parser.add_argument('--top', type=int, default=3, help='Number of top architectures')
    int_parser.add_argument('--eval-dir', help='Evaluation directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        'generate': cmd_generate,
        'train': cmd_train,
        'evaluate': cmd_evaluate,
        'integrate': cmd_integrate
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()
