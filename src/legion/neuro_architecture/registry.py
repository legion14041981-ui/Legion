"""
Architecture Registry - immutable реестр с криптографической защитой.

Вдохновлён BIP32 (Bitcoin Improvement Proposal):
- Hierarchical Deterministic derivation
- Checksum validation
- Semantic hashing
- Опционально: IPFS для distributed storage
"""

import hashlib
import hmac
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
    Immutable snapshot архитектуры с криптографической защитой.
    """
    semantic_hash: str  # 16-byte hex
    checksum: str  # 8-byte hex (last 8 chars of SHA-256)
    version: str  # Hierarchical path (e.g., "v4/0.92/45")
    config: Dict[str, Any]
    metrics: Dict[str, float]
    provenance: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = field(default_factory=list)
    ipfs_cid: Optional[str] = None  # IPFS Content Identifier
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def verify_integrity(self) -> bool:
        """
        Проверить целостность snapshot.
        
        Returns:
            True если checksum valid
        """
        recomputed_hash = ArchitectureSnapshot.compute_hash(self.config)
        expected_checksum = hashlib.sha256(bytes.fromhex(recomputed_hash)).hexdigest()[:8]
        
        valid = self.checksum == expected_checksum
        if not valid:
            logger.error(f"❌ Integrity check failed for {self.semantic_hash}")
            logger.error(f"   Expected checksum: {expected_checksum}")
            logger.error(f"   Actual checksum: {self.checksum}")
        
        return valid
    
    @staticmethod
    def compute_hash(config: Dict[str, Any]) -> str:
        """
        Вычислить semantic hash для конфигурации.
        
        Args:
            config: Конфигурация
        
        Returns:
            32-byte hex hash
        """
        content = json.dumps(config, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class ArchitectureRegistry:
    """
    Реестр архитектур с криптографической защитой.
    
    Особенности:
    - BIP32-style hierarchical derivation
    - Checksum validation (аналог Bitcoin seed phrase)
    - Immutable storage
    - Опционально: IPFS integration
    """
    
    DERIVATION_SALT = b"legion-v4-ultra-orchestrator"
    
    def __init__(
        self,
        storage_dir: str = "artifacts/architecture_registry",
        ipfs_enabled: bool = False
    ):
        """
        Инициализация реестра.
        
        Args:
            storage_dir: Директория для хранения snapshots
            ipfs_enabled: Включить IPFS storage
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.ipfs_enabled = ipfs_enabled
        
        if ipfs_enabled:
            self._init_ipfs()
        
        logger.info(f"✅ ArchitectureRegistry initialized at {storage_dir}")
        if ipfs_enabled:
            logger.info("   IPFS integration: enabled")
    
    def _init_ipfs(self) -> None:
        """Инициализировать IPFS клиент."""
        try:
            import ipfshttpclient
            self.ipfs_client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
            logger.info("✅ IPFS client connected")
        except Exception as e:
            logger.warning(f"⚠️ IPFS not available: {e}")
            self.ipfs_enabled = False
    
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
            version: Версия (напр. 'v4/0.92/45')
            config: Конфигурация архитектуры
            metrics: Метрики
            provenance: Provenance metadata
            tags: Теги
        
        Returns:
            ArchitectureSnapshot
        """
        # 1. Генерация seed hash
        config_json = json.dumps(config, sort_keys=True)
        seed = hashlib.sha256(config_json.encode()).digest()
        
        # 2. BIP32-style derivation
        derived_key = self._derive_key(seed, version)
        semantic_hash = derived_key.hex()[:16]  # First 16 bytes
        
        # 3. Checksum (последние 8 символов SHA-256 derived key)
        checksum = hashlib.sha256(derived_key).hexdigest()[:8]
        
        # Проверить, есть ли уже
        if self.exists(semantic_hash):
            logger.warning(f"⚠️ Architecture with hash {semantic_hash} already exists")
            return self.get(semantic_hash)
        
        # 4. Создать snapshot
        snapshot = ArchitectureSnapshot(
            semantic_hash=semantic_hash,
            checksum=checksum,
            version=version,
            config=config,
            metrics=metrics,
            provenance=provenance,
            tags=tags or []
        )
        
        # 5. IPFS upload (если включено)
        if self.ipfs_enabled:
            snapshot.ipfs_cid = self._upload_to_ipfs(snapshot)
        
        # 6. Сохранить локально
        self._save_snapshot(snapshot)
        
        logger.info(f"✅ Registered architecture {version}")
        logger.info(f"   Hash: {semantic_hash}")
        logger.info(f"   Checksum: {checksum}")
        if snapshot.ipfs_cid:
            logger.info(f"   IPFS CID: {snapshot.ipfs_cid}")
        
        return snapshot
    
    def _derive_key(self, seed: bytes, path: str) -> bytes:
        """
        BIP32-style hierarchical key derivation.
        
        Args:
            seed: 32-byte seed
            path: Derivation path (e.g., 'v4/0.92/45')
        
        Returns:
            32-byte derived key
        """
        # Master key
        key = hmac.new(self.DERIVATION_SALT, seed, hashlib.sha512).digest()
        
        # Derive for each path segment
        for segment in path.split('/'):
            key = hmac.new(key, segment.encode(), hashlib.sha512).digest()
        
        return key[:32]  # Use first 32 bytes
    
    def _upload_to_ipfs(self, snapshot: ArchitectureSnapshot) -> str:
        """
        Загрузить snapshot в IPFS.
        
        Args:
            snapshot: ArchitectureSnapshot
        
        Returns:
            IPFS CID
        """
        try:
            content = snapshot.to_json()
            result = self.ipfs_client.add_str(content)
            return result
        except Exception as e:
            logger.error(f"❌ IPFS upload failed: {e}")
            return None
    
    def exists(self, semantic_hash: str) -> bool:
        """Проверить, существует ли snapshot."""
        snapshot_file = self.storage_dir / f"{semantic_hash}.json"
        return snapshot_file.exists()
    
    def get(self, semantic_hash: str) -> Optional[ArchitectureSnapshot]:
        """
        Получить snapshot по hash.
        
        Args:
            semantic_hash: Semantic hash
        
        Returns:
            ArchitectureSnapshot или None
        """
        snapshot_file = self.storage_dir / f"{semantic_hash}.json"
        if not snapshot_file.exists():
            logger.warning(f"⚠️ Snapshot {semantic_hash} not found locally")
            
            # Попробовать загрузить из IPFS
            if self.ipfs_enabled:
                # TODO: Implement IPFS retrieval
                pass
            
            return None
        
        with open(snapshot_file, 'r') as f:
            data = json.load(f)
        
        snapshot = ArchitectureSnapshot(**data)
        
        # Проверить целостность
        if not snapshot.verify_integrity():
            logger.error(f"❌ Snapshot {semantic_hash} failed integrity check")
            return None
        
        return snapshot
    
    def list_all(self, verify_integrity: bool = False) -> List[ArchitectureSnapshot]:
        """
        Получить все snapshots.
        
        Args:
            verify_integrity: Проверять целостность
        
        Returns:
            Список ArchitectureSnapshot
        """
        snapshots = []
        for snapshot_file in self.storage_dir.glob("*.json"):
            with open(snapshot_file, 'r') as f:
                data = json.load(f)
            snapshot = ArchitectureSnapshot(**data)
            
            if verify_integrity:
                if not snapshot.verify_integrity():
                    logger.warning(f"⚠️ Skipping corrupted snapshot: {snapshot.semantic_hash}")
                    continue
            
            snapshots.append(snapshot)
        
        # Сортировать по времени
        snapshots.sort(key=lambda x: x.created_at, reverse=True)
        return snapshots
    
    def get_by_tag(self, tag: str) -> List[ArchitectureSnapshot]:
        """Получить snapshots по тегу."""
        all_snapshots = self.list_all()
        return [s for s in all_snapshots if tag in s.tags]
    
    def restore_snapshot(self, semantic_hash: str) -> Optional[Dict[str, Any]]:
        """
        Восстановить архитектуру из snapshot.
        
        Args:
            semantic_hash: Hash snapshot
        
        Returns:
            Конфигурация или None
        """
        snapshot = self.get(semantic_hash)
        if not snapshot:
            logger.error(f"❌ Cannot restore: snapshot {semantic_hash} not found")
            return None
        
        logger.info(f"🔄 Restoring architecture from {semantic_hash}")
        logger.info(f"   Version: {snapshot.version}")
        logger.info(f"   Metrics: {snapshot.metrics}")
        
        return snapshot.config
    
    def _save_snapshot(self, snapshot: ArchitectureSnapshot) -> None:
        """Сохранить snapshot на диск."""
        snapshot_file = self.storage_dir / f"{snapshot.semantic_hash}.json"
        with open(snapshot_file, 'w') as f:
            f.write(snapshot.to_json())
        
        logger.debug(f"💾 Snapshot saved: {snapshot_file}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику реестра."""
        all_snapshots = self.list_all()
        
        tags_count = {}
        for snapshot in all_snapshots:
            for tag in snapshot.tags:
                tags_count[tag] = tags_count.get(tag, 0) + 1
        
        return {
            'total_snapshots': len(all_snapshots),
            'tags': tags_count,
            'latest_snapshot': all_snapshots[0].to_dict() if all_snapshots else None,
            'ipfs_enabled': self.ipfs_enabled
        }
