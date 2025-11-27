# -*- coding: utf-8 -*-
"""
Base Agent - базовый класс для всех агентов Legion Framework.

Этот модуль предоставляет базовый класс LegionAgent, который должны наследовать
все специализированные агенты системы.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

# Конфигурация логирования
logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Конфигурация агента."""
    name: str
    agent_type: str
    enabled: bool = True
    timeout: float = 30.0
    retry_count: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


class LegionAgent(ABC):
    """
    Базовый класс для всех агентов в Legion Framework.
    
    Предоставляет интерфейс для создания специализированных агентов,
    которые могут выполнять различные задачи в системе.
    
    Attributes:
        config (AgentConfig): Конфигурация агента
        agent_id (str): Уникальный идентификатор агента
        is_running (bool): Флаг статуса работы агента
    """
    
    def __init__(self, config: AgentConfig):
        """
        Инициализация базового агента.
        
        Args:
            config (AgentConfig): Конфигурация агента
        """
        self.config = config
        self.agent_id = config.name
        self.is_running = False
        self.created_at = datetime.now()
        logger.info(f"Initialized agent: {self.agent_id}")
    
    async def initialize(self) -> None:
        """
        Инициализация агента перед запуском.
        Переопределяется в подклассах для специфической логики инициализации.
        """
        logger.debug(f"Agent {self.agent_id} initialized")
    
    async def start(self) -> None:
        """
        Запуск агента.
        """
        self.is_running = True
        logger.info(f"Agent {self.agent_id} started")
        await self.initialize()
    
    async def stop(self) -> None:
        """
        Остановка агента.
        """
        self.is_running = False
        logger.info(f"Agent {self.agent_id} stopped")
    
    @abstractmethod
    async def execute(self, task_data: Dict[str, Any]) -> Any:
        """
        Выполнение задачи агентом.
        Должна быть реализована в подклассах.
        
        Args:
            task_data (Dict[str, Any]): Данные задачи
            
        Returns:
            Any: Результат выполнения задачи
        """
        raise NotImplementedError("Subclasses must implement execute method")
    
    async def handle_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка задачи с обработкой ошибок и retry логикой.
        
        Args:
            task_id (str): Идентификатор задачи
            task_data (Dict[str, Any]): Данные задачи
            
        Returns:
            Dict[str, Any]: Результат обработки
        """
        if not self.is_running:
            raise RuntimeError(f"Agent {self.agent_id} is not running")
        
        retry_count = 0
        last_error = None
        
        while retry_count < self.config.retry_count:
            try:
                result = await asyncio.wait_for(
                    self.execute(task_data),
                    timeout=self.config.timeout
                )
                logger.info(f"Task {task_id} completed successfully")
                return {
                    "status": "success",
                    "task_id": task_id,
                    "agent_id": self.agent_id,
                    "result": result
                }
            except asyncio.TimeoutError:
                last_error = "Task execution timeout"
                logger.warning(f"Task {task_id} timeout (attempt {retry_count + 1})")
                retry_count += 1
            except Exception as e:
                last_error = str(e)
                logger.error(f"Task {task_id} failed: {e} (attempt {retry_count + 1})")
                retry_count += 1
        
        logger.error(f"Task {task_id} failed after {self.config.retry_count} retries")
        return {
            "status": "failed",
            "task_id": task_id,
            "agent_id": self.agent_id,
            "error": last_error
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получить статус агента.
        
        Returns:
            Dict[str, Any]: Информация о статусе агента
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.config.agent_type,
            "is_running": self.is_running,
            "created_at": self.created_at.isoformat(),
            "enabled": self.config.enabled
        }
