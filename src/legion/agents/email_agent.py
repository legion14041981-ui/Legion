"""
EmailAgent - специализированный агент для работы с email.

Поддерживает:
- Отправку email через SMTP
- Шаблоны писем
- Вложения
- HTML и plain text
- Массовую рассылку с ограничением rate
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import asyncio
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from ..agents import LegionAgent

from logging_config import get_agent_logger


class EmailAgent(LegionAgent):
    """
    Агент для отправки email сообщений.
    
    Использует SMTP для отправки писем с поддержкой:
    - HTML и plain text форматов
    - Вложений
    - Шаблонов
    - Rate limiting для массовых рассылок
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str = "EmailAgent",
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
        from_email: Optional[str] = None,
        max_tasks: int = 10
    ):
        """
        Инициализация EmailAgent.
        
        Args:
            agent_id: Уникальный ID агента
            name: Имя агента
            smtp_host: SMTP сервер (по умолчанию из EMAIL_SMTP_HOST)
            smtp_port: SMTP порт (по умолчанию из EMAIL_SMTP_PORT или 587)
            smtp_user: Логин SMTP (по умолчанию из EMAIL_SMTP_USER)
            smtp_password: Пароль SMTP (по умолчанию из EMAIL_SMTP_PASSWORD)
            use_tls: Использовать TLS
            from_email: Email отправителя (по умолчанию из EMAIL_FROM)
            max_tasks: Максимум задач одновременно
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["email_send", "email_template", "email_bulk"],
            max_tasks=max_tasks
        )
        
        # SMTP настройки
        self.smtp_host = smtp_host or os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("EMAIL_SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("EMAIL_SMTP_PASSWORD")
        self.use_tls = use_tls
        self.from_email = from_email or os.getenv("EMAIL_FROM", self.smtp_user)
        
        # Logging
        self.logger = get_agent_logger(name)
        
        # Статистика
        self.emails_sent = 0
        self.emails_failed = 0
        
        self.logger.info(f"EmailAgent инициализирован: {name} ({agent_id})")
        self.logger.debug(f"SMTP: {self.smtp_host}:{self.smtp_port}, From: {self.from_email}")
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Отправка email сообщения.
        
        Args:
            to: Email получателя
            subject: Тема письма
            body: Текст письма
            html: True если body в HTML формате
            cc: Список CC получателей
            bcc: Список BCC получателей
            attachments: Список путей к файлам для вложения
        
        Returns:
            Dict с результатом отправки
        """
        try:
            self.logger.info(f"Отправка email: {to}, тема: {subject}")
            
            # Создаём сообщение
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            # Добавляем тело письма
            mime_subtype = 'html' if html else 'plain'
            msg.attach(MIMEText(body, mime_subtype, 'utf-8'))
            
            # Добавляем вложения
            if attachments:
                for file_path in attachments:
                    self._attach_file(msg, file_path)
            
            # Отправка через SMTP
            await self._send_via_smtp(msg, to, cc, bcc)
            
            self.emails_sent += 1
            self.logger.info(f"✓ Email отправлен успешно: {to}")
            
            return {
                "success": True,
                "to": to,
                "subject": subject,
                "sent_at": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            self.emails_failed += 1
            self.logger.error(f"✗ Ошибка отправки email: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to
            }
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Добавление файла как вложение."""
        try:
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                
                filename = Path(file_path).name
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
                
            self.logger.debug(f"Добавлено вложение: {filename}")
        except Exception as e:
            self.logger.error(f"Ошибка добавления вложения {file_path}: {e}")
    
    async def _send_via_smtp(
        self,
        msg: MIMEMultipart,
        to: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ):
        """Отправка сообщения через SMTP."""
        # Выполняем в отдельном потоке чтобы не блокировать event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._smtp_send, msg, to, cc, bcc)
    
    def _smtp_send(
        self,
        msg: MIMEMultipart,
        to: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ):
        """Синхронная отправка через SMTP."""
        server = None
        try:
            # Подключение к SMTP серверу
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.ehlo()
            
            if self.use_tls:
                server.starttls()
                server.ehlo()
            
            # Авторизация
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            
            # Список всех получателей
            recipients = [to]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Отправка
            server.send_message(msg, self.from_email, recipients)
            
        finally:
            if server:
                server.quit()
    
    async def send_bulk(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html: bool = False,
        delay_seconds: float = 1.0
    ) -> Dict[str, Any]:
        """
        Массовая рассылка с rate limiting.
        
        Args:
            recipients: Список email получателей
            subject: Тема письма
            body: Текст письма
            html: HTML формат
            delay_seconds: Задержка между отправками
        
        Returns:
            Dict со статистикой рассылки
        """
        self.logger.info(f"Массовая рассылка: {len(recipients)} получателей")
        
        results = {
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "errors": []
        }
        
        for email in recipients:
            result = await self.send_email(email, subject, body, html)
            
            if result["success"]:
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "email": email,
                    "error": result.get("error")
                })
            
            # Rate limiting
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
        
        self.logger.info(
            f"Рассылка завершена: {results['sent']}/{results['total']} отправлено"
        )
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику агента."""
        base_stats = super().get_status()
        base_stats.update({
            "emails_sent": self.emails_sent,
            "emails_failed": self.emails_failed,
            "success_rate": (
                self.emails_sent / (self.emails_sent + self.emails_failed) * 100
                if (self.emails_sent + self.emails_failed) > 0
                else 0
            )
        })
        return base_stats


# Пример использования
if __name__ == "__main__":
    async def test_email_agent():
        """Тестирование EmailAgent."""
        from logging_config import setup_logging
        
        logger = setup_logging("EmailAgentTest", "INFO")
        logger.info("Тест EmailAgent")
        
        # Создание агента
        agent = EmailAgent(
            agent_id="email_001",
            name="TestEmailAgent",
            max_tasks=5
        )
        
        agent.start()
        logger.info("Агент запущен")
        
        # Проверка статуса
        stats = agent.get_stats()
        logger.info(f"Статистика: {stats}")
        
        # Для реальной отправки нужны SMTP credentials в .env
        logger.info("Для отправки email установите переменные:")
        logger.info("  EMAIL_SMTP_HOST, EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD")
        
        agent.stop()
        logger.info("Агент остановлен")
    
    asyncio.run(test_email_agent())
