"""OS Interface - интерфейс взаимодействия с операционной системой.

Обеспечивает:
- Безопасный доступ к файловой системе
- Выполнение системных команд
- Управление процессами
"""

import os
import subprocess
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import shlex

logger = logging.getLogger(__name__)


class OSInterface:
    """Интерфейс взаимодействия с ОС."""
    
    def __init__(self, workspace_root: Path, allowed_commands: Optional[List[str]] = None):
        """
        Инициализация интерфейса.
        
        Args:
            workspace_root: Корневая директория workspace
            allowed_commands: Whitelist разрешенных команд
        """
        self.workspace_root = workspace_root
        self.allowed_commands = allowed_commands or ['ls', 'cat', 'echo', 'pwd']
        logger.info(f"OSInterface initialized with workspace: {workspace_root}")
    
    def read_file(self, filepath: str) -> Optional[str]:
        """
        Прочитать файл.
        
        Args:
            filepath: Путь к файлу
        
        Returns:
            Optional[str]: Содержимое файла или None
        """
        full_path = self.workspace_root / filepath
        
        if not self._validate_path(full_path):
            logger.error(f"Access denied to file: {filepath}")
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Read file: {filepath}")
            return content
        except Exception as e:
            logger.error(f"Failed to read file {filepath}: {e}")
            return None
    
    def write_file(self, filepath: str, content: str) -> bool:
        """
        Записать файл.
        
        Args:
            filepath: Путь к файлу
            content: Содержимое для записи
        
        Returns:
            bool: True если успешно
        """
        full_path = self.workspace_root / filepath
        
        if not self._validate_path(full_path):
            logger.error(f"Access denied to file: {filepath}")
            return False
        
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Wrote file: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to write file {filepath}: {e}")
            return False
    
    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Выполнить системную команду.
        
        Args:
            command: Команда для выполнения
            timeout: Таймаут в секундах
        
        Returns:
            Dict: Результат выполнения
        """
        # Parse command
        try:
            cmd_parts = shlex.split(command)
        except ValueError as e:
            return {'success': False, 'error': f"Invalid command: {e}"}
        
        # Check if command allowed
        if cmd_parts[0] not in self.allowed_commands:
            return {'success': False, 'error': f"Command not allowed: {cmd_parts[0]}"}
        
        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace_root
            )
            
            logger.info(f"Executed command: {command}")
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_files(self, directory: str = '.') -> Optional[List[str]]:
        """
        Получить список файлов в директории.
        
        Args:
            directory: Директория для просмотра
        
        Returns:
            Optional[List[str]]: Список файлов или None
        """
        full_path = self.workspace_root / directory
        
        if not self._validate_path(full_path):
            logger.error(f"Access denied to directory: {directory}")
            return None
        
        try:
            files = [str(p.relative_to(full_path)) for p in full_path.iterdir()]
            return files
        except Exception as e:
            logger.error(f"Failed to list directory {directory}: {e}")
            return None
    
    def _validate_path(self, path: Path) -> bool:
        """
        Валидировать путь (должен быть внутри workspace).
        
        Args:
            path: Путь для проверки
        
        Returns:
            bool: True если путь валиден
        """
        try:
            path.resolve().relative_to(self.workspace_root.resolve())
            return True
        except ValueError:
            return False
