"""Legion Agents Module - базовые классы для создания агентов.

Этот модуль определяет:
- Базовый интерфейс для всех агентов
- Поведенческие методы
- Жизненные циклы
- Async/await поддержку (v2.2)
"""

import logging
import asyncio
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LegionAgent(ABC):
    """
    Базовый класс для всех агентов в Legion Framework.
    
    v2.2: Добавлена поддержка async/await для неблокирующего выполнения.
    
    Attributes:
        agent_id (str): Уникальный идентификатор
        is_active (bool): Флаг текущего статуса
        config (Dict): Конфигурация агента
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация базового агента.
        
        Args:
            agent_id (str): Уникальный идентификатор агента
            config (Dict[str, Any], optional): Конфигурация агента
        """
        self.agent_id: str = agent_id
        self.is_active: bool = False
        self.config: Dict[str, Any] = config or {}
        
        logger.info(f"Agent '{agent_id}' initialized")
    
    @abstractmethod
    def execute(self, task_data: Dict[str, Any]) -> Any:
        """
        Обработать и выполнить задачу (синхронный метод).
        
        Каждый агент должен реализовать этот метод.
        
        Args:
            task_data (Dict[str, Any]): Данные задачи для обработки
        
        Returns:
            Any: Результат выполнения
        """
        pass
    
    async def execute_async(self, task_data: Dict[str, Any]) -> Any:
        """
        Асинхронное выполнение задачи (v2.2).
        
        По умолчанию делегирует выполнение синхронному методу execute().
        Агенты могут переопределить этот метод для нативной async реализации.
        
        Args:
            task_data (Dict[str, Any]): Данные задачи
        
        Returns:
            Any: Результат выполнения
        """
        # По умолчанию: запустить синхронный execute() в executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.execute, task_data)
        return result
    
    def start(self) -> None:
        """Запустить агент."""
        self.is_active = True
        logger.info(f"Agent '{self.agent_id}' started")
    
    def stop(self) -> None:
        """Остановить агент."""
        self.is_active = False
        logger.info(f"Agent '{self.agent_id}' stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получить текущий статус агента.
        
        Returns:
            Dict[str, Any]: Статус агента
        """
        return {
            'agent_id': self.agent_id,
            'is_active': self.is_active,
            'config': self.config
        }
    
    def validate_task(self, task_data: Dict[str, Any]) -> bool:
        """
        Проверить валидность данных задачи.
        
        Args:
            task_data (Dict[str, Any]): Данные для проверки
        
        Returns:
            bool: True если данные валидны
        """
        return task_data is not None
    
    def __repr__(self) -> str:
        """
        Строковое представление агента.
        
        Returns:
            str: Описание агента
        """
        return f"<LegionAgent {self.agent_id} (active={self.is_active})>"


__all__ = ['LegionAgent']
