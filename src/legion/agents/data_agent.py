# -*- coding: utf-8 -*-
"""
DataAgent - агент для обработки и трансформации данных

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

from ..base_agent import LegionAgent


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
        **kwargs
    ):
        super().__init__(agent_id, name, description, **kwargs)
        
        # Определяем доступные capabilities
        self.capabilities = [
            "data_parse_json",
            "data_parse_csv",
            "data_parse_xml",
            "data_filter",
            "data_transform",
            "data_aggregate",
            "data_validate",
            "data_statistics"
        ]
        
        # Статистика операций
        self.operations_count = 0
        self.parse_count = 0
        self.transform_count = 0
        self.validation_count = 0
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполняет операцию обработки данных.
        
        Args:
            task: Словарь с параметрами задачи
                - capability: Тип операции
                - data: Данные для обработки
                - options: Дополнительные параметры
        
        Returns:
            Результат выполнения операции
        """
        self.operations_count += 1
        capability = task.get('capability')
        data = task.get('data')
        options = task.get('options', {})
        
        try:
            if capability == 'data_parse_json':
                result = await self._parse_json(data, options)
            elif capability == 'data_parse_csv':
                result = await self._parse_csv(data, options)
            elif capability == 'data_parse_xml':
                result = await self._parse_xml(data, options)
            elif capability == 'data_filter':
                result = await self._filter_data(data, options)
            elif capability == 'data_transform':
                result = await self._transform_data(data, options)
            elif capability == 'data_aggregate':
                result = await self._aggregate_data(data, options)
            elif capability == 'data_validate':
                result = await self._validate_data(data, options)
            elif capability == 'data_statistics':
                result = await self._calculate_statistics(data, options)
            else:
                return {'success': False, 'error': f'Unknown capability: {capability}'}
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            logging.error(f"DataAgent error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _parse_json(self, data: Union[str, dict], options: Dict) -> Any:
        """Парсинг JSON"""
        self.parse_count += 1
        if isinstance(data, str):
            return json.loads(data)
        return data
    
    async def _parse_csv(self, data: str, options: Dict) -> List[Dict]:
        """Парсинг CSV"""
        self.parse_count += 1
        delimiter = options.get('delimiter', ',')
        reader = csv.DictReader(StringIO(data), delimiter=delimiter)
        return list(reader)
    
    async def _parse_xml(self, data: str, options: Dict) -> Dict:
        """Парсинг XML"""
        self.parse_count += 1
        root = ET.fromstring(data)
        return self._xml_to_dict(root)
    
    def _xml_to_dict(self, element) -> Dict:
        result = {element.tag: {}}
        if element.attrib:
            result[element.tag]['@attributes'] = element.attrib
        if element.text and element.text.strip():
            result[element.tag]['#text'] = element.text.strip()
        for child in element:
            child_data = self._xml_to_dict(child)
            result[element.tag].update(child_data)
        return result
    
    async def _filter_data(self, data: List[Dict], options: Dict) -> List[Dict]:
        """Фильтрация данных"""
        self.transform_count += 1
        filters = options.get('filters', {})
        result = data
        for key, value in filters.items():
            result = [item for item in result if item.get(key) == value]
        return result
    
    async def _transform_data(self, data: List[Dict], options: Dict) -> List[Dict]:
        """Трансформация данных"""
        self.transform_count += 1
        fields = options.get('fields')
        sort_by = options.get('sort_by')
        limit = options.get('limit')
        
        result = data
        if fields:
            result = [{k: item.get(k) for k in fields} for item in result]
        if sort_by:
            result = sorted(result, key=lambda x: x.get(sort_by, ''))
        if limit:
            result = result[:limit]
        return result
    
    async def _aggregate_data(self, data: List[Dict], options: Dict) -> Dict:
        """Агрегация данных"""
        self.transform_count += 1
        group_by = options.get('group_by')
        aggregate_field = options.get('field')
        operation = options.get('operation', 'count')
        
        if not group_by:
            return {'error': 'group_by required'}
        
        groups = {}
        for item in data:
            key = item.get(group_by)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        
        result = {}
        for key, items in groups.items():
            if operation == 'count':
                result[key] = len(items)
            elif operation == 'sum' and aggregate_field:
                result[key] = sum(float(item.get(aggregate_field, 0)) for item in items)
            elif operation == 'avg' and aggregate_field:
                result[key] = sum(float(item.get(aggregate_field, 0)) for item in items) / len(items)
        
        return result
    
    async def _validate_data(self, data: List[Dict], options: Dict) -> Dict:
        """Валидация данных"""
        self.validation_count += 1
        schema = options.get('schema', {})
        required_fields = options.get('required_fields', [])
        
        errors = []
        for idx, item in enumerate(data):
            for field in required_fields:
                if field not in item:
                    errors.append(f"Row {idx}: missing field '{field}'")
            
            for field, rules in schema.items():
                if field in item:
                    value = item[field]
                    if 'type' in rules:
                        expected_type = rules['type']
                        if expected_type == 'int' and not isinstance(value, int):
                            try:
                                int(value)
                            except:
                                errors.append(f"Row {idx}: {field} is not int")
        
        return {'valid': len(errors) == 0, 'errors': errors, 'checked': len(data)}
    
    async def _calculate_statistics(self, data: List[Dict], options: Dict) -> Dict:
        """Расчёт статистики"""
        field = options.get('field')
        if not field:
            return {'count': len(data)}
        
        values = [float(item.get(field, 0)) for item in data if field in item]
        if not values:
            return {'error': 'No numeric values found'}
        
        return {
            'count': len(values),
            'sum': sum(values),
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values)
        }
    
    @property
    def stats(self) -> Dict:
        """Возвращает статистику агента"""
        return {
            'operations_count': self.operations_count,
            'parse_count': self.parse_count,
            'transform_count': self.transform_count,
            'validation_count': self.validation_count
        }
