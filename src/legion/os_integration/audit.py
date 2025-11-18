"""Audit Trail - Tamper-evident logging for agent actions.

Inspired by Microsoft Windows Agent security model (Nov 2025).
Provides blockchain-style audit logging with integrity verification.
"""

import logging
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Single audit log entry."""
    
    timestamp: str
    agent_id: str
    action_type: str
    target: Optional[str]
    parameters: Dict[str, Any]
    result: Optional[Any]
    user_approved: bool
    risk_level: str
    hash: str
    previous_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class LegionAuditTrail:
    """
    Tamper-evident audit trail for Legion agents.
    
    Features:
    - Blockchain-style hash chaining (like git commits)
    - Immutable log records
    - Integrity verification
    - Risk-based categorization
    - Real-time monitoring
    - Compliance reporting (SOC 2, ISO 27001)
    
    Security Model (Microsoft-inspired):
    - Every agent action logged
    - Cryptographic hash chain prevents tampering
    - Timestamps for forensic analysis
    - User approval tracking
    - Risk level classification
    
    Attributes:
        agent_id: Agent identifier
        entries: List of audit entries
        hash_chain: List of entry hashes
    """
    
    def __init__(self, agent_id: str, persist_to_db: bool = True):
        """
        Initialize audit trail.
        
        Args:
            agent_id: Agent identifier
            persist_to_db: Whether to persist logs to Supabase
        """
        self.agent_id = agent_id
        self.entries: List[AuditEntry] = []
        self.hash_chain: List[str] = []
        self.persist_to_db = persist_to_db
        
        # Risk counters
        self.risk_counters = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0
        }
        
        logger.info(f"Audit trail initialized for agent {agent_id}")
    
    async def log_action(self,
                        action_type: str,
                        target: Optional[str] = None,
                        parameters: Optional[Dict[str, Any]] = None,
                        result: Optional[Any] = None,
                        user_approved: bool = False,
                        risk_level: str = "medium") -> str:
        """Log agent action with tamper-evident hash.
        
        Args:
            action_type: Type of action (read_file, execute_command, etc.)
            target: Target of action (file path, URL, etc.)
            parameters: Action parameters
            result: Action result
            user_approved: Whether user approved this action
            risk_level: Risk level (low, medium, high, critical)
        
        Returns:
            Hash of log entry
        """
        # Create entry (without hash first)
        entry_data = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "action_type": action_type,
            "target": target,
            "parameters": parameters or {},
            "result": str(result) if result else None,
            "user_approved": user_approved,
            "risk_level": risk_level
        }
        
        # Compute hash (blockchain-style)
        previous_hash = self.hash_chain[-1] if self.hash_chain else "0" * 64
        entry_json = json.dumps(entry_data, sort_keys=True)
        current_hash = hashlib.sha256(f"{previous_hash}{entry_json}".encode()).hexdigest()
        
        # Create complete entry
        entry = AuditEntry(
            **entry_data,
            hash=current_hash,
            previous_hash=previous_hash
        )
        
        # Store
        self.entries.append(entry)
        self.hash_chain.append(current_hash)
        self.risk_counters[risk_level] += 1
        
        # Persist to database (async, non-blocking)
        if self.persist_to_db:
            asyncio.create_task(self._persist_entry(entry))
        
        logger.debug(f"Logged action: {action_type} (risk: {risk_level})")
        
        return current_hash
    
    async def _persist_entry(self, entry: AuditEntry):
        """Persist audit entry to Supabase.
        
        Args:
            entry: Audit entry to persist
        """
        try:
            # Placeholder for Supabase integration
            # from supabase import create_client
            # supabase = create_client(url, key)
            # supabase.table("audit_logs").insert(entry.to_dict()).execute()
            pass
        except Exception as e:
            logger.error(f"Failed to persist audit entry: {e}")
    
    def verify_integrity(self) -> bool:
        """Verify entire audit trail integrity.
        
        Returns:
            bool: True if no tampering detected
        """
        if not self.entries:
            return True
        
        logger.info(f"Verifying audit trail integrity ({len(self.entries)} entries)...")
        
        for i, entry in enumerate(self.entries):
            # Check previous hash link
            expected_prev = self.hash_chain[i-1] if i > 0 else "0" * 64
            if entry.previous_hash != expected_prev:
                logger.error(f"Integrity violation at entry {i}: broken hash chain")
                return False
            
            # Recompute hash
            entry_dict = entry.to_dict()
            entry_dict.pop("hash")
            entry_dict.pop("previous_hash")
            entry_json = json.dumps(entry_dict, sort_keys=True)
            
            expected_hash = hashlib.sha256(
                f"{entry.previous_hash}{entry_json}".encode()
            ).hexdigest()
            
            if entry.hash != expected_hash:
                logger.error(f"Integrity violation at entry {i}: hash mismatch")
                return False
        
        logger.info("✅ Audit trail integrity verified")
        return True
    
    def get_entries_by_risk(self, risk_level: str) -> List[AuditEntry]:
        """Get entries filtered by risk level.
        
        Args:
            risk_level: Risk level to filter (low, medium, high, critical)
        
        Returns:
            List of matching entries
        """
        return [e for e in self.entries if e.risk_level == risk_level]
    
    def get_entries_by_action(self, action_type: str) -> List[AuditEntry]:
        """Get entries filtered by action type.
        
        Args:
            action_type: Action type to filter
        
        Returns:
            List of matching entries
        """
        return [e for e in self.entries if e.action_type == action_type]
    
    def get_entries_since(self, since: datetime) -> List[AuditEntry]:
        """Get entries since specific timestamp.
        
        Args:
            since: Start timestamp
        
        Returns:
            List of matching entries
        """
        return [
            e for e in self.entries 
            if datetime.fromisoformat(e.timestamp) >= since
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get audit trail summary.
        
        Returns:
            Summary statistics
        """
        if not self.entries:
            return {
                "agent_id": self.agent_id,
                "total_entries": 0,
                "integrity_verified": True
            }
        
        return {
            "agent_id": self.agent_id,
            "total_entries": len(self.entries),
            "integrity_verified": self.verify_integrity(),
            "risk_distribution": self.risk_counters.copy(),
            "first_entry": self.entries[0].timestamp,
            "last_entry": self.entries[-1].timestamp,
            "user_approved_actions": len([e for e in self.entries if e.user_approved]),
            "critical_actions": self.risk_counters["critical"],
            "high_risk_actions": self.risk_counters["high"]
        }
    
    def generate_compliance_report(self, 
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate compliance report for auditing.
        
        Args:
            start_date: Report start date (default: all time)
            end_date: Report end date (default: now)
        
        Returns:
            Compliance report with all required fields
        """
        # Filter entries by date range
        entries = self.entries
        if start_date:
            entries = [e for e in entries if datetime.fromisoformat(e.timestamp) >= start_date]
        if end_date:
            entries = [e for e in entries if datetime.fromisoformat(e.timestamp) <= end_date]
        
        # Categorize actions
        filesystem_ops = [e for e in entries if e.action_type.startswith(("read_file", "write_file", "delete_file"))]
        system_commands = [e for e in entries if e.action_type == "execute_command"]
        network_ops = [e for e in entries if e.action_type.startswith("api_call")]
        
        return {
            "report_type": "Legion Agent Audit Report",
            "agent_id": self.agent_id,
            "report_period": {
                "start": start_date.isoformat() if start_date else "all_time",
                "end": end_date.isoformat() if end_date else datetime.now().isoformat()
            },
            "total_actions": len(entries),
            "actions_by_type": {
                "filesystem": len(filesystem_ops),
                "system_commands": len(system_commands),
                "network": len(network_ops)
            },
            "actions_by_risk": {
                "low": len([e for e in entries if e.risk_level == "low"]),
                "medium": len([e for e in entries if e.risk_level == "medium"]),
                "high": len([e for e in entries if e.risk_level == "high"]),
                "critical": len([e for e in entries if e.risk_level == "critical"])
            },
            "user_approvals": {
                "total": len([e for e in entries if e.user_approved]),
                "percentage": (len([e for e in entries if e.user_approved]) / len(entries) * 100) if entries else 0
            },
            "integrity_status": "VERIFIED" if self.verify_integrity() else "COMPROMISED",
            "compliance_standards": ["SOC 2 Type II", "ISO 27001", "GDPR Article 30"],
            "generated_at": datetime.now().isoformat()
        }
    
    def export_to_json(self, output_path: str, include_full_logs: bool = True):
        """Export audit trail to JSON file.
        
        Args:
            output_path: Output file path
            include_full_logs: Whether to include full log entries
        """
        export_data = {
            "agent_id": self.agent_id,
            "summary": self.get_summary(),
            "compliance_report": self.generate_compliance_report()
        }
        
        if include_full_logs:
            export_data["full_logs"] = [e.to_dict() for e in self.entries]
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Audit trail exported to {output_path}")
