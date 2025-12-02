"""DependencyDoctor — автоматический фикс зависимостей.

Обрабатывает ModuleNotFoundError и устанавливает недостающие пакеты.
"""

import logging
import subprocess
import re
from typing import Optional, Dict, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Whitelist безопасных Python пакетов для автоматической установки
SAFE_PACKAGES: Set[str] = {
    'numpy', 'pandas', 'matplotlib', 'scipy', 'scikit-learn',
    'requests', 'flask', 'django', 'fastapi', 'pydantic',
    'pytest', 'black', 'pylint', 'mypy', 'httpx',
    'aiohttp', 'asyncio', 'uvicorn', 'sqlalchemy',
    'redis', 'celery', 'python-dotenv', 'click'
}


@dataclass
class Patch:
    """Патч для dependency."""
    file: str
    new_content: str  # Renamed from 'diff' for clarity
    risk_level: int
    reason: str
    confidence: float


class DependencyDoctor:
    """Автофикс зависимостей (pip/npm/poetry)."""
    
    def __init__(self, safe_packages: Optional[Set[str]] = None):
        """Initialize DependencyDoctor.
        
        Args:
            safe_packages: Optional custom whitelist of safe packages.
                          If None, uses default SAFE_PACKAGES.
        """
        self.logger = logger
        self.safe_packages = safe_packages or SAFE_PACKAGES
    
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
        
        # Validate package name before processing
        if not self._is_safe_package(module_name):
            logger.warning(
                f"[DependencyDoctor] Package '{module_name}' not in whitelist. "
                f"Manual review required."
            )
            return None
        
        logger.info(f"[DependencyDoctor] Fixing missing module: {module_name}")
        
        # Определяем тип проекта (Python/Node.js)
        if "requirements.txt" in full_tree:
            return self._fix_python_dependency(module_name, full_tree)
        elif "package.json" in full_tree:
            logger.info(
                f"[DependencyDoctor] Node.js project detected. "
                f"Automatic fix not yet supported."
            )
            return None
        
        logger.warning(f"[DependencyDoctor] No dependency file found")
        return None
    
    def _extract_module_name(self, message: str) -> Optional[str]:
        """Извлекает имя модуля из ModuleNotFoundError сообщения.
        
        Args:
            message: Error message text
            
        Returns:
            Module name or None if not found
        """
        match = re.search(r"No module named ['\"](.+?)['\"]|", message)
        if match:
            module_name = match.group(1)
            # Extract base package name (before first dot)
            return module_name.split('.')[0]
        return None
    
    def _is_safe_package(self, package: str) -> bool:
        """Check if package is in whitelist.
        
        Args:
            package: Package name to validate
            
        Returns:
            True if safe to install
        """
        # Normalize package name (lowercase, no special chars)
        normalized = package.lower().replace('-', '').replace('_', '')
        return package in self.safe_packages or normalized in {
            p.lower().replace('-', '').replace('_', '') 
            for p in self.safe_packages
        }
    
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
        
        # Check if already in requirements
        if module in requirements_content:
            logger.info(f"[DependencyDoctor] Module '{module}' already in requirements")
            return None
        
        # Получаем последнюю версию пакета через pip
        version = self._get_latest_version(module)
        
        # Добавляем в requirements
        new_line = f"{module}>={version}" if version else module
        new_content = requirements_content.rstrip() + f"\n{new_line}\n"
        
        return Patch(
            file="requirements.txt",
            new_content=new_content,
            risk_level=1,
            reason=f"Добавлена зависимость: {module}",
            confidence=0.80
        )
    
    def _get_latest_version(self, package: str) -> Optional[str]:
        """
        Получает последнюю версию пакета через pip.
        
        Args:
            package: Имя пакета
        
        Returns:
            Версия или None
        """
        try:
            # SECURITY: Use explicit args list instead of shell=True
            result = subprocess.run(
                ["pip", "index", "versions", package],
                capture_output=True,
                text=True,
                timeout=10,
                check=False  # Don't raise on non-zero exit
            )
            
            if result.returncode != 0:
                logger.warning(
                    f"[DependencyDoctor] pip command failed with code {result.returncode}"
                )
                return None
            
            # Парсим вывод pip
            match = re.search(r"Available versions: (.+?),", result.stdout)
            if match:
                return match.group(1).strip()
        
        except subprocess.TimeoutExpired:
            logger.error(
                f"[DependencyDoctor] Timeout getting version for '{package}'"
            )
        except subprocess.CalledProcessError as e:
            logger.error(
                f"[DependencyDoctor] pip command failed: {e}"
            )
        except Exception as e:
            logger.error(
                f"[DependencyDoctor] Unexpected error getting version: {e}"
            )
        
        return None
