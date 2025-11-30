#!/usr/bin/env python3
"""
Ultra-Orchestrator v4 CLI - полный командный интерфейс.

Использование:
    # Full workflow
    python tools/orchestrator_cli.py workflow --task classification --n 10
    
    # Individual commands
    python tools/orchestrator_cli.py generate --task summarization --n 10
    python tools/orchestrator_cli.py train --proposal lora_v1_abc123
    python tools/orchestrator_cli.py evaluate --runs artifacts/proxy_runs/*
    python tools/orchestrator_cli.py deploy --snapshot abc123 --canary 5
    
    # Mobile agent
    python tools/orchestrator_cli.py mobile --goal "Open settings, enable dark mode"
    
    # Registry management
    python tools/orchestrator_cli.py registry list
    python tools/orchestrator_cli.py registry get abc123
    python tools/orchestrator_cli.py registry restore abc123
"""

import sys
import argparse
import logging
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from legion.neuro_architecture import (
    ArchitectureGenerator,
    ProxyTrainer,
    MultiObjectiveEvaluator,
    ArchitectureRegistry,
    HumanisticController,
    AdaptiveUIInterpreter,
    ArchitectureCache,
    PerformanceWatchdog
)
from legion.neuro_architecture.watchdog import PerformanceWatchdog

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_workflow(args):
    """Полный workflow: generate → train → evaluate → deploy."""
    logger.info("🚀 Starting full Ultra-Orchestrator v4 workflow")
    logger.info(f"   Task: {args.task}")
    logger.info(f"   Proposals: {args.n}")
    logger.info(f"   Mode: {args.mode}")
    
    # 1. Initialize controller
    controller = HumanisticController(mode=args.mode, memory_enabled=True)
    registry = ArchitectureRegistry(ipfs_enabled=args.ipfs)
    
    # 2. Generate proposals
    logger.info("\n" + "="*60)
    logger.info("STEP 1: GENERATE ARCHITECTURE PROPOSALS")
    logger.info("="*60)
    
    generator = ArchitectureGenerator(seed=args.seed)
    strategies = args.strategies.split(',') if args.strategies else ['LoRA', 'MoE', 'Adapter']
    proposals = generator.generate(
        task=args.task,
        n=args.n,
        strategies=strategies
    )
    
    # 3. Evaluate and train
    logger.info("\n" + "="*60)
    logger.info("STEP 2: PROXY TRAINING & EVALUATION")
    logger.info("="*60)
    
    approved_proposals = []
    for proposal in proposals:
        evaluation = controller.evaluate_proposal(proposal)
        
        if evaluation['approval_required'] and not args.auto_approve:
            approved = controller.request_approval(proposal, evaluation)
            if not approved:
                continue
        
        approved_proposals.append(proposal)
        
        # Train
        trainer = ProxyTrainer(proposal.id)
        metrics = trainer.train(
            data_path=args.data or "data/ci_test/",
            steps=args.steps
        )
    
    # 4. Multi-objective evaluation
    logger.info("\n" + "="*60)
    logger.info("STEP 3: MULTI-OBJECTIVE EVALUATION")
    logger.info("="*60)
    
    from glob import glob
    metrics_files = glob("artifacts/proxy_runs/*/metrics.json")
    
    evaluator = MultiObjectiveEvaluator()
    results = evaluator.evaluate(metrics_files=metrics_files)
    
    # 5. Register top-K
    logger.info("\n" + "="*60)
    logger.info("STEP 4: REGISTER TOP ARCHITECTURES")
    logger.info("="*60)
    
    top_k = results[:args.top_k]
    for i, result in enumerate(top_k, 1):
        snapshot = registry.register(
            version=f"v4/{result.accuracy:.2f}/{result.latency_ms:.0f}",
            config={'proposal_id': result.proposal_id},
            metrics={
                'accuracy': result.accuracy,
                'latency_ms': result.latency_ms,
                'cost': result.resource_cost
            },
            provenance={
                'task': args.task,
                'workflow': 'full',
                'rank': i
            },
            tags=['workflow', f'rank_{i}']
        )
        logger.info(f"   Registered: {snapshot.semantic_hash}")
    
    # 6. Deploy (if requested)
    if args.deploy:
        logger.info("\n" + "="*60)
        logger.info("STEP 5: CANARY DEPLOYMENT")
        logger.info("="*60)
        
        top_snapshot = registry.get(top_k[0].proposal_id)
        logger.info(f"Deploying top architecture: {top_snapshot.semantic_hash}")
        # TODO: Real deployment
    
    logger.info("\n" + "="*60)
    logger.info("✅ WORKFLOW COMPLETED SUCCESSFULLY")
    logger.info("="*60)


def cmd_mobile(args):
    """Запустить mobile agent."""
    logger.info(f"📱 Starting Mobile Agent")
    logger.info(f"   Goal: {args.goal}")
    
    agent = AdaptiveUIInterpreter(llm_provider="ollama", model="llama3")
    
    # Extract UI
    elements = agent.extract_structure(args.screenshot or "screenshot.png")
    logger.info(f"   Found {len(elements)} UI elements")
    
    # Plan actions
    actions = agent.plan_actions(args.goal, elements)
    logger.info(f"   Planned {len(actions)} actions")
    
    # Execute
    result = agent.execute_with_healing(actions, max_retries=3)
    
    if result['success']:
        logger.info("✅ Goal achieved successfully")
    else:
        logger.error(f"❌ Goal failed: {result['error']}")


def cmd_registry(args):
    """Управление registry."""
    registry = ArchitectureRegistry(ipfs_enabled=args.ipfs)
    
    if args.action == 'list':
        snapshots = registry.list_all(verify_integrity=True)
        logger.info(f"\n📚 Found {len(snapshots)} snapshots:")
        for snapshot in snapshots:
            logger.info(f"\n  {snapshot.semantic_hash}")
            logger.info(f"    Version: {snapshot.version}")
            logger.info(f"    Metrics: {snapshot.metrics}")
            logger.info(f"    Tags: {snapshot.tags}")
    
    elif args.action == 'get':
        snapshot = registry.get(args.hash)
        if snapshot:
            print(json.dumps(snapshot.to_dict(), indent=2))
        else:
            logger.error(f"❌ Snapshot {args.hash} not found")
    
    elif args.action == 'restore':
        config = registry.restore_snapshot(args.hash)
        if config:
            logger.info("✅ Snapshot restored successfully")
            print(json.dumps(config, indent=2))
        else:
            logger.error(f"❌ Restore failed")
    
    elif args.action == 'stats':
        stats = registry.get_stats()
        logger.info("\n📊 Registry Statistics:")
        logger.info(f"  Total snapshots: {stats['total_snapshots']}")
        logger.info(f"  Tags: {stats['tags']}")
        logger.info(f"  IPFS enabled: {stats['ipfs_enabled']}")


def main():
    parser = argparse.ArgumentParser(
        description='Ultra-Orchestrator v4 CLI - Complete workflow automation'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Workflow command (full pipeline)
    workflow_parser = subparsers.add_parser('workflow', help='Run full workflow')
    workflow_parser.add_argument('--task', required=True, help='Task name')
    workflow_parser.add_argument('--n', type=int, default=10, help='Number of proposals')
    workflow_parser.add_argument('--strategies', help='Comma-separated strategies')
    workflow_parser.add_argument('--mode', default='standard', choices=['conservative', 'standard', 'aggressive'])
    workflow_parser.add_argument('--steps', type=int, default=2000, help='Training steps')
    workflow_parser.add_argument('--data', help='Data directory')
    workflow_parser.add_argument('--top-k', type=int, default=3, help='Top K architectures')
    workflow_parser.add_argument('--seed', type=int, help='Random seed')
    workflow_parser.add_argument('--auto-approve', action='store_true', help='Auto-approve all')
    workflow_parser.add_argument('--deploy', action='store_true', help='Deploy after evaluation')
    workflow_parser.add_argument('--ipfs', action='store_true', help='Enable IPFS')
    
    # Mobile agent command
    mobile_parser = subparsers.add_parser('mobile', help='Run mobile agent')
    mobile_parser.add_argument('--goal', required=True, help='Goal description')
    mobile_parser.add_argument('--screenshot', help='Screenshot path')
    
    # Registry command
    registry_parser = subparsers.add_parser('registry', help='Manage registry')
    registry_parser.add_argument('action', choices=['list', 'get', 'restore', 'stats'])
    registry_parser.add_argument('--hash', help='Snapshot hash')
    registry_parser.add_argument('--ipfs', action='store_true', help='Enable IPFS')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        'workflow': cmd_workflow,
        'mobile': cmd_mobile,
        'registry': cmd_registry
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()
