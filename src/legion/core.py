"""
Legion Core Module - руководящая система работы многоагентной архитектуры.

Этот модуль отвечает за:
- Координацию эксекуции агентов
- Диспетчеризацию задач
- Логирование и мониторинг
- Async/await поддержку (v2.3)
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC
from .database import LegionDatabase
import os
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Конфигурация логирования
logger = logging.getLogger(__name__)


def safe_load_dotenv() -> bool:
    """
    Безопасная загрузка .env файла с обработкой ошибок кодировки.
    
    Реализует self-healing механизм:
    1. Попытка загрузить с UTF-8
    2. При ошибке - автоматическая конвертация из UTF-16/CP1251/Latin-1
    3. Пересохранение в UTF-8
    
    Returns:
        bool: True если загрузка успешна, False в противном случае
    """
    env_path = Path(__file__).parent.parent.parent / '.env'
    
    if not env_path.exists():
        logger.warning(f"⚠️ .env file not found at {env_path}")
        logger.info("💡 Create .env file with your configuration")
        return False
    
    try:
        # Попытка загрузить с UTF-8
        load_dotenv(env_path, encoding='utf-8')
        logger.info("✅ .env loaded successfully")
        return True
    except UnicodeDecodeError as e:
        logger.error(f"❌ .env file has invalid UTF-8 encoding: {e}")
        logger.info(f"📝 Attempting to fix encoding...")
        
        try:
            # Прочитать как байты
            content = env_path.read_bytes()
            
            # Попытка декодировать с разными кодировками
            for encoding in ['utf-16', 'utf-16-le', 'utf-16-be', 'cp1251', 'cp1252', 'latin-1']:
                try:
                    text = content.decode(encoding)
                    
                    # Создать резервную копию
                    backup_path = env_path.with_suffix('.env.backup')
                    backup_path.write_bytes(content)
                    logger.info(f"📦 Backup created: {backup_path}")
                    
                    # Пересохранить в UTF-8
                    env_path.write_text(text, encoding='utf-8')
                    logger.info(f"✅ Fixed encoding: {encoding} → UTF-8")
                    
                    # Загрузить исправленный файл
                    load_dotenv(env_path)
                    return True
                    
                except (UnicodeDecodeError, UnicodeEncodeError):
                    continue
            
            logger.error(f"❌ Could not fix encoding automatically")
            logger.info(f"💡 Please recreate .env file manually with UTF-8 encoding")
            logger.info(f"   Example content:")
            logger.info(f"   OPENAI_API_KEY=your_key_here")
            logger.info(f"   ANTHROPIC_API_KEY=your_key_here")
            logger.info(f"   LEGION_OS_ENABLED=true")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error fixing .env: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Unexpected error loading .env: {e}")
        return False


# Загрузка переменных окружения с обработкой ошибок
if not safe_load_dotenv():
    logger.warning("⚠️ Running without .env configuration")


class LegionCore:
    """
    Основное ядро Legion Framework.
    
    Отвечает за запуск и управление экосистемой агентов:
    - Инициализация и конфигурация
    - Координация эксекуции
    - Логирование
    - Async/await (v2.3)
    - Health checks (v2.3)
    - Graceful shutdown (v2.3)
    
    Attributes:
        agents (Dict[str, Any]): Словарь зарегистрированных агентов
        is_running (bool): Флаг статуса работы ядра
        _health_status (Dict): Статус здоровья системы
        _metrics (Dict): Метрики производительности
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Объект инициализации LegionCore.
        
        Args:
            config (Dict[str, Any], optional): Конфигурация системы. По умолчанию None.
        """
        self.agents: Dict[str, Any] = {}
        self.is_running: bool = False
        self.config: Dict[str, Any] = config or {}
        self._shutdown_event = asyncio.Event()
        self._health_status = {"status": "initializing", "timestamp": datetime.utcnow().isoformat()}
        self._agent_registry_lock = asyncio.Lock()
        self._metrics = {
            "agents_registered": 0,
            "tasks_dispatched": 0,
            "errors": 0
        }

        # Подключение к БД с retry
        try:
            self.db = self._init_database_with_retry(max_retries=3)
            logger.info("Database connection established")
        except Exception as e:
            logger.warning(f"Database not available: {e}")
            self.db = None
        
        logger.info("LegionCore initialized")
        self._health_status = {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    
    def _init_database_with_retry(self, max_retries: int = 3) -> Optional[LegionDatabase]:
        """
        Инициализация БД с retry механизмом.
        
        Args:
            max_retries: Максимальное количество попыток
        
        Returns:
            LegionDatabase или None при неудаче
        """
        import time
        for attempt in range(max_retries):
            try:
                db = LegionDatabase()
                logger.info(f"Database connected on attempt {attempt + 1}")
                return db
            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
        return None
    
    async def register_agent_async(self, agent_id: str, agent: Any) -> bool:
        """
        Асинхронная регистрация нового агента в системе (v2.3).
        
        Args:
            agent_id (str): Уникальный идентификатор агента
            agent (Any): Объект агента
        
        Returns:
            bool: True если регистрация успешна
        """
        async with self._agent_registry_lock:
            if agent_id in self.agents:
                logger.warning(f"Agent '{agent_id}' already registered, updating...")
            
            self.agents[agent_id] = agent
            self._metrics["agents_registered"] += 1
            logger.info(f"Agent '{agent_id}' registered successfully")

            # Синхронизация с БД (async)
            if self.db:
                try:
                    await asyncio.to_thread(
                        self.db.register_agent,
                        agent_id=agent_id,
                        name=agent.__class__.__name__,
                        config=getattr(agent, 'config', {})
                    )
                except Exception as e:
                    logger.error(f"Failed to sync agent to database: {e}")
                    self._metrics["errors"] += 1
                    return False
            
            return True
    
    def register_agent(self, agent_id: str, agent: Any) -> None:
        """
        Синхронная регистрация агента (legacy, deprecated).
        
        Рекомендуется использовать register_agent_async().
        
        Args:
            agent_id (str): Уникальный идентификатор агента
            agent (Any): Объект агента
        """
        logger.warning("Using deprecated synchronous register_agent(). Use register_agent_async() instead.")
        
        self.agents[agent_id] = agent
        self._metrics["agents_registered"] += 1
        logger.info(f"Agent '{agent_id}' registered")

        # Синхронизация с БД
        if self.db:
            try:
                self.db.register_agent(
                    agent_id=agent_id,
                    name=agent.__class__.__name__,
                    config=getattr(agent, 'config', {})
                )
            except Exception as e:
                logger.error(f"Failed to sync agent to database: {e}")
                self._metrics["errors"] += 1
    
    async def dispatch_task_async(self, task_id: str, task_data: Dict[str, Any]) -> Optional[Any]:
        """
        Асинхронная диспетчеризация задачи к соответствующему агенту (v2.3).
        
        Args:
            task_id (str): Идентификатор задачи
            task_data (Dict[str, Any]): Данные задачи
        
        Returns:
            Optional[Any]: Результат выполнения задачи
        """
        self._metrics["tasks_dispatched"] += 1
        logger.debug(f"Dispatching task '{task_id}' with data: {task_data}")
        
        # Логика диспетчеризации будет реализована в подклассах или через orchestrator
        return None
    
    def dispatch_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """
        Диспетчеризация задачи к соответствующему агенту.
        
        Args:
            task_id (str): Идентификатор задачи
            task_data (Dict[str, Any]): Данные задачи
        """
        self._metrics["tasks_dispatched"] += 1
        logger.debug(f"Dispatching task '{task_id}' with data: {task_data}")
    
    async def start_async(self) -> None:
        """
        Асинхронный запуск экосистемы агентов (v2.3).
        """
        if self.is_running:
            logger.warning("LegionCore already running")
            return
        
        self.is_running = True
        self._health_status = {"status": "running", "timestamp": datetime.utcnow().isoformat()}
        logger.info("LegionCore started")
        
        # Запуск всех агентов
        for agent_id, agent in self.agents.items():
            try:
                if hasattr(agent, 'start'):
                    agent.start()
            except Exception as e:
                logger.error(f"Failed to start agent '{agent_id}': {e}")
                self._metrics["errors"] += 1
    
    def start(self) -> None:
        """
        Синхронный запуск экосистемы агентов (legacy).
        """
        self.is_running = True
        self._health_status = {"status": "running", "timestamp": datetime.utcnow().isoformat()}
        logger.info("LegionCore started")
    
    async def stop_async(self) -> None:
        """
        Асинхронная остановка экосистемы агентов с graceful shutdown (v2.3).
        """
        if not self.is_running:
            logger.warning("LegionCore not running")
            return
        
        logger.info("Initiating graceful shutdown...")
        self._health_status = {"status": "shutting_down", "timestamp": datetime.utcnow().isoformat()}
        
        # Остановка всех агентов
        for agent_id, agent in self.agents.items():
            try:
                if hasattr(agent, 'stop'):
                    agent.stop()
                logger.info(f"Agent '{agent_id}' stopped")
            except Exception as e:
                logger.error(f"Error stopping agent '{agent_id}': {e}")
        
        self.is_running = False
        self._shutdown_event.set()
        self._health_status = {"status": "stopped", "timestamp": datetime.utcnow().isoformat()}
        logger.info("LegionCore stopped gracefully")
    
    def stop(self) -> None:
        """
        Остановка экосистемы агентов.
        """
        self.is_running = False
        self._health_status = {"status": "stopped", "timestamp": datetime.utcnow().isoformat()}
        logger.info("LegionCore stopped")
    
    def get_health(self) -> Dict[str, Any]:
        """
        Получить health status системы.
        
        Returns:
            Dict[str, Any]: Health check информация
        """
        return {
            **self._health_status,
            "agents_count": len(self.agents),
            "metrics": self._metrics.copy()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Получить метрики производительности.
        
        Returns:
            Dict[str, Any]: Метрики системы
        """
        return self._metrics.copy()
    
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
