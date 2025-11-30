"""
Humanistic Controller - Microsoft AI principles integration.

Реализует концепцию "AI на стороне человека":
- Safety gates для high-risk изменений
- Memory для контекста и обучения
- User approval для критических решений
- Containment policies
- Transparent decision-making
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DecisionRecord:
    """Запись о принятом решении."""
    id: str
    timestamp: str
    decision_type: str
    proposal_id: str
    risk_score: float
    user_approved: bool
    reasoning: str
    outcome: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MemoryManager:
    """
    Менеджер памяти для контекста и обучения.
    
    Хранит:
    - Историю архитектурных экспериментов
    - Успешные/неудачные конфигурации
    - Паттерны принятия решений
    - User preferences
    """
    
    def __init__(self, storage_dir: str = "artifacts/memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.short_term: List[DecisionRecord] = []  # Last 100 decisions
        self.max_short_term = 100
        logger.info(f"✅ MemoryManager initialized at {storage_dir}")
    
    def record_decision(self, record: DecisionRecord) -> None:
        """Записать решение в память."""
        self.short_term.append(record)
        if len(self.short_term) > self.max_short_term:
            self._archive_old_records()
        
        # Сохранить на диск
        self._persist_record(record)
        logger.debug(f"📝 Recorded decision: {record.id}")
    
    def get_similar_decisions(self, proposal_id: str, n: int = 5) -> List[DecisionRecord]:
        """Найти похожие решения из прошлого."""
        # TODO: Semantic search по proposal configs
        return self.short_term[-n:]
    
    def get_success_patterns(self) -> Dict[str, float]:
        """Извлечь паттерны успешных конфигураций."""
        successful = [r for r in self.short_term if r.outcome == 'success']
        
        patterns = {}
        for record in successful:
            # TODO: Анализ общих черт
            patterns[record.proposal_id] = record.risk_score
        
        return patterns
    
    def _archive_old_records(self) -> None:
        """Архивировать старые записи."""
        archive_file = self.storage_dir / f"archive-{datetime.utcnow().timestamp()}.json"
        with open(archive_file, 'w') as f:
            json.dump([r.to_dict() for r in self.short_term], f, indent=2)
        
        # Очистить short-term
        self.short_term = self.short_term[-50:]  # Keep last 50
        logger.info(f"📦 Archived old records to {archive_file}")
    
    def _persist_record(self, record: DecisionRecord) -> None:
        """Сохранить запись на диск."""
        record_file = self.storage_dir / "current" / f"{record.id}.json"
        record_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(record_file, 'w') as f:
            f.write(json.dumps(record.to_dict(), indent=2))


class ContainmentPolicy:
    """
    Containment Policy - ограничения для безопасности.
    
    Предотвращает:
    - Неконтролируемую автономию
    - Критические изменения без одобрения
    - Деградацию системы
    """
    
    RISK_THRESHOLDS = {
        'low': 0.3,
        'medium': 0.6,
        'high': 0.8
    }
    
    def __init__(self, mode: str = "conservative"):
        """
        Инициализация политики.
        
        Args:
            mode: Режим (conservative, standard, aggressive)
        """
        self.mode = mode
        self.auto_approve_threshold = self._get_threshold(mode)
        logger.info(f"✅ ContainmentPolicy initialized: mode={mode}, threshold={self.auto_approve_threshold}")
    
    def _get_threshold(self, mode: str) -> float:
        """Получить порог для режима."""
        thresholds = {
            'conservative': 0.2,  # Почти все требуют одобрения
            'standard': 0.5,
            'aggressive': 0.8  # Авто-одобрение почти всего
        }
        return thresholds.get(mode, 0.5)
    
    def check_approval_required(self, risk_score: float, change_type: str) -> bool:
        """
        Проверить, требуется ли одобрение пользователя.
        
        Args:
            risk_score: Оценка риска (0.0-1.0)
            change_type: Тип изменения (architecture, deployment, data)
        
        Returns:
            True если требуется одобрение
        """
        # Критические типы всегда требуют одобрения
        critical_types = ['deployment', 'data_deletion', 'system_config']
        if change_type in critical_types:
            logger.warning(f"⚠️ Critical change type '{change_type}' requires approval")
            return True
        
        # Проверка по риску
        if risk_score > self.auto_approve_threshold:
            logger.warning(f"⚠️ High risk score {risk_score:.2f} requires approval")
            return True
        
        return False
    
    def get_risk_category(self, risk_score: float) -> str:
        """Получить категорию риска."""
        for category, threshold in self.RISK_THRESHOLDS.items():
            if risk_score <= threshold:
                return category
        return 'critical'


class HumanisticController:
    """
    Гуманистический контроллер для Ultra-Orchestrator v4.
    
    Принципы:
    - AI действует в интересах пользователя
    - Transparent decision-making
    - User approval для критических решений
    - Memory-based learning
    - Containment для безопасности
    """
    
    def __init__(
        self,
        mode: str = "standard",
        memory_enabled: bool = True
    ):
        """
        Инициализация контроллера.
        
        Args:
            mode: Режим работы (conservative, standard, aggressive)
            memory_enabled: Включить Memory Manager
        """
        self.mode = mode
        self.containment = ContainmentPolicy(mode=mode)
        self.memory = MemoryManager() if memory_enabled else None
        logger.info(f"✅ HumanisticController initialized: mode={mode}")
    
    def evaluate_proposal(
        self,
        proposal: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Оценить архитектурное предложение.
        
        Args:
            proposal: ArchitectureProposal
            context: Дополнительный контекст
        
        Returns:
            Результат оценки
        """
        logger.info(f"🔍 Evaluating proposal: {proposal.id}")
        
        # Проверка риска
        risk_category = self.containment.get_risk_category(proposal.risk_score)
        approval_required = self.containment.check_approval_required(
            proposal.risk_score,
            proposal.strategy
        )
        
        # Поиск похожих в памяти
        similar_decisions = []
        if self.memory:
            similar_decisions = self.memory.get_similar_decisions(proposal.id)
        
        evaluation = {
            'proposal_id': proposal.id,
            'risk_score': proposal.risk_score,
            'risk_category': risk_category,
            'approval_required': approval_required,
            'similar_past_decisions': len(similar_decisions),
            'recommendation': self._generate_recommendation(
                proposal, risk_category, similar_decisions
            )
        }
        
        logger.info(f"   Risk: {risk_category} ({proposal.risk_score:.2f})")
        logger.info(f"   Approval required: {approval_required}")
        
        return evaluation
    
    def request_approval(
        self,
        proposal: Any,
        evaluation: Dict[str, Any]
    ) -> bool:
        """
        Запросить одобрение у пользователя.
        
        Args:
            proposal: ArchitectureProposal
            evaluation: Результат оценки
        
        Returns:
            True если одобрено
        """
        logger.info("\n" + "="*60)
        logger.info("🚨 USER APPROVAL REQUIRED")
        logger.info("="*60)
        logger.info(f"Proposal: {proposal.id}")
        logger.info(f"Strategy: {proposal.strategy}")
        logger.info(f"Risk Score: {proposal.risk_score:.2f} ({evaluation['risk_category']})")
        logger.info(f"Expected FLOPs: {proposal.expected_flops:,}")
        logger.info(f"Expected Latency: {proposal.expected_latency_ms:.1f}ms")
        logger.info(f"\nRecommendation: {evaluation['recommendation']}")
        logger.info("="*60)
        
        # В production - отправка в Slack/Email/Web UI
        # Пока - консольный ввод
        response = input("\nApprove this proposal? (yes/no/skip): ").strip().lower()
        
        approved = response == 'yes'
        
        # Записать в память
        if self.memory:
            record = DecisionRecord(
                id=f"decision-{datetime.utcnow().timestamp()}",
                timestamp=datetime.utcnow().isoformat(),
                decision_type="architecture_approval",
                proposal_id=proposal.id,
                risk_score=proposal.risk_score,
                user_approved=approved,
                reasoning=f"User {response}"
            )
            self.memory.record_decision(record)
        
        logger.info(f"{'✅ Approved' if approved else '❌ Rejected'}")
        return approved
    
    def _generate_recommendation(
        self,
        proposal: Any,
        risk_category: str,
        similar_decisions: List[DecisionRecord]
    ) -> str:
        """Сгенерировать рекомендацию."""
        if risk_category == 'low':
            return "✅ Low risk. Safe to proceed."
        elif risk_category == 'medium':
            return "⚠️ Medium risk. Review carefully before proceeding."
        elif risk_category == 'high':
            return "🚨 High risk. Consider alternative approaches."
        else:
            return "🛑 Critical risk. Requires extensive review and mitigation plan."
    
    def record_outcome(
        self,
        proposal_id: str,
        outcome: str,
        metrics: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Записать результат применения proposal.
        
        Args:
            proposal_id: ID предложения
            outcome: Результат (success, failure, degradation)
            metrics: Метрики после применения
        """
        if not self.memory:
            return
        
        logger.info(f"📊 Recording outcome for {proposal_id}: {outcome}")
        
        # Обновить запись в памяти
        for record in self.memory.short_term:
            if record.proposal_id == proposal_id:
                record.outcome = outcome
                break
