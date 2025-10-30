"""
Legion Agents Module - базовые классы для создания агентов.

Этот модуль определяет:
- Базовый интерфейс для всех агентов
- Поведенческие методы
- Жизненные циклы
"""

import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

# Конфигурация логирования
logger = logging.getLogger(__name__)


class LegionAgent(ABC):
    """
    Базовый класс для всех агентов в Legion Framework.
    
    Этот класс дефинирует абстрактные методы для:
    - Инициализации агента
    - Запуска и остановки выполнения
    - Обработки задач
    - Мониторинга статуса
    
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
            config (Dict[str, Any], optional): Конфигурация агента. По умолчанию None.
        """
        self.agent_id: str = agent_id
        self.is_active: bool = False
        self.config: Dict[str, Any] = config or {}
        
        logger.info(f"Agent '{agent_id}' initialized")
    
    @abstractmethod
    def execute(self, task_data: Dict[str, Any]) -> Any:
        """
        Обработать и выполнить задачу.
        
        Каждый агент должен реализовать этот метод.
        
        Args:
            task_data (Dict[str, Any]): Данные задачи для обработки
        
        Returns:
            Any: Результат выполнения
        """
        pass
    
    def start(self) -> None:
        """
        Запустить агент.
        """
        self.is_active = True
        logger.info(f"Agent '{self.agent_id}' started")
    
    def stop(self) -> None:
        """
        Остановить агент.
        """
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
            bool: True если данные валидны, иначе False
        """
        # Плацехолдер для валидации
        return task_data is not None
    
    def __repr__(self) -> str:
        """
        Строковое представление агента.
        
        Returns:
            str: Описание агента
        """
        return f"<LegionAgent {self.agent_id} (active={self.is_active})>"
