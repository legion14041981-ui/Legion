"""ErrorDetector — детектор ошибок из CI-логов.

Анализирует сырые логи CI/CD и извлекает структурированные ошибки.
"""

import re
import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CIProblem:
    """Структура описания проблемы CI."""
    type: str  # syntax_error, module_error, test_failure, merge_conflict
    message: str
    file: Optional[str]
    line: Optional[int]
    severity: int  # 0=low, 1=medium, 2=high, 3=critical
    raw_trace: str
    context: dict = None


class ErrorDetector:
    """Детектор ошибок из CI-логов."""
    
    # Regex паттерны для различных типов ошибок
    PATTERNS = {
        "syntax_error": r"SyntaxError: (.+?) at line (\d+)",
        "module_error": r"ModuleNotFoundError: No module named '(.+?)'",
        "import_error": r"ImportError: cannot import name '(.+?)'",
        "type_error": r"TypeError: (.+?) at (.+?):(\d+)",
        "test_failure": r"FAILED (.+?) - (.+)",
        "merge_conflict": r"<<<<<<< HEAD",
        "assertion_error": r"AssertionError: (.+)",
        "attribute_error": r"AttributeError: (.+?) has no attribute '(.+?)'",
        "key_error": r"KeyError: '(.+?)'",
        "value_error": r"ValueError: (.+)"
    }
    
    # Карта severity для типов ошибок
    SEVERITY_MAP = {
        "syntax_error": 3,        # Critical
        "module_error": 2,        # High
        "import_error": 2,        # High
        "type_error": 2,          # High
        "test_failure": 1,        # Medium
        "merge_conflict": 3,      # Critical
        "assertion_error": 1,     # Medium
        "attribute_error": 2,     # High
        "key_error": 1,           # Medium
        "value_error": 1          # Medium
    }
    
    def detect_all(self, logs: str) -> List[CIProblem]:
        """
        Детектирует все проблемы из логов.
        
        Args:
            logs: Сырые логи CI
        
        Returns:
            Список CIProblem
        """
        problems = []
        
        for err_type, pattern in self.PATTERNS.items():
            matches = re.finditer(pattern, logs, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                problem = self._parse_match(err_type, match, logs)
                if problem:
                    problems.append(problem)
                    logger.debug(f"[ErrorDetector] Found {err_type}: {problem.message[:80]}")
        
        # Дедупликация
        problems = self._deduplicate(problems)
        
        logger.info(f"[ErrorDetector] Total problems detected: {len(problems)}")
        return problems
    
    def _parse_match(self, err_type: str, match, logs: str) -> Optional[CIProblem]:
        """
        Парсит regex match в CIProblem.
        
        Args:
            err_type: Тип ошибки
            match: re.Match объект
            logs: Полные логи для контекста
        
        Returns:
            CIProblem или None
        """
        try:
            # Извлекаем filename и line из traceback (если есть)
            file_path, line_num = self._extract_file_info(match, logs)
            
            return CIProblem(
                type=err_type,
                message=match.group(0),
                file=file_path,
                line=line_num,
                severity=self.SEVERITY_MAP.get(err_type, 1),
                raw_trace=self._extract_context(match, logs, context_lines=10)
            )
        except Exception as e:
            logger.error(f"[ErrorDetector] Failed to parse match: {e}")
            return None
    
    def _extract_file_info(self, match, logs: str) -> tuple:
        """
        Извлекает путь к файлу и номер строки из traceback.
        
        Returns:
            (file_path, line_number) или (None, None)
        """
        # Ищем traceback паттерн вида: File "path/to/file.py", line 123
        traceback_pattern = r'File "([^"]+)", line (\d+)'
        
        # Ищем в контексте вокруг match
        context_start = max(0, match.start() - 500)
        context_end = min(len(logs), match.end() + 500)
        context = logs[context_start:context_end]
        
        tb_match = re.search(traceback_pattern, context)
        if tb_match:
            return tb_match.group(1), int(tb_match.group(2))
        
        return None, None
    
    def _extract_context(self, match, logs: str, context_lines: int = 10) -> str:
        """
        Извлекает контекст вокруг ошибки (N строк до и после).
        
        Args:
            match: re.Match объект
            logs: Полные логи
            context_lines: Число строк контекста
        
        Returns:
            Текст контекста
        """
        lines = logs[:match.end()].splitlines()
        start_idx = max(0, len(lines) - context_lines)
        
        context = "\n".join(lines[start_idx:])
        return context[-1000:]  # Ограничиваем длину
    
    def _deduplicate(self, problems: List[CIProblem]) -> List[CIProblem]:
        """
        Удаляет дубликаты ошибок.
        
        Args:
            problems: Список проблем
        
        Returns:
            Дедуплицированный список
        """
        seen = set()
        unique = []
        
        for problem in problems:
            # Создаём ключ для дедупликации
            key = (problem.type, problem.message, problem.file, problem.line)
            
            if key not in seen:
                seen.add(key)
                unique.append(problem)
        
        return unique
