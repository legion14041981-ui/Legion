"""
Legion Core Module - руководитель работы многоагентного система.

Этот модуль отвечает за:
- Координацию эксекуции агентов
- Диспетчеризацию задач
- Логирование и мониторинг
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC
from .database import LegionDatabase
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурация логирования
logger = logging.getLogger(__name__)


class LegionCore:
    """
    Основное ядро Legion Framework.
    
    Отвечает за запуск и управление экосистемой агентов:
    - Инициализация и конфигурация
    - Координация эксекуции
    - Логирование
    
    Attributes:
        agents (Dict[str, Any]): Словарь зарегистрированных агентов
        is_running (bool): Флаг статуса работы ядра
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация LegionCore.
        
        Args:
            config (Dict[str, Any], optional): Конфигурация системы. По умолчанию None.
        """
        self.agents: Dict[str, Any] = {}
        self.is_running: bool = False
        self.config: Dict[str, Any] = config or {}

        # Подключение к БД
        try:
            self.db = LegionDatabase()
            logger.info("Database connection established")
        except Exception as e:
            logger.warning(f"Database not available: {e}")
            self.db = None
        
        logger.info("LegionCore initialized")
    
    def register_agent(self, agent_id: str, agent: Any) -> None:
        """
        Регистрация нового агента в системе.
        
        Args:
            agent_id (str): Уникальный идентификатор агента
            agent (Any): Объект агента
        """
        # Простая регистрация агента
        self.agents[agent_id] = agent
        logger.info(f"Agent '{agent_id}' registered")

        # Синхронизация с БД
        if self.db:
            try:
                self.db.register_agent(
                    agent_id=agent_id,
                    name=agent.__class__.__name__,
                    config=agent.config
                )
            except Exception as e:
                logger.error(f"Failed to sync agent to database: {e}")
    
    def dispatch_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """
        Диспетчеризация задачи к соответствующему агенту.
        
        Args:
            task_id (str): Идентификатор задачи
            task_data (Dict[str, Any]): Данные задачи
        """
        # Плейсхолдер для диспетчеризации
        logger.debug(f"Dispatching task '{task_id}' with data: {task_data}")
    
    def start(self) -> None:
        """
        Запуск экосистемы агентов.
        """
        self.is_running = True
        logger.info("LegionCore started")
    
    def stop(self) -> None:
        """
        Остановка экосистемы агентов.
        """
        self.is_running = False
        logger.info("LegionCore stopped")
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """
        Получить агента по его идентификатору.
        
        Args:
            agent_id (str): Идентификатор агента
        
        Returns:
            Optional[Any]: Объект агента или None
        """
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, Any]:
        """
        Получить всех зарегистрированных агентов.
        
        Returns:
            Dict[str, Any]: Словарь агентов
        """
        return self.agents.copy()
