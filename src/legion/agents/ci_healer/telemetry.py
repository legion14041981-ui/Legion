"""Telemetry — логирование и уведомления.

Отправляет логи в Slack и S3.
"""

import json
import logging
import requests
from datetime import datetime
from typing import List, Optional

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

logger = logging.getLogger(__name__)


class Telemetry:
    """Модуль телеметрии для CI-Healer."""
    
    def __init__(
        self,
        slack_webhook: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        enabled: bool = True
    ):
        self.enabled = enabled
        self.slack_webhook = slack_webhook
        self.s3_bucket = s3_bucket
        
        if enabled and s3_bucket and HAS_BOTO3:
            self.s3_client = boto3.client('s3')
        else:
            self.s3_client = None
        
        self.session_data = {
            "started_at": datetime.now().isoformat(),
            "iterations": []
        }
    
    def log_iteration(self, iteration: int, problem, patch, logs_snippet: str):
        """Логирует итерацию healing-процесса."""
        if not self.enabled:
            return
        
        iteration_data = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "problem": {
                "type": problem.type,
                "message": problem.message,
                "file": problem.file,
                "severity": problem.severity
            },
            "patch": {
                "file": patch.file,
                "risk_level": patch.risk_level,
                "confidence": patch.confidence,
                "reason": patch.reason
            },
            "logs_snippet": logs_snippet
        }
        
        self.session_data["iterations"].append(iteration_data)
        logger.info(f"[Telemetry] Logged iteration {iteration}")
    
    def send_slack(self, message: str, patches: Optional[List] = None):
        """Отправляет уведомление в Slack."""
        if not self.enabled or not self.slack_webhook:
            return
        
        try:
            payload = {"text": message}
            
            if patches:
                attachments = []
                for patch in patches:
                    attachments.append({
                        "color": self._risk_color(patch.risk_level),
                        "fields": [
                            {"title": "File", "value": patch.file, "short": True},
                            {"title": "Risk", "value": str(patch.risk_level), "short": True},
                            {"title": "Reason", "value": patch.reason, "short": False}
                        ]
                    })
                payload["attachments"] = attachments
            
            response = requests.post(
                self.slack_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info("[Telemetry] Slack notification sent")
        
        except Exception as e:
            logger.error(f"[Telemetry] Failed to send Slack: {e}")
    
    def upload_to_s3(self, session_key: Optional[str] = None):
        """Загружает полный отчёт о сессии в S3."""
        if not self.enabled or not self.s3_client or not self.s3_bucket:
            return
        
        try:
            key = session_key or f"ci-healer/{datetime.now().isoformat()}.json"
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=json.dumps(self.session_data, ensure_ascii=False, indent=2),
                ContentType="application/json"
            )
            
            logger.info(f"[Telemetry] Uploaded to S3: s3://{self.s3_bucket}/{key}")
        
        except Exception as e:
            logger.error(f"[Telemetry] Failed to upload to S3: {e}")
    
    def _risk_color(self, level: int) -> str:
        """Цвет для Slack attachment."""
        colors = {0: "good", 1: "#36a64f", 2: "warning", 3: "danger"}
        return colors.get(level, "good")
