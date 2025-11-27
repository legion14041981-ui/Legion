"""PatchEngine — генератор минимальных патчей для исправления ошибок.

Использует AST-анализ для точного патчинга кода.
"""

import ast
import difflib
import logging
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Patch:
    """Unified diff патч."""
    file: str
    diff: str
    risk_level: int  # 0-3
    reason: str
    confidence: float
    old_sha: Optional[str] = None


class PatchEngine:
    """AST-based генератор патчей."""
    
    def __init__(self):
        self.logger = logger
    
    def generate(
        self,
        problem,
        context_files: Dict[str, str],
        risk_limit: int = 1
    ) -> Optional[Patch]:
        """
        Генерирует минимальный unified diff для проблемы.
        
        Args:
            problem: CIProblem объект
            context_files: Релевантные файлы {path: content}
            risk_limit: Максимальный допустимый risk level
        
        Returns:
            Patch объект или None
        """
        if problem.type == "syntax_error":
            return self._fix_syntax(problem, context_files)
        
        elif problem.type == "import_error":
            return self._fix_import(problem, context_files)
        
        elif problem.type == "module_error":
            # DependencyDoctor обрабатывает отдельно
            return None
        
        # Fallback: generic fix attempt
        return self._generic_fix(problem, context_files, risk_limit)
    
    def _fix_syntax(self, problem, files: Dict) -> Optional[Patch]:
        """
        AST-based фикс SyntaxError.
        
        Стратегия:
        1. Парсим файл до ошибки
        2. Определяем тип синтаксической ошибки
        3. Применяем автофикс (например, добавление :, ), ])
        """
        if not problem.file or problem.file not in files:
            return None
        
        content = files[problem.file]
        lines = content.splitlines()
        
        if not problem.line or problem.line > len(lines):
            return None
        
        error_line_idx = problem.line - 1
        error_line = lines[error_line_idx]
        
        # Простые автофиксы
        fixed_line = self._apply_syntax_fixes(error_line, problem.message)
        
        if fixed_line != error_line:
            # Создаём unified diff
            lines[error_line_idx] = fixed_line
            new_content = "\n".join(lines)
            
            diff = self._create_unified_diff(
                content,
                new_content,
                problem.file
            )
            
            return Patch(
                file=problem.file,
                diff=diff,
                risk_level=0,  # Minimal risk
                reason=f"SyntaxError фикс: {problem.message[:50]}",
                confidence=0.85
            )
        
        return None
    
    def _apply_syntax_fixes(self, line: str, error_msg: str) -> str:
        """
        Применяет простые синтаксические фиксы.
        
        Args:
            line: Строка кода с ошибкой
            error_msg: Сообщение об ошибке
        
        Returns:
            Исправленная строка
        """
        # Missing colon
        if "expected ':'" in error_msg.lower():
            if line.rstrip().endswith(("if", "else", "elif", "for", "while", "def", "class")):
                return line.rstrip() + ":"
        
        # Unclosed bracket
        if "unclosed" in error_msg.lower():
            open_count = line.count("(")
            close_count = line.count(")")
            if open_count > close_count:
                return line.rstrip() + ")" * (open_count - close_count)
        
        # Missing quotes
        if "unterminated string" in error_msg.lower():
            if line.count('"') % 2 != 0:
                return line.rstrip() + '"'
            if line.count("'") % 2 != 0:
                return line.rstrip() + "'"
        
        return line
    
    def _fix_import(self, problem, files: Dict) -> Optional[Patch]:
        """
        Фикс ImportError через добавление недостающего импорта.
        
        Стратегия:
        1. Определяем, что не импортировано
        2. Находим файл, где используется
        3. Добавляем import в начало файла
        """
        # Извлекаем имя модуля из сообщения
        import_name = self._extract_import_name(problem.message)
        
        if not import_name or not problem.file:
            return None
        
        if problem.file not in files:
            return None
        
        content = files[problem.file]
        lines = content.splitlines()
        
        # Ищем последнюю строку с импортом
        import_line_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ")):
                import_line_idx = i
        
        # Добавляем новый импорт
        new_import = f"from typing import {import_name}"
        lines.insert(import_line_idx + 1, new_import)
        
        new_content = "\n".join(lines)
        diff = self._create_unified_diff(content, new_content, problem.file)
        
        return Patch(
            file=problem.file,
            diff=diff,
            risk_level=0,
            reason=f"Добавлен импорт: {import_name}",
            confidence=0.90
        )
    
    def _extract_import_name(self, message: str) -> Optional[str]:
        """Извлекает имя модуля из ImportError сообщения."""
        import re
        match = re.search(r"cannot import name '(.+?)'", message)
        if match:
            return match.group(1)
        return None
    
    def _generic_fix(self, problem, files: Dict, risk_limit: int) -> Optional[Patch]:
        """
        Generic фикс через LLM (placeholder).
        
        В production здесь будет интеграция с LegionAISystem.ask()
        для генерации патчей через LLM.
        """
        # TODO: Интеграция с LLM
        logger.warning(f"[PatchEngine] Generic fix not implemented for {problem.type}")
        return None
    
    def _create_unified_diff(self, old: str, new: str, filename: str) -> str:
        """
        Создаёт unified diff между old и new содержимым.
        
        Args:
            old: Старое содержимое
            new: Новое содержимое
            filename: Имя файла
        
        Returns:
            Unified diff строка
        """
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=""
        )
        
        return "".join(diff)
    
    def apply_diff(self, original: str, diff: str) -> str:
        """
        Применяет unified diff к оригинальному содержимому.
        
        Args:
            original: Оригинальное содержимое
            diff: Unified diff
        
        Returns:
            Патченное содержимое
        """
        # Простой парсер unified diff
        lines = original.splitlines()
        
        for line in diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                # Добавляем строку
                lines.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                # Удаляем строку (упрощённо)
                content = line[1:]
                if content in lines:
                    lines.remove(content)
        
        return "\n".join(lines)
