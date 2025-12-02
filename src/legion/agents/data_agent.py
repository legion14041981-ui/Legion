# -*- coding: utf-8 -*-
"""
DataAgent - агент для обработки и трансформации данных.

Поддерживает:
- Парсинг различных форматов (JSON, CSV, XML)
- Трансформацию данных (фильтрация, сортировка, агрегация)
- Валидацию данных
- Работу с pandas DataFrame
- Статистический анализ

OPTIMIZED (Proposal #3): Resource cleanup and memory management
"""

import asyncio
import json
import csv
import xml.etree.ElementTree as ET
import gc
import weakref
from typing import Dict, List, Any, Optional, Union
from io import StringIO
from contextlib import contextmanager
import logging

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("pandas not installed. DataFrame operations will be limited.")

from .base_agent import LegionAgent, AgentConfig


class MemoryPool:
    """
    Simple memory pool for reusing buffers.
    OPTIMIZED (Proposal #3): Reduce allocation overhead.
    """
    
    def __init__(self, max_size: int = 100):
        self.pool: List[StringIO] = []
        self.max_size = max_size
        self._in_use = weakref.WeakSet()
    
    def acquire(self) -> StringIO:
        """Acquire a buffer from the pool."""
        if self.pool:
            buf = self.pool.pop()
            buf.seek(0)
            buf.truncate(0)
        else:
            buf = StringIO()
        
        self._in_use.add(buf)
        return buf
    
    def release(self, buf: StringIO) -> None:
        """Release a buffer back to the pool."""
        if buf in self._in_use:
            self._in_use.remove(buf)
        
        if len(self.pool) < self.max_size:
            buf.seek(0)
            buf.truncate(0)
            self.pool.append(buf)
        else:
            buf.close()
    
    @contextmanager
    def buffer(self):
        """Context manager for automatic buffer acquisition and release."""
        buf = self.acquire()
        try:
            yield buf
        finally:
            self.release(buf)


class DataAgent(LegionAgent):
    """
    Агент для обработки и анализа данных.

    Поддерживает множество операций с данными:
    - Парсинг JSON, CSV, XML
    - Фильтрация и трансформация
    - Агрегация и статистика
    - Валидация данных
    
    OPTIMIZED (Proposal #3): 
    - Memory pooling for buffers
    - Explicit resource cleanup
    - Garbage collection hints
    """
    
    # Class-level memory pool (shared across instances)
    _memory_pool = MemoryPool(max_size=50)

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str = "Data processing agent",
        **kwargs: Any,
    ) -> None:
        config = AgentConfig(
            name=name,
            agent_type="DataAgent"
        )
        super().__init__(config)
        self.agent_id = agent_id
        self.description = description
        self._active_resources: List[Any] = []  # Track resources for cleanup

    async def execute(self, task_data: Dict[str, Any]) -> Any:
        """
        Execute method required by abstract base class.
        
        OPTIMIZED (Proposal #3): Added comprehensive resource cleanup.
        
        Args:
            task_data (Dict[str, Any]): Task data containing parameters for execution
            
        Returns:
            Result of the execution
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        try:
            # Execute the actual task
            raise NotImplementedError(
                "DataAgent.execute() must be implemented by subclasses. "
                "Use specific methods like parse_json(), parse_csv(), etc."
            )
        finally:
            # OPTIMIZED: Cleanup resources after execution
            await self._cleanup_resources()
    
    async def _cleanup_resources(self) -> None:
        """
        Cleanup resources used during execution.
        OPTIMIZED (Proposal #3): Explicit resource management.
        """
        # Close any tracked resources
        for resource in self._active_resources:
            try:
                if hasattr(resource, 'close'):
                    resource.close()
            except Exception as e:
                logging.warning(f"Error closing resource: {e}")
        
        self._active_resources.clear()
        
        # Hint to garbage collector
        gc.collect(generation=0)

    async def parse_json(self, data: Union[str, bytes]) -> Any:
        """
        Парсинг JSON-данных.

        :param data: строка или bytes с JSON
        :return: распарсенный объект Python
        """
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return json.loads(data)

    async def parse_csv(
        self,
        data: Union[str, bytes],
        delimiter: str = ",",
        has_header: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Парсинг CSV-данных.
        
        OPTIMIZED (Proposal #3): Uses memory pool for StringIO buffers.

        :param data: строка или bytes с CSV
        :param delimiter: разделитель
        :param has_header: первая строка содержит заголовок
        :return: список словарей (строки)
        """
        if isinstance(data, bytes):
            data = data.decode("utf-8")

        # OPTIMIZED: Use memory pool
        with self._memory_pool.buffer() as f:
            f.write(data)
            f.seek(0)
            
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter)
                result = list(reader)
            else:
                reader = csv.reader(f, delimiter=delimiter)
                result = [row for row in reader]
        
        return result

    async def parse_xml(self, data: Union[str, bytes]) -> ET.Element:
        """
        Парсинг XML-данных.

        :param data: строка или bytes с XML
        :return: корневой элемент XML-дерева
        """
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return ET.fromstring(data)

    async def filter_data(
        self,
        records: List[Dict[str, Any]],
        predicate,
    ) -> List[Dict[str, Any]]:
        """
        Фильтрация списка записей по предикату.

        :param records: список словарей
        :param predicate: функция record -> bool
        :return: отфильтрованный список
        """
        return [r for r in records if predicate(r)]

    async def aggregate(
        self,
        records: List[Dict[str, Any]],
        field: str,
        op: str = "sum",
    ) -> Any:
        """
        Агрегация по полю.

        :param records: список словарей
        :param field: имя поля для агрегации
        :param op: операция: sum, avg, min, max, count
        :return: результат агрегации
        """
        values = [r.get(field) for r in records if r.get(field) is not None]

        if not values:
            return None

        if op == "sum":
            return sum(values)
        if op == "avg":
            return sum(values) / len(values)
        if op == "min":
            return min(values)
        if op == "max":
            return max(values)
        if op == "count":
            return len(values)

        raise ValueError(f"Unsupported aggregation op: {op}")

    async def to_dataframe(
        self,
        records: List[Dict[str, Any]],
    ) -> "pd.DataFrame":
        """
        Преобразование списка записей в pandas DataFrame.
        
        OPTIMIZED (Proposal #3): Track DataFrame for cleanup.

        :param records: список словарей
        :return: DataFrame
        """
        if not PANDAS_AVAILABLE:
            raise RuntimeError("pandas is not installed")

        df = pd.DataFrame.from_records(records)
        self._active_resources.append(df)  # Track for cleanup
        return df

    async def describe_dataframe(
        self,
        df: "pd.DataFrame",
    ) -> Dict[str, Any]:
        """
        Статистическое описание DataFrame.
        
        OPTIMIZED (Proposal #3): Explicit GC hint after heavy operations.

        :param df: DataFrame
        :return: словарь с основными статистиками
        """
        if not PANDAS_AVAILABLE:
            raise RuntimeError("pandas is not installed")

        desc = df.describe(include="all")
        result = {
            "summary": desc.to_dict(),
            "shape": df.shape,
            "columns": list(df.columns),
        }
        
        # OPTIMIZED: Hint GC after heavy operation
        del desc
        gc.collect(generation=0)
        
        return result

    async def validate_records(
        self,
        records: List[Dict[str, Any]],
        schema: Dict[str, type],
    ) -> Dict[str, Any]:
        """
        Простая валидация записей по схеме типов.

        :param records: список словарей
        :param schema: поле -> ожидаемый тип
        :return: результат валидации
        """
        valid = []
        invalid = []

        for r in records:
            errors = {}
            for field, expected_type in schema.items():
                value = r.get(field)
                if value is None:
                    errors[field] = "missing"
                elif not isinstance(value, expected_type):
                    errors[field] = f"expected {expected_type}, got {type(value)}"
            if errors:
                invalid.append({"record": r, "errors": errors})
            else:
                valid.append(r)

        return {"valid": valid, "invalid": invalid}
