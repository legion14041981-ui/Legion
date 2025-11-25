"""RiskAnalyzer — оценка риска патчей.

Определяет уровень риска (0-3) для каждого патча.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """Анализатор риска патчей."""
    
    RISK_LEVELS = {
        0: "whitespace/imports only",
        1: "single line patch",
        2: "function-level patch",
        3: "file rewrite"
    }
    
    def __init__(self):
        self.logger = logger
    
    def validate(self, patch, risk_limit: int) -> bool:
        """
        Проверяет, допустим ли патч согласно risk_limit.
        
        Args:
            patch: Patch объект
            risk_limit: Максимальный допустимый уровень риска
        
        Returns:
            True если патч допустим
        """
        if patch.risk_level > risk_limit:
            logger.warning(
                f"[RiskAnalyzer] Patch rejected: "
                f"risk {patch.risk_level} > limit {risk_limit}"
            )
            return False
        
        logger.info(f"[RiskAnalyzer] Patch approved: risk {patch.risk_level}")
        return True
    
    def assess_risk(self, diff: str) -> int:
        """
        Оценивает риск патча на основе unified diff.
        
        Args:
            diff: Unified diff строка
        
        Returns:
            Risk level (0-3)
        """
        lines = diff.splitlines()
        
        # Подсчитываем изменённые строки
        added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
        
        total_changes = added + removed
        
        # Определяем risk level
        if total_changes == 0:
            return 0
        elif total_changes <= 3:
            return 0  # Whitespace/imports
        elif total_changes <= 10:
            return 1  # Single line patch
        elif total_changes <= 50:
            return 2  # Function-level patch
        else:
            return 3  # File rewrite
    
    def explain_risk(self, level: int) -> str:
        """
        Возвращает объяснение уровня риска.
        
        Args:
            level: Risk level (0-3)
        
        Returns:
            Описание риска
        """
        return self.RISK_LEVELS.get(level, "unknown risk")
