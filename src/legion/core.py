"""
Legion Core Module - руководителя работы многоагентного система.

Этот модуль отвечает за:
- Координацию эксекуции агентов
- Диспетчеризацию задач
- Логирование и мониторинг
- OS-уровневую интеграцию (workspace, identity, audit)
"""

import logging
import os
from typing import List, Dict, Any, Optional
from abc import ABC
from pathlib import Path
from dotenv import load_dotenv

from .database import LegionDatabase

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
    - OS Integration (если включена)
    
    Attributes:
        agents (Dict[str, Any]): Словарь зарегистрированных агентов
        is_running (bool): Флаг статуса работы ядра
        os_integration_enabled (bool): Флаг включения OS Integration
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Общая инициализация LegionCore.
        
        Args:
            config (Dict[str, Any], optional): Конфигурация системы. По умолчанию None.
        """
        self.agents: Dict[str, Any] = {}
        self.is_running: bool = False
        self.config: Dict[str, Any] = config or {}
        
        # Проверить включение OS Integration
        self.os_integration_enabled = (
            os.getenv('LEGION_OS_ENABLED', 'false').lower() == 'true'
            or self.config.get('os_integration_enabled', False)
        )
        
        # Подключение к БД
        try:
            self.db = LegionDatabase()
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.warning(f"⚠️ Database not available: {e}")
            self.db = None
        
        logger.info("✅ LegionCore initialized")
        if self.os_integration_enabled:
            logger.info("🔌 OS Integration enabled")
    
    def register_agent(self, agent_id: str, agent: Any) -> None:
        """
        Регистрация нового агента в системе.
        
        Args:
            agent_id (str): Уникальный идентификатор агента
            agent (Any): Объект агента
        """
        # Простая регистрация агента
        self.agents[agent_id] = agent
        logger.info(f"✅ Agent '{agent_id}' registered")
        
        # Синхронизация с БД
        if self.db:
            try:
                self.db.register_agent(
                    agent_id=agent_id,
                    name=agent.__class__.__name__,
                    config=getattr(agent, 'config', {})
                )
            except Exception as e:
                logger.error(f"❌ Failed to sync agent to database: {e}")
        
        # OS Integration: создать OS Interface для агента
        if self.os_integration_enabled and hasattr(agent, 'os_interface'):
            try:
                from .os_integration import OSInterface
                agent.os_interface = OSInterface(
                    agent_id=agent_id,
                    config=getattr(agent, 'config', {})
                )
                logger.info(f"🔌 OS Interface attached to agent '{agent_id}'")
            except Exception as e:
                logger.error(f"❌ Failed to attach OS Interface: {e}")
    
    def dispatch_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """
        Диспетчеризация задачи к соответствующему агенту.
        
        Args:
            task_id (str): Идентификатор задачи
            task_data (Dict[str, Any]): Данные задачи
        """
        logger.debug(f"📤 Dispatching task '{task_id}' with data: {task_data}")
        
        # Плацехолдер для реальной диспетчеризации
        # TODO: Реализовать маршрутизацию задач к агентам
    
    def start(self) -> None:
        """
        Запуск экосистемы агентов.
        """
        self.is_running = True
        logger.info("▶️ LegionCore started")
    
    def stop(self) -> None:
        """
        Остановка экосистемы агентов.
        """
        self.is_running = False
        logger.info("⏹️ LegionCore stopped")
    
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
