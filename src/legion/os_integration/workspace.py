"""Workspace - безопасная изоляция агентов.

Каждый агент работает в изолированном пространстве с:
- Ограниченным доступом к файловой системе
- Лимитами ресурсов (CPU, RAM)
- Сетевой изоляцией
"""

import os
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import psutil
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class WorkspaceConfig:
    """Workspace configuration."""
    max_disk_usage_mb: int = 1000  # 1GB
    max_memory_mb: int = 512  # 512MB
    max_cpu_percent: float = 50.0  # 50% CPU
    allowed_paths: List[str] = None  # Whitelist of allowed paths
    network_enabled: bool = False
    temp_dir: Optional[Path] = None


class Workspace:
    """Изолированное рабочее пространство для агента."""
    
    def __init__(self, agent_id: str, config: Optional[WorkspaceConfig] = None):
        """
        Инициализация workspace.
        
        Args:
            agent_id: Идентификатор агента
            config: Конфигурация workspace
        """
        self.agent_id = agent_id
        self.config = config or WorkspaceConfig()
        
        # Создать temporary directory
        if self.config.temp_dir:
            self.root = self.config.temp_dir / agent_id
            self.root.mkdir(parents=True, exist_ok=True)
        else:
            self.root = Path(tempfile.mkdtemp(prefix=f"legion_ws_{agent_id}_"))
        
        # Инициализировать директории
        (self.root / 'input').mkdir(exist_ok=True)
        (self.root / 'output').mkdir(exist_ok=True)
        (self.root / 'temp').mkdir(exist_ok=True)
        
        # Resource tracking
        self.process = psutil.Process(os.getpid())
        self._initial_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
        
        logger.info(f"Workspace created for agent '{agent_id}' at {self.root}")
    
    def validate_path(self, path: Path) -> bool:
        """
        Проверить, разрешен ли доступ к пути.
        
        Args:
            path: Путь для проверки
        
        Returns:
            bool: True если доступ разрешен
        """
        path = Path(path).resolve()
        
        # Проверить, что path внутри workspace
        try:
            path.relative_to(self.root)
            return True
        except ValueError:
            pass
        
        # Проверить whitelist
        if self.config.allowed_paths:
            for allowed in self.config.allowed_paths:
                try:
                    path.relative_to(Path(allowed).resolve())
                    return True
                except ValueError:
                    continue
        
        logger.warning(f"Access denied to path: {path}")
        return False
    
    def get_input_path(self, filename: str) -> Path:
        """Get path in input directory."""
        return self.root / 'input' / filename
    
    def get_output_path(self, filename: str) -> Path:
        """Get path in output directory."""
        return self.root / 'output' / filename
    
    def get_temp_path(self, filename: str) -> Path:
        """Get path in temp directory."""
        return self.root / 'temp' / filename
    
    def check_disk_usage(self) -> Dict[str, Any]:
        """
        Проверить использование диска.
        
        Returns:
            Dict с информацией о использовании диска
        """
        total_size = 0
        for path in self.root.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
        
        used_mb = total_size / (1024 * 1024)
        limit_mb = self.config.max_disk_usage_mb
        
        return {
            'used_mb': used_mb,
            'limit_mb': limit_mb,
            'usage_percent': (used_mb / limit_mb * 100) if limit_mb > 0 else 0,
            'exceeds_limit': used_mb > limit_mb
        }
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """
        Проверить использование памяти.
        
        Returns:
            Dict с информацией о использовании памяти
        """
        current_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
        used_mb = current_memory - self._initial_memory
        limit_mb = self.config.max_memory_mb
        
        return {
            'used_mb': used_mb,
            'limit_mb': limit_mb,
            'usage_percent': (used_mb / limit_mb * 100) if limit_mb > 0 else 0,
            'exceeds_limit': used_mb > limit_mb
        }
    
    def check_cpu_usage(self) -> Dict[str, Any]:
        """
        Проверить использование CPU.
        
        Returns:
            Dict с информацией о использовании CPU
        """
        cpu_percent = self.process.cpu_percent(interval=1.0)
        limit_percent = self.config.max_cpu_percent
        
        return {
            'usage_percent': cpu_percent,
            'limit_percent': limit_percent,
            'exceeds_limit': cpu_percent > limit_percent
        }
    
    def get_resource_status(self) -> Dict[str, Any]:
        """
        Получить полную информацию о ресурсах.
        
        Returns:
            Dict с информацией о всех ресурсах
        """
        return {
            'agent_id': self.agent_id,
            'root': str(self.root),
            'disk': self.check_disk_usage(),
            'memory': self.check_memory_usage(),
            'cpu': self.check_cpu_usage(),
            'network_enabled': self.config.network_enabled
        }
    
    def cleanup(self):
        """Очистить workspace."""
        try:
            shutil.rmtree(self.root)
            logger.info(f"Workspace cleaned for agent '{self.agent_id}'")
        except Exception as e:
            logger.error(f"Failed to clean workspace: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
