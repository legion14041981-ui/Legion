"""
Architecture Registry - immutable реестр архитектур.

Хранит версии архитектур, метрики, provenance.
Каждый snapshot - immutable с semantic hash.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ArchitectureSnapshot:
    """
Immutable snapshot архитектуры.
    """
    semantic_hash: str
    version: str
    config: Dict[str, Any]
    metrics: Dict[str, float]
    provenance: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @staticmethod
    def compute_hash(config: Dict[str, Any]) -> str:
        """Вычислить semantic hash для конфигурации."""
        content = json.dumps(config, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class ArchitectureRegistry:
    """
    Реестр архитектур с immutable storage.
    
    Хранилище: локальная файловая система + опционально DB.
    """
    
    def __init__(self, storage_dir: str = "artifacts/architecture_registry"):
        """
        Инициализация реестра.
        
        Args:
            storage_dir: Директория для хранения snapshots
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ ArchitectureRegistry initialized at {storage_dir}")
    
    def register(
        self,
        version: str,
        config: Dict[str, Any],
        metrics: Dict[str, float],
        provenance: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> ArchitectureSnapshot:
        """
        Зарегистрировать новую архитектуру.
        
        Args:
            version: Версия (напр. '4.0.1')
            config: Конфигурация архитектуры
            metrics: Метрики (accuracy, latency, и т.д.)
            provenance: Информация о происхождении (branch, commit, author)
            tags: Теги (напр. ['production', 'experimental'])
        
        Returns:
            ArchitectureSnapshot
        """
        semantic_hash = ArchitectureSnapshot.compute_hash(config)
        
        # Проверить, есть ли уже такой snapshot
        if self.exists(semantic_hash):
            logger.warning(f"⚠️ Architecture with hash {semantic_hash} already exists")
            return self.get(semantic_hash)
        
        snapshot = ArchitectureSnapshot(
            semantic_hash=semantic_hash,
            version=version,
            config=config,
            metrics=metrics,
            provenance=provenance,
            tags=tags or []
        )
        
        # Сохранить
        self._save_snapshot(snapshot)
        
        logger.info(f"✅ Registered architecture {version} with hash {semantic_hash}")
        return snapshot
    
    def exists(self, semantic_hash: str) -> bool:
        """Проверить, существует ли snapshot."""
        snapshot_file = self.storage_dir / f"{semantic_hash}.json"
        return snapshot_file.exists()
    
    def get(self, semantic_hash: str) -> Optional[ArchitectureSnapshot]:
        """Получить snapshot по hash."""
        snapshot_file = self.storage_dir / f"{semantic_hash}.json"
        if not snapshot_file.exists():
            return None
        
        with open(snapshot_file, 'r') as f:
            data = json.load(f)
        
        return ArchitectureSnapshot(**data)
    
    def list_all(self) -> List[ArchitectureSnapshot]:
        """Получить все snapshots."""
        snapshots = []
        for snapshot_file in self.storage_dir.glob("*.json"):
            with open(snapshot_file, 'r') as f:
                data = json.load(f)
            snapshots.append(ArchitectureSnapshot(**data))
        
        # Сортировать по времени создания
        snapshots.sort(key=lambda x: x.created_at, reverse=True)
        return snapshots
    
    def get_by_tag(self, tag: str) -> List[ArchitectureSnapshot]:
        """Получить snapshots по тегу."""
        all_snapshots = self.list_all()
        return [s for s in all_snapshots if tag in s.tags]
    
    def _save_snapshot(self, snapshot: ArchitectureSnapshot) -> None:
        """Сохранить snapshot на диск."""
        snapshot_file = self.storage_dir / f"{snapshot.semantic_hash}.json"
        with open(snapshot_file, 'w') as f:
            f.write(snapshot.to_json())
        
        logger.debug(f"💾 Snapshot saved: {snapshot_file}")
