"""MCP Tool Registry - система регистрации и управления инструментами.

Предоставляет централизованный реестр для регистрации, поиска и выполнения
инструментов в рамках Model Context Protocol (MCP).
"""

import logging
from typing import Any, Callable, Dict, List, Optional
import asyncio

logger = logging.getLogger(__name__)


class ToolDefinition:
    """Определение инструмента в MCP реестре."""
    
    def __init__(
        self,
        name: str,
        handler: Callable,
        description: str,
        category: str = 'general',
        examples: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.handler = handler
        self.description = description
        self.category = category
        self.examples = examples or []
        self.parameters = parameters or {}
    
    def __repr__(self) -> str:
        return f"<Tool {self.name} ({self.category})>"


class LegionToolRegistry:
    """Реестр инструментов для MCP интеграции.
    
    Управляет регистрацией, поиском и выполнением инструментов.
    Поддерживает категоризацию и фильтрацию инструментов.
    """
    
    def __init__(self):
        """Инициализация реестра инструментов."""
        self._tools: Dict[str, ToolDefinition] = {}
        logger.info("LegionToolRegistry initialized")
    
    def register(
        self,
        name: str,
        handler: Callable,
        description: str,
        category: str = 'general',
        examples: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """Зарегистрировать новый инструмент.
        
        Args:
            name: Уникальное имя инструмента
            handler: Callable для выполнения (синхронный или асинхронный)
            description: Описание функциональности
            category: Категория инструмента (browser, file, network, etc.)
            examples: Примеры использования
            parameters: Схема параметров (JSON Schema)
        """
        if name in self._tools:
            logger.warning(f"Tool '{name}' already registered, overwriting")
        
        tool = ToolDefinition(
            name=name,
            handler=handler,
            description=description,
            category=category,
            examples=examples,
            parameters=parameters
        )
        
        self._tools[name] = tool
        logger.info(f"Registered tool: {name} ({category})")
    
    def unregister(self, name: str) -> bool:
        """Удалить инструмент из реестра.
        
        Args:
            name: Имя инструмента
            
        Returns:
            bool: True если инструмент был удалён
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Получить определение инструмента.
        
        Args:
            name: Имя инструмента
            
        Returns:
            ToolDefinition или None
        """
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[ToolDefinition]:
        """Получить список всех инструментов.
        
        Args:
            category: Фильтр по категории (опционально)
            
        Returns:
            Список инструментов
        """
        if category:
            return [
                tool for tool in self._tools.values()
                if tool.category == category
            ]
        return list(self._tools.values())
    
    def list_categories(self) -> List[str]:
        """Получить список всех категорий.
        
        Returns:
            Список уникальных категорий
        """
        return list(set(tool.category for tool in self._tools.values()))
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        """Выполнить инструмент по имени.
        
        Args:
            tool_name: Имя инструмента
            **kwargs: Параметры для передачи в handler
            
        Returns:
            Результат выполнения инструмента
            
        Raises:
            KeyError: Если инструмент не найден
            Exception: Ошибки при выполнении
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise KeyError(f"Tool '{tool_name}' not found in registry")
        
        logger.debug(f"Executing tool: {tool_name} with args: {kwargs}")
        
        # Проверка, является ли handler асинхронным
        if asyncio.iscoroutinefunction(tool.handler):
            result = await tool.handler(**kwargs)
        else:
            # Запуск синхронного handler в executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: tool.handler(**kwargs))
        
        logger.debug(f"Tool {tool_name} completed successfully")
        return result
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Получить JSON Schema для инструмента (для MCP).
        
        Args:
            tool_name: Имя инструмента
            
        Returns:
            JSON Schema или None
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return None
        
        return {
            'name': tool.name,
            'description': tool.description,
            'category': tool.category,
            'parameters': tool.parameters,
            'examples': tool.examples
        }
    
    def export_schemas(self) -> List[Dict[str, Any]]:
        """Экспортировать схемы всех инструментов (для MCP server).
        
        Returns:
            Список JSON схем
        """
        return [
            self.get_tool_schema(tool.name)
            for tool in self._tools.values()
        ]
    
    def __len__(self) -> int:
        """Количество зарегистрированных инструментов."""
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        """Проверка наличия инструмента."""
        return name in self._tools
    
    def __repr__(self) -> str:
        return f"<LegionToolRegistry: {len(self._tools)} tools>"
