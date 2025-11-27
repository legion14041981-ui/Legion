"""DependencyDoctor — автоматический фикс зависимостей.

Обрабатывает ModuleNotFoundError и устанавливает недостающие пакеты.
"""

import logging
import subprocess
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Patch:
    """Патч для dependency."""
    file: str
    diff: str
    risk_level: int
    reason: str
    confidence: float


class DependencyDoctor:
    """Автофикс зависимостей (pip/npm/poetry)."""
    
    def __init__(self):
        self.logger = logger
    
    def fix(self, problem, full_tree: Dict[str, str]) -> Optional[Patch]:
        """
        Исправляет ModuleNotFoundError через добавление в requirements.
        
        Args:
            problem: CIProblem с type='module_error'
            full_tree: Полное дерево проекта
        
        Returns:
            Patch для requirements.txt или None
        """
        if problem.type != "module_error":
            return None
        
        # Извлекаем имя модуля
        module_name = self._extract_module_name(problem.message)
        
        if not module_name:
            return None
        
        logger.info(f"[DependencyDoctor] Fixing missing module: {module_name}")
        
        # Определяем тип проекта (Python/Node.js)
        if "requirements.txt" in full_tree:
            return self._fix_python_dependency(module_name, full_tree)
        elif "package.json" in full_tree:
            return self._fix_node_dependency(module_name, full_tree)
        
        logger.warning(f"[DependencyDoctor] No dependency file found")
        return None
    
    def _extract_module_name(self, message: str) -> Optional[str]:
        """Извлекает имя модуля из ModuleNotFoundError сообщения."""
        import re
        match = re.search(r"No module named '(.+?)'", message)
        if match:
            return match.group(1)
        return None
    
    def _fix_python_dependency(self, module: str, tree: Dict) -> Optional[Patch]:
        """
        Добавляет модуль в requirements.txt.
        
        Args:
            module: Имя Python модуля
            tree: Дерево проекта
        
        Returns:
            Patch для requirements.txt
        """
        requirements_content = tree.get("requirements.txt", "")
        
        # Получаем последнюю версию пакета через pip
        version = self._get_latest_version(module)
        
        # Добавляем в requirements
        new_line = f"{module}>={version}" if version else module
        new_content = requirements_content.rstrip() + f"\n{new_line}\n"
        
        # Создаём diff
        diff = f"--- a/requirements.txt\n+++ b/requirements.txt\n@@ -1 +1 @@\n+{new_line}"
        
        return Patch(
            file="requirements.txt",
            diff=new_content,  # Здесь полное содержимое, не diff
            risk_level=1,
            reason=f"Добавлена зависимость: {module}",
            confidence=0.80
        )
    
    def _fix_node_dependency(self, module: str, tree: Dict) -> Optional[Patch]:
        """Добавляет модуль в package.json (npm/yarn)."""
        # TODO: Реализовать для Node.js проектов
        logger.info(f"[DependencyDoctor] Node.js dependency fix not implemented")
        return None
    
    def _get_latest_version(self, package: str) -> Optional[str]:
        """
        Получает последнюю версию пакета через pip.
        
        Args:
            package: Имя пакета
        
        Returns:
            Версия или None
        """
        try:
            result = subprocess.run(
                ["pip", "index", "versions", package],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Парсим вывод pip
            import re
            match = re.search(r"Available versions: (.+?),", result.stdout)
            if match:
                return match.group(1).strip()
        
        except Exception as e:
            logger.error(f"[DependencyDoctor] Failed to get version: {e}")
        
        return None
