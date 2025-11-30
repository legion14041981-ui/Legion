"""
Architecture Generator - генератор нейроархитектур.

Реализует NAS-lite подход с эволюционными алгоритмами.
Стратегии: LoRA, MoE, Adapter, Layer Morphism, Sparse Routing.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import random

logger = logging.getLogger(__name__)


@dataclass
class ArchitectureProposal:
    """Proposal архитектуры с метаданными."""
    id: str
    strategy: str
    changes: Dict[str, Any]
    expected_flops: int
    expected_latency_ms: float
    risk_score: float  # 0.0-1.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @property
    def semantic_hash(self) -> str:
        """Generate semantic hash for this architecture."""
        content = f"{self.strategy}:{json.dumps(self.changes, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]


class ArchitectureGenerator:
    """
    Генератор архитектурных вариантов.
    
    Поддерживаемые стратегии:
    - LoRA: Low-Rank Adaptation
    - MoE: Mixture-of-Experts
    - Adapter: Bottleneck adapters
    - SplitLayer: Layer splitting/merging
    - SparseRouting: Conditional computation
    """
    
    STRATEGIES = {
        'LoRA': {
            'rank': [4, 8, 16, 32],
            'alpha': [8, 16, 32, 64],
            'target_modules': [['query', 'value'], ['query', 'key', 'value'], ['all_linear']],
            'dropout': [0.0, 0.05, 0.1]
        },
        'MoE': {
            'num_experts': [2, 4, 8, 16],
            'top_k': [1, 2, 3],
            'expert_capacity': [64, 128, 256],
            'load_balancing': [True, False]
        },
        'Adapter': {
            'bottleneck_size': [16, 32, 64, 128],
            'residual': [True, False],
            'activation': ['relu', 'gelu', 'swish']
        },
        'SplitLayer': {
            'split_ratio': [0.25, 0.5, 0.75],
            'merge_strategy': ['concat', 'add', 'attention']
        },
        'SparseRouting': {
            'sparsity': [0.1, 0.25, 0.5],
            'routing_strategy': ['learned', 'random', 'threshold']
        }
    }
    
    def __init__(self, seed: Optional[int] = None):
        """
        Инициализация генератора.
        
        Args:
            seed: Random seed для воспроизводимости
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        logger.info(f"✅ ArchitectureGenerator initialized (seed={seed})")
    
    def generate(self, task: str, n: int, strategies: List[str]) -> List[ArchitectureProposal]:
        """
        Генерировать N архитектурных proposal'ov.
        
        Args:
            task: Название задачи (напр. 'summarization', 'classification')
            n: Количество предложений
            strategies: Список стратегий для использования
        
        Returns:
            Список ArchitectureProposal
        """
        logger.info(f"💡 Generating {n} proposals for task '{task}' with strategies: {strategies}")
        
        proposals = []
        per_strategy = max(1, n // len(strategies))
        
        for strategy in strategies:
            if strategy not in self.STRATEGIES:
                logger.warning(f"⚠️ Unknown strategy '{strategy}', skipping")
                continue
            
            strategy_proposals = self._generate_strategy(strategy, task, per_strategy)
            proposals.extend(strategy_proposals)
        
        # Если нужно добавить ещё, догенерируем
        while len(proposals) < n:
            strategy = random.choice(strategies)
            if strategy in self.STRATEGIES:
                proposals.extend(self._generate_strategy(strategy, task, 1))
        
        return proposals[:n]
    
    def _generate_strategy(self, strategy: str, task: str, count: int) -> List[ArchitectureProposal]:
        """Генерировать proposals для конкретной стратегии."""
        proposals = []
        config_space = self.STRATEGIES[strategy]
        
        for i in range(count):
            # Случайный выбор конфигурации
            config = {k: random.choice(v) for k, v in config_space.items()}
            
            # Оценка FLOPs и latency (эвристика)
            flops, latency = self._estimate_cost(strategy, config)
            risk = self._estimate_risk(strategy, config)
            
            proposal = ArchitectureProposal(
                id=f"{strategy.lower()}_v{i+1}_{hashlib.md5(json.dumps(config).encode()).hexdigest()[:8]}",
                strategy=strategy,
                changes=config,
                expected_flops=flops,
                expected_latency_ms=latency,
                risk_score=risk,
                metadata={'task': task}
            )
            proposals.append(proposal)
        
        return proposals
    
    def _estimate_cost(self, strategy: str, config: Dict) -> tuple[int, float]:
        """Эвристическая оценка FLOPs и latency."""
        base_flops = 1_000_000_000  # 1 GFLOPs baseline
        base_latency = 50.0  # 50ms baseline
        
        if strategy == 'LoRA':
            rank = config.get('rank', 8)
            flops = base_flops + (rank * 10_000_000)
            latency = base_latency + (rank * 0.1)
        elif strategy == 'MoE':
            num_experts = config.get('num_experts', 4)
            flops = base_flops * num_experts * 0.3  # Only activated experts
            latency = base_latency * 1.2
        elif strategy == 'Adapter':
            bottleneck = config.get('bottleneck_size', 64)
            flops = base_flops + (bottleneck * 100_000)
            latency = base_latency + (bottleneck * 0.01)
        else:
            flops = base_flops
            latency = base_latency
        
        return int(flops), latency
    
    def _estimate_risk(self, strategy: str, config: Dict) -> float:
        """Оценка риска (0.0 = low, 1.0 = high)."""
        risk_map = {
            'LoRA': 0.1,  # Low risk
            'Adapter': 0.2,
            'MoE': 0.5,  # Medium risk
            'SplitLayer': 0.7,
            'SparseRouting': 0.6
        }
        return risk_map.get(strategy, 0.5)
    
    def save_proposals(self, proposals: List[ArchitectureProposal], output_dir: str) -> None:
        """Сохранить proposals в файлы."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for proposal in proposals:
            filepath = os.path.join(output_dir, f"{proposal.id}.json")
            with open(filepath, 'w') as f:
                f.write(proposal.to_json())
        
        logger.info(f"✅ Saved {len(proposals)} proposals to {output_dir}")
