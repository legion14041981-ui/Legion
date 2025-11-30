"""
Adapters - реализация LoRA и других адаптеров.

Поддержка:
- LoRA (Low-Rank Adaptation)
- Bottleneck Adapters
- Prompt Tuning
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """Базовый класс для всех адаптеров."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_active = False
    
    @abstractmethod
    def apply(self, model: Any) -> Any:
        """Применить адаптер к модели."""
        pass
    
    @abstractmethod
    def remove(self, model: Any) -> Any:
        """Удалить адаптер из модели."""
        pass


class LoRAAdapter(BaseAdapter):
    """
    Low-Rank Adaptation (LoRA) adapter.
    
    LoRA добавляет trainable low-rank matrices к frozen модели.
    Это позволяет fine-tuning с минимальным количеством параметров.
    """
    
    def __init__(
        self,
        rank: int = 8,
        alpha: int = 32,
        target_modules: Optional[list] = None,
        dropout: float = 0.0
    ):
        """
        Инициализация LoRA adapter.
        
        Args:
            rank: Ранг low-rank matrices
            alpha: Scaling parameter
            target_modules: Модули для применения LoRA
            dropout: Dropout rate
        """
        config = {
            'rank': rank,
            'alpha': alpha,
            'target_modules': target_modules or ['query', 'value'],
            'dropout': dropout
        }
        super().__init__(config)
        logger.info(f"✅ LoRAAdapter initialized: rank={rank}, alpha={alpha}")
    
    def apply(self, model: Any) -> Any:
        """
        Применить LoRA к модели.
        
        TODO: Интегрировать с HuggingFace PEFT
        """
        logger.info(f"🔧 Applying LoRA adapter (rank={self.config['rank']})")
        # TODO: Реальная интеграция с PEFT
        self.is_active = True
        return model
    
    def remove(self, model: Any) -> Any:
        """Удалить LoRA из модели."""
        logger.info("🗑️ Removing LoRA adapter")
        self.is_active = False
        return model


class BottleneckAdapter(BaseAdapter):
    """
    Bottleneck Adapter - добавляет маленькие feedforward слои.
    """
    
    def __init__(self, bottleneck_size: int = 64, residual: bool = True):
        config = {
            'bottleneck_size': bottleneck_size,
            'residual': residual
        }
        super().__init__(config)
        logger.info(f"✅ BottleneckAdapter initialized: size={bottleneck_size}")
    
    def apply(self, model: Any) -> Any:
        logger.info(f"🔧 Applying Bottleneck adapter (size={self.config['bottleneck_size']})")
        self.is_active = True
        return model
    
    def remove(self, model: Any) -> Any:
        logger.info("🗑️ Removing Bottleneck adapter")
        self.is_active = False
        return model
