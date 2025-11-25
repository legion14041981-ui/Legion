"""Детекторы ошибок из CI-логов.

Поддерживаемые типы ошибок:
- SyntaxError
- ModuleNotFoundError / ImportError
- TypeError / AttributeError
- Test failures (pytest, unittest, jest)
- Merge conflicts
- Linter errors (pylint, flake8, eslint)
"""

import re
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CIProblem:
    """Структура описания проблемы CI."""
    type: str  # syntax_error, module_error, test_failure, merge_conflict, lint_error
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    severity: int = 1  # 0=low, 1=medium, 2=high, 3=critical
    raw_trace: str = ""
    context: Dict = field(default_factory=dict)
    
    def __str__(self):
        return f"{self.type}: {self.message[:60]}... @ {self.file or 'unknown'}:{self.line or '?'}"


class ErrorDetector:
    """Детектор ошибок из CI-логов."""
    
    # Регулярные выражения для детектирования ошибок
    PATTERNS = {
        "syntax_error": [
            r"SyntaxError: (.+?) at (.+?):line (\d+)",
            r"File \"(.+?)\", line (\d+).*?SyntaxError: (.+)",
            r"SyntaxError: (.+)"
        ],
        "module_error": [
            r"ModuleNotFoundError: No module named ['\"](.+?)['\"]",
            r"ImportError: cannot import name ['\"](.+?)['\"]",
            r"Error: Cannot find module ['\"](.+?)['\"]"
        ],
        "type_error": [
            r"TypeError: (.+?) at (.+?):line (\d+)",
            r"AttributeError: (.+?) at (.+?):line (\d+)",
            r"TypeError: (.+)"
        ],
        "test_failure": [
            r"FAILED (.+?) - (.+)",
            r"Test (.+?) failed: (.+)",
            r"(\d+) failed, (\d+) passed",
            r"AssertionError: (.+)"
        ],
        "merge_conflict": [
            r"<<<<<<< HEAD",
            r"CONFLICT \(content\): Merge conflict in (.+)"
        ],
        "lint_error": [
            r"(.+?):(\d+):(\d+): (E\d+) (.+)",  # flake8/pylint
            r"(.+?)\((\d+),(\d+)\): error (.+): (.+)"  # eslint
        ]
    }
    
    SEVERITY_MAP = {
        "syntax_error": 3,      # critical
        "module_error": 2,      # high
        "type_error": 2,        # high
        "test_failure": 1,      # medium
        "merge_conflict": 3,    # critical
        "lint_error": 0         # low
    }
    
    def detect_all(self, logs: str) -> List[CIProblem]:
        """
        Детектирует все проблемы из логов CI.
        
        Args:
            logs: Сырые логи CI
        
        Returns:
            Список обнаруженных проблем
        """
        problems = []
        
        for err_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, logs, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    problem = self._parse_match(err_type, match, logs)
                    if problem:
                        problems.append(problem)
        
        # Дедупликация по message
        seen = set()
        unique_problems = []
        for p in problems:
            key = (p.type, p.message[:50], p.file)
            if key not in seen:
                seen.add(key)
                unique_problems.append(p)
        
        logger.info(f"[ErrorDetector] Found {len(unique_problems)} unique problems")
        return unique_problems
    
    def _parse_match(self, err_type: str, match, logs: str) -> Optional[CIProblem]:
        """
        Парсит regex match в CIProblem.
        
        Args:
            err_type: Тип ошибки
            match: Regex match object
            logs: Полные логи для извлечения контекста
        
        Returns:
            CIProblem или None
        """
        try:
            groups = match.groups()
            
            if err_type == "syntax_error":
                if len(groups) >= 3:
                    file, line, message = groups[0], int(groups[1]), groups[2]
                else:
                    file, line, message = None, None, groups[0] if groups else match.group(0)
            
            elif err_type == "module_error":
                message = f"Module not found: {groups[0]}"
                file, line = self._extract_file_from_context(match.start(), logs)
            
            elif err_type == "type_error":
                if len(groups) >= 3:
                    message, file, line = groups[0], groups[1], int(groups[2])
                else:
                    message, file, line = groups[0] if groups else match.group(0), None, None
            
            elif err_type == "test_failure":
                message = " ".join(str(g) for g in groups if g)
                file, line = self._extract_file_from_context(match.start(), logs)
            
            elif err_type == "merge_conflict":
                message = "Merge conflict detected"
                file = groups[0] if groups else None
                line = None
            
            elif err_type == "lint_error":
                if len(groups) >= 5:
                    file, line, message = groups[0], int(groups[1]), f"{groups[3]}: {groups[4]}"
                else:
                    file, line, message = None, None, match.group(0)
            
            else:
                message = match.group(0)
                file, line = None, None
            
            # Извлекаем контекст (10 строк вокруг)
            raw_trace = self._extract_trace(match.start(), logs)
            
            return CIProblem(
                type=err_type,
                message=message,
                file=file,
                line=line,
                severity=self.SEVERITY_MAP.get(err_type, 1),
                raw_trace=raw_trace
            )
        
        except Exception as e:
            logger.warning(f"[ErrorDetector] Failed to parse {err_type}: {e}")
            return None
    
    def _extract_file_from_context(self, pos: int, logs: str) -> tuple:
        """
        Извлекает имя файла и строку из контекста вокруг позиции.
        
        Args:
            pos: Позиция в логах
            logs: Полные логи
        
        Returns:
            (file, line) или (None, None)
        """
        # Ищем строки вида 'File "path/to/file.py", line 123'
        context = logs[max(0, pos-500):pos+500]
        file_match = re.search(r'File "(.+?)", line (\d+)', context)
        
        if file_match:
            return file_match.group(1), int(file_match.group(2))
        
        # Альтернативный формат: path/to/file.py:123
        alt_match = re.search(r'([\w/.-]+\.py):(\d+)', context)
        if alt_match:
            return alt_match.group(1), int(alt_match.group(2))
        
        return None, None
    
    def _extract_trace(self, pos: int, logs: str, lines: int = 10) -> str:
        """
        Извлекает контекст вокруг позиции ошибки.
        
        Args:
            pos: Позиция в логах
            logs: Полные логи
            lines: Количество строк контекста
        
        Returns:
            Строка с контекстом
        """
        log_lines = logs.splitlines()
        
        # Находим номер строки
        char_count = 0
        line_num = 0
        for i, line in enumerate(log_lines):
            char_count += len(line) + 1  # +1 для \n
            if char_count >= pos:
                line_num = i
                break
        
        # Извлекаем контекст
        start = max(0, line_num - lines // 2)
        end = min(len(log_lines), line_num + lines // 2)
        
        return "\n".join(log_lines[start:end])
