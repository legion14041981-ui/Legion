"""Self-Improvement Engine - long-term memory, continuous learning и AI-powered самооптимизация.

Реализует систему обучения и улучшения агентов:
- Long-term memory (долгосрочная память)
- Pattern recognition (распознавание паттернов)
- Performance optimization (оптимизация производительности)
- Continuous learning
- Анализ производительности агентов
- Автоматическое выявление узких мест
- Генерация рекомендаций по оптимизации
- Применение улучшений в runtime
"""

import json
import logging
import asyncio
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class SelfImprovementEngine:
    """Движок самоулучшения агента.
    
    Сохраняет и анализирует:
    - Успешные/неуспешные действия
    - Производительность разных стратегий
    - Частые паттерны и ошибки
    - Knowledge base для будущих задач
    - Метрики производительности
    - Рекомендации по оптимизации
    
    Attributes:
        agent_id: ID агента
        memory_file: Путь к файлу памяти
        knowledge: База знаний
    """
    
    def __init__(self, agent_id: str, memory_dir: Optional[Path] = None):
        """Инициализировать self-improvement engine.
        
        Args:
            agent_id: Уникальный ID агента
            memory_dir: Директория для памяти
        """
        self.agent_id = agent_id
        
        if memory_dir is None:
            memory_dir = Path.cwd() / 'agent_memory'
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_file = memory_dir / f'{agent_id}_memory.json'
        
        # Структура памяти
        self.knowledge = {
            'successful_actions': [],
            'failed_actions': [],
            'performance_metrics': defaultdict(list),
            'learned_patterns': {},
            'improvement_suggestions': [],
            'optimization_history': [],
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_experiences': 0,
                'optimization_count': 0
            }
        }
        
        # Загрузить существующую память
        self._load_memory()
        
        logger.info(f"🧠 Self-improvement engine initialized for '{agent_id}'")
    
    def record_success(self, action: str, context: Dict[str, Any], result: Any):
        """Записать успешное действие.
        
        Args:
            action: Название действия
            context: Контекст выполнения
            result: Результат
        """
        experience = {
            'action': action,
            'context': context,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        self.knowledge['successful_actions'].append(experience)
        self.knowledge['metadata']['total_experiences'] += 1
        self._save_memory()
        
        logger.debug(f"✅ Success recorded: {action}")
    
    def record_failure(self, action: str, context: Dict[str, Any], error: str):
        """Записать неуспешное действие.
        
        Args:
            action: Название действия
            context: Контекст
            error: Описание ошибки
        """
        experience = {
            'action': action,
            'context': context,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        
        self.knowledge['failed_actions'].append(experience)
        self.knowledge['metadata']['total_experiences'] += 1
        self._save_memory()
        
        logger.debug(f"❌ Failure recorded: {action} - {error}")
    
    def record_performance(self, metric_name: str, value: float, context: Dict = None):
        """Записать метрику производительности.
        
        Args:
            metric_name: Название метрики
            value: Значение
            context: Контекст
        """
        metric = {
            'value': value,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.knowledge['performance_metrics'][metric_name].append(metric)
        self._save_memory()
        
        logger.debug(f"📊 Performance metric: {metric_name}={value}")
    
    def learn_pattern(self, pattern_name: str, pattern_data: Dict[str, Any]):
        """Сохранить распознанный паттерн.
        
        Args:
            pattern_name: Название паттерна
            pattern_data: Данные паттерна
        """
        self.knowledge['learned_patterns'][pattern_name] = {
            'data': pattern_data,
            'learned_at': datetime.now().isoformat(),
            'usage_count': 0
        }
        self._save_memory()
        
        logger.info(f"🎯 Pattern learned: {pattern_name}")
    
    def get_pattern(self, pattern_name: str) -> Optional[Dict]:
        """Получить сохранённый паттерн.
        
        Args:
            pattern_name: Название паттерна
        
        Returns:
            Optional[Dict]: Данные паттерна или None
        """
        pattern = self.knowledge['learned_patterns'].get(pattern_name)
        if pattern:
            pattern['usage_count'] += 1
            self._save_memory()
        return pattern
    
    def suggest_improvement(self, suggestion: str, priority: str = 'medium'):
        """Добавить предложение по улучшению.
        
        Args:
            suggestion: Текст предложения
            priority: Приоритет (low/medium/high)
        """
        improvement = {
            'suggestion': suggestion,
            'priority': priority,
            'suggested_at': datetime.now().isoformat(),
            'applied': False
        }
        
        self.knowledge['improvement_suggestions'].append(improvement)
        self._save_memory()
        
        logger.info(f"💡 Improvement suggested: {suggestion}")
    
    def apply_optimization(self, optimization: Dict[str, Any]):
        """Применить оптимизацию.
        
        Args:
            optimization: Описание оптимизации
        """
        optimization['applied_at'] = datetime.now().isoformat()
        self.knowledge['optimization_history'].append(optimization)
        self.knowledge['metadata']['optimization_count'] += 1
        self._save_memory()
        
        logger.info(f"🚀 Optimization applied: {optimization.get('description', 'Unknown')}")
    
    def analyze_performance(self, metric_name: str, window_hours: int = 24) -> Dict[str, Any]:
        """Анализ производительности за период.
        
        Args:
            metric_name: Название метрики
            window_hours: Окно анализа в часах
        
        Returns:
            Dict: Статистика производительности
        """
        metrics = self.knowledge['performance_metrics'].get(metric_name, [])
        
        if not metrics:
            return {'error': 'No metrics found'}
        
        # Фильтр по времени
        cutoff = datetime.now() - timedelta(hours=window_hours)
        recent_metrics = [
            m for m in metrics
            if datetime.fromisoformat(m['timestamp']) > cutoff
        ]
        
        if not recent_metrics:
            return {'error': 'No recent metrics'}
        
        values = [m['value'] for m in recent_metrics]
        
        return {
            'metric_name': metric_name,
            'count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'stdev': statistics.stdev(values) if len(values) > 1 else 0,
            'min': min(values),
            'max': max(values),
            'window_hours': window_hours
        }
    
    def get_success_rate(self, action: str = None) -> float:
        """Рассчитать success rate.
        
        Args:
            action: Конкретное действие (если None - общий)
        
        Returns:
            float: Success rate (0.0 - 1.0)
        """
        successes = self.knowledge['successful_actions']
        failures = self.knowledge['failed_actions']
        
        if action:
            successes = [s for s in successes if s['action'] == action]
            failures = [f for f in failures if f['action'] == action]
        
        total = len(successes) + len(failures)
        if total == 0:
            return 0.0
        
        return len(successes) / total
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику.
        
        Returns:
            Dict: Статистика обучения
        """
        return {
            'agent_id': self.agent_id,
            'total_experiences': self.knowledge['metadata']['total_experiences'],
            'success_count': len(self.knowledge['successful_actions']),
            'failure_count': len(self.knowledge['failed_actions']),
            'success_rate': self.get_success_rate(),
            'patterns_learned': len(self.knowledge['learned_patterns']),
            'improvements_suggested': len(self.knowledge['improvement_suggestions']),
            'optimizations_applied': self.knowledge['metadata']['optimization_count']
        }
    
    def _load_memory(self):
        """Загрузить память из файла."""
        if self.memory_file.exists():
            try:
                data = json.loads(self.memory_file.read_text(encoding='utf-8'))
                self.knowledge.update(data)
                # Преобразовать performance_metrics обратно в defaultdict
                self.knowledge['performance_metrics'] = defaultdict(
                    list,
                    self.knowledge.get('performance_metrics', {})
                )
                logger.info(f"📚 Memory loaded: {self.knowledge['metadata']['total_experiences']} experiences")
            except Exception as e:
                logger.error(f"❌ Failed to load memory: {e}")
    
    def _save_memory(self):
        """Сохранить память в файл."""
        try:
            self.knowledge['metadata']['last_updated'] = datetime.now().isoformat()
            # Преобразовать defaultdict в обычный dict для JSON
            data = dict(self.knowledge)
            data['performance_metrics'] = dict(data['performance_metrics'])
            
            self.memory_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"❌ Failed to save memory: {e}")
