# -*- coding: utf-8 -*-
"""
DataAgent - агент для обработки и трансформации данных.

Поддерживает:
- Парсинг различных форматов (JSON, CSV, XML)
- Трансформацию данных (фильтрация, сортировка, агрегация)
- Валидацию данных
- Работу с pandas DataFrame
- Статистический анализ
"""

import asyncio
import json
import csv
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Union
from io import StringIO
import logging

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("pandas not installed. DataFrame operations will be limited.")

from .base_agent import LegionAgent


class DataAgent(LegionAgent):
    """
    Агент для обработки и анализа данных.

    Поддерживает множество операций с данными:
    - Парсинг JSON, CSV, XML
    - Фильтрация и трансформация
    - Агрегация и статистика
    - Валидация данных
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str = "Data processing agent",
        **kwargs: Any,
    ) -> None:
        super().__init__(agent_id=agent_id, name=name, description=description, **kwargs)

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

        :param data: строка или bytes с CSV
        :param delimiter: разделитель
        :param has_header: первая строка содержит заголовок
        :return: список словарей (строки)
        """
        if isinstance(data, bytes):
            data = data.decode("utf-8")

        f = StringIO(data)
        if has_header:
            reader = csv.DictReader(f, delimiter=delimiter)
            return list(reader)
        else:
            reader = csv.reader(f, delimiter=delimiter)
            return [row for row in reader]

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

        :param records: список словарей
        :return: DataFrame
        """
        if not PANDAS_AVAILABLE:
            raise RuntimeError("pandas is not installed")

        return pd.DataFrame.from_records(records)

    async def describe_dataframe(
        self,
        df: "pd.DataFrame",
    ) -> Dict[str, Any]:
        """
        Статистическое описание DataFrame.

        :param df: DataFrame
        :return: словарь с основными статистиками
        """
        if not PANDAS_AVAILABLE:
            raise RuntimeError("pandas is not installed")

        desc = df.describe(include="all")
        return {
            "summary": desc.to_dict(),
            "shape": df.shape,
            "columns": list(df.columns),
        }

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
