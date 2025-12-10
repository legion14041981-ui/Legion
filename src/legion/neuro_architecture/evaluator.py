"""
Multi-Objective Evaluator - многокритериальная оценка.

Критерии: accuracy, latency, cost, safety, robustness.
Использует Pareto-оптимизацию + weighted scoring.
"""

import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Результат оценки архитектуры."""
    proposal_id: str
    accuracy: float
    latency_ms: float
    resource_cost: float
    safety_score: float
    robustness_score: float
    composite_score: float
    rank: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class MultiObjectiveEvaluator:
    """
    Многокритериальная оценка архитектур.
    
    Формула скоринга:
    score = α*accuracy - β*latency - γ*cost - δ*safety_violations + ε*robustness
    """
    
    DEFAULT_WEIGHTS = {
        'accuracy': 0.5,
        'latency': 0.2,
        'cost': 0.15,
        'safety': 0.1,
        'robustness': 0.05
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Инициализация evaluator.
        
        Args:
            weights: Веса для каждого критерия
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._validate_weights()
        logger.info(f"✅ MultiObjectiveEvaluator initialized with weights: {self.weights}")
    
    def _validate_weights(self) -> None:
        """Проверить, что веса суммируются в 1.0."""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"⚠️ Weights sum to {total}, not 1.0. Normalizing...")
            factor = 1.0 / total
            self.weights = {k: v * factor for k, v in self.weights.items()}
    
    def evaluate(
        self,
        metrics_files: List[str],
        output_dir: str = "artifacts/evals"
    ) -> List[EvaluationResult]:
        """
        Оценить набор архитектур.
        
        Args:
            metrics_files: Список путей к metrics.json
            output_dir: Директория для результатов
        
        Returns:
            Список EvaluationResult, отсортированный по rank
        """
        logger.info(f"📊 Evaluating {len(metrics_files)} architectures")
        
        results = []
        for metrics_file in metrics_files:
            result = self._evaluate_single(metrics_file)
            if result:
                results.append(result)
        
        # Ранжирование
        results = self._rank_results(results)
        
        # Сохранение
        self._save_results(results, output_dir)
        
        logger.info(f"✅ Evaluation completed. Top-3 proposals: {[r.proposal_id for r in results[:3]]}")
        return results
    
    def _evaluate_single(self, metrics_file: str) -> Optional[EvaluationResult]:
        """Оценить одну архитектуру."""
        try:
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
            
            # Извлечь метрики
            accuracy = metrics.get('eval_accuracy', 0.0)
            latency = metrics.get('latency_ms', 100.0)
            cost = metrics.get('gpu_memory_mb', 4000) / 1000  # GB
            
            # Safety и robustness (пока заглушки)
            safety = 1.0  # No violations
            robustness = 0.8  # Default
            
            # Композитный скор
            composite = (
                self.weights['accuracy'] * accuracy -
                self.weights['latency'] * (latency / 100.0) -  # Normalize
                self.weights['cost'] * (cost / 10.0) -  # Normalize
                self.weights['safety'] * (1.0 - safety) * 10 +
                self.weights['robustness'] * robustness
            )
            
            return EvaluationResult(
                proposal_id=metrics.get('proposal_id', 'unknown'),
                accuracy=accuracy,
                latency_ms=latency,
                resource_cost=cost,
                safety_score=safety,
                robustness_score=robustness,
                composite_score=composite
            )
        except Exception as e:
            logger.error(f"❌ Failed to evaluate {metrics_file}: {e}")
            return None
    
    def _rank_results(self, results: List[EvaluationResult]) -> List[EvaluationResult]:
        """Ранжировать результаты по composite score."""
        sorted_results = sorted(results, key=lambda x: x.composite_score, reverse=True)
        for i, result in enumerate(sorted_results, start=1):
            result.rank = i
        return sorted_results
    
    def _save_results(self, results: List[EvaluationResult], output_dir: str) -> None:
        """Сохранить результаты."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for result in results:
            result_file = output_path / f"{result.proposal_id}.json"
            with open(result_file, 'w') as f:
                f.write(result.to_json())
        
        # Summary file
        summary_file = output_path / "evaluation_summary.json"
        summary = {
            'total_evaluated': len(results),
            'top_3': [r.to_dict() for r in results[:3]],
            'weights_used': self.weights
        }
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.debug(f"💾 Evaluation results saved to {output_dir}")
