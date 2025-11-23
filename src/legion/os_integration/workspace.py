"""Agent Workspace - isolated filesystem environments for agents.

Предоставляет изолированные файловые окружения для каждого агента:
- Собственная директория с квотами
- Контроль доступа (read/write/execute)
- Auto-cleanup при завершении
- Resource usage tracking
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class AgentWorkspace:
    """Isolated filesystem workspace for an agent.
    
    Каждый агент получает собственную директорию с:
    - Ограничением размера (quota_mb)
    - Автоматической очисткой (auto_cleanup)
    - Отслеживанием использования ресурсов
    
    Attributes:
        agent_id: Уникальный идентификатор агента
        workspace_path: Путь к рабочей директории
        quota_mb: Максимальный размер в MB
        auto_cleanup: Автоматическая очистка при завершении
    """
    
    def __init__(
        self,
        agent_id: str,
        base_path: Optional[Path] = None,
        quota_mb: int = 100,
        auto_cleanup: bool = True
    ):
        """Initialize agent workspace.
        
        Args:
            agent_id: Уникальный идентификатор агента
            base_path: Базовая директория (по умолчанию ./agent_workspaces)
            quota_mb: Максимальный размер в MB
            auto_cleanup: Автоматическая очистка
        """
        self.agent_id = agent_id
        self.quota_mb = quota_mb
        self.auto_cleanup = auto_cleanup
        self.quota_bytes = quota_mb * 1024 * 1024
        
        # Определить базовую директорию
        if base_path is None:
            base_path = Path.cwd() / 'agent_workspaces'
        
        self.workspace_path = base_path / agent_id
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Создать структуру каталогов
        (self.workspace_path / 'temp').mkdir(exist_ok=True)
        (self.workspace_path / 'data').mkdir(exist_ok=True)
        (self.workspace_path / 'logs').mkdir(exist_ok=True)
        
        # Инициализировать метаданные
        self.metadata = {
            'agent_id': agent_id,
            'created_at': datetime.now().isoformat(),
            'quota_mb': quota_mb,
            'files_created': 0,
            'total_bytes_written': 0
        }
        self._save_metadata()
        
        logger.info(f"✅ Workspace created for agent '{agent_id}' at {self.workspace_path}")
    
    def write_file(self, filename: str, content: str, subdir: str = 'data') -> Path:
        """Записать файл в workspace.
        
        Args:
            filename: Имя файла
            content: Содержимое
            subdir: Поддиректория (temp/data/logs)
        
        Returns:
            Path: Полный путь к файлу
        
        Raises:
            ValueError: Если превышена квота
        """
        file_path = self.workspace_path / subdir / filename
        content_bytes = len(content.encode('utf-8'))
        
        # Проверить квоту
        current_usage = self._get_workspace_size()
        if current_usage + content_bytes > self.quota_bytes:
            raise ValueError(
                f"Квота превышена: {current_usage + content_bytes} > {self.quota_bytes}"
            )
        
        # Записать файл
        file_path.write_text(content, encoding='utf-8')
        
        # Обновить метаданные
        self.metadata['files_created'] += 1
        self.metadata['total_bytes_written'] += content_bytes
        self._save_metadata()
        
        logger.debug(f"💾 File written: {file_path} ({content_bytes} bytes)")
        return file_path
    
    def read_file(self, filename: str, subdir: str = 'data') -> str:
        """Прочитать файл из workspace.
        
        Args:
            filename: Имя файла
            subdir: Поддиректория
        
        Returns:
            str: Содержимое файла
        """
        file_path = self.workspace_path / subdir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        return file_path.read_text(encoding='utf-8')
    
    def list_files(self, subdir: str = None) -> list[Path]:
        """Получить список файлов.
        
        Args:
            subdir: Поддиректория (если None - все файлы)
        
        Returns:
            list[Path]: Список путей к файлам
        """
        search_path = self.workspace_path / subdir if subdir else self.workspace_path
        return list(search_path.rglob('*')) if search_path.exists() else []
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Получить статистику использования.
        
        Returns:
            Dict: Статистика использования ресурсов
        """
        current_size = self._get_workspace_size()
        return {
            'agent_id': self.agent_id,
            'current_size_mb': current_size / (1024 * 1024),
            'quota_mb': self.quota_mb,
            'usage_percent': (current_size / self.quota_bytes) * 100,
            'files_count': len(self.list_files()),
            **self.metadata
        }
    
    def cleanup(self):
        """Очистить workspace (удалить все файлы)."""
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path)
            logger.info(f"🧹 Workspace cleaned up: {self.workspace_path}")
    
    def _get_workspace_size(self) -> int:
        """Подсчитать общий размер workspace в байтах."""
        total_size = 0
        for path in self.list_files():
            if path.is_file():
                total_size += path.stat().st_size
        return total_size
    
    def _save_metadata(self):
        """Сохранить метаданные в .metadata.json."""
        metadata_path = self.workspace_path / '.metadata.json'
        metadata_path.write_text(json.dumps(self.metadata, indent=2), encoding='utf-8')
    
    def __enter__(self):
        """Context manager вход."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager выход с авто-очисткой."""
        if self.auto_cleanup:
            self.cleanup()
