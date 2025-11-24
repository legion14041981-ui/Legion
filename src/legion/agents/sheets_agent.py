"""
GoogleSheetsAgent - агент для работы с Google Sheets.

Поддерживает:
- Чтение данных из таблиц
- Запись данных в таблицы  
- Обновление ячеек
- Форматирование
- Batch операции
"""

import os
from typing import List, Dict, Any, Optional
import asyncio
from pathlib import Path

try:
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials
except ImportError:
    print("WARNING: google-api-python-client not installed")
    print("Install with: pip install google-api-python-client google-auth")

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# FIXED: Changed from `fro..base_agent import LegionAgent` to relative import
from ..base_agent import LegionAgent
from logging_config import get_agent_logger


class GoogleSheetsAgent(LegionAgent):
    """
    Агент для работы с Google Sheets API.
    
    Использует Service Account для авторизации.
    Поддерживает чтение, запись, обновление данных.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(
        self,
        agent_id: str,
        name: str = "GoogleSheetsAgent",
        credentials_file: Optional[str] = None,
        max_tasks: int = 5
    ):
        """
        Инициализация GoogleSheetsAgent.
        
        Args:
            agent_id: Уникальный ID агента
            name: Имя агента
            credentials_file: Путь к JSON файлу Service Account
            max_tasks: Максимум задач одновременно
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["sheets_read", "sheets_write", "sheets_update", "sheets_format"],
            max_tasks=max_tasks
        )
        
        self.credentials_file = credentials_file or os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        self.service = None
        self.logger = get_agent_logger(name)
        
        # Статистика
        self.reads = 0
        self.writes = 0
        self.updates = 0
        
        self.logger.info(f"GoogleSheetsAgent инициализирован: {name} ({agent_id})")
        
        # Инициализация API
        self._init_service()
    
    def _init_service(self):
        """Инициализация Google Sheets API service."""
        try:
            if not self.credentials_file:
                self.logger.warning("Credentials file не указан. Укажите GOOGLE_SHEETS_CREDENTIALS")
                return
            
            if not Path(self.credentials_file).exists():
                self.logger.error(f"Credentials file не найден: {self.credentials_file}")
                return
            
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.SCOPES
            )
            self.service = build('sheets', 'v4', credentials=creds)
            self.logger.info("✓ Google Sheets API инициализирован")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации Google Sheets API: {e}")
    
    async def read_range(
        self,
        spreadsheet_id: str,
        range_name: str
    ) -> Dict[str, Any]:
        """
        Чтение данных из указанного диапазона.
        
        Args:
            spreadsheet_id: ID таблицы Google Sheets
            range_name: Диапазон в формате A1 (например, "Sheet1!A1:D10")
        
        Returns:
            Dict с данными и метаинформацией
        """
        try:
            self.logger.info(f"Чтение диапазона: {range_name} из {spreadsheet_id}")
            
            if not self.service:
                return {"success": False, "error": "Service не инициализирован"}
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name
                ).execute()
            )
            
            values = result.get('values', [])
            self.reads += 1
            
            self.logger.info(f"✓ Прочитано {len(values)} строк")
            
            return {
                "success": True,
                "values": values,
                "range": result.get('range'),
                "majorDimension": result.get('majorDimension'),
                "rows": len(values)
            }
            
        except Exception as e:
            self.logger.error(f"✗ Ошибка чтения: {e}")
            return {"success": False, "error": str(e)}
    
    async def write_range(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED"
    ) -> Dict[str, Any]:
        """
        Запись данных в указанный диапазон.
        
        Args:
            spreadsheet_id: ID таблицы
            range_name: Диапазон в формате A1
            values: Двумерный массив значений
            value_input_option: Как интерпретировать данные (USER_ENTERED или RAW)
        
        Returns:
            Dict с результатом операции
        """
        try:
            self.logger.info(f"Запись в диапазон: {range_name}")
            
            if not self.service:
                return {"success": False, "error": "Service не инициализирован"}
            
            body = {'values': values}
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    body=body
                ).execute()
            )
            
            self.writes += 1
            
            self.logger.info(f"✓ Записано {result.get('updatedCells')} ячеек")
            
            return {
                "success": True,
                "updatedRange": result.get('updatedRange'),
                "updatedRows": result.get('updatedRows'),
                "updatedColumns": result.get('updatedColumns'),
                "updatedCells": result.get('updatedCells')
            }
            
        except Exception as e:
            self.logger.error(f"✗ Ошибка записи: {e}")
            return {"success": False, "error": str(e)}
    
    async def append_rows(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED"
    ) -> Dict[str, Any]:
        """
        Добавление строк в конец таблицы.
        
        Args:
            spreadsheet_id: ID таблицы
            range_name: Диапазон (обычно имя листа, например "Sheet1")
            values: Массив строк для добавления
            value_input_option: Как интерпретировать данные
        
        Returns:
            Dict с результатом
        """
        try:
            self.logger.info(f"Добавление {len(values)} строк в {range_name}")
            
            if not self.service:
                return {"success": False, "error": "Service не инициализирован"}
            
            body = {'values': values}
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    insertDataOption='INSERT_ROWS',
                    body=body
                ).execute()
            )
            
            self.writes += 1
            
            self.logger.info(f"✓ Добавлено {result.get('updates', {}).get('updatedRows')} строк")
            
            return {
                "success": True,
                "updates": result.get('updates'),
                "updatedRange": result.get('updates', {}).get('updatedRange')
            }
            
        except Exception as e:
            self.logger.error(f"✗ Ошибка добавления строк: {e}")
            return {"success": False, "error": str(e)}
    
    async def batch_update(
        self,
        spreadsheet_id: str,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Batch обновление нескольких диапазонов.
        
        Args:
            spreadsheet_id: ID таблицы
            data: Список словарей с range и values
                  Например: [{"range": "Sheet1!A1", "values": [[1, 2]]}]
        
        Returns:
            Dict с результатом операции
        """
        try:
            self.logger.info(f"Batch update: {len(data)} диапазонов")
            
            if not self.service:
                return {"success": False, "error": "Service не инициализирован"}
            
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': data
            }
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets().values().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=body
                ).execute()
            )
            
            self.updates += 1
            
            total_cells = result.get('totalUpdatedCells', 0)
            self.logger.info(f"✓ Обновлено {total_cells} ячеек")
            
            return {
                "success": True,
                "totalUpdatedRows": result.get('totalUpdatedRows'),
                "totalUpdatedColumns": result.get('totalUpdatedColumns'),
                "totalUpdatedCells": total_cells,
                "responses": result.get('responses')
            }
            
        except Exception as e:
            self.logger.error(f"✗ Ошибка batch update: {e}")
            return {"success": False, "error": str(e)}
    
    async def clear_range(
        self,
        spreadsheet_id: str,
        range_name: str
    ) -> Dict[str, Any]:
        """
        Очистка содержимого диапазона.
        
        Args:
            spreadsheet_id: ID таблицы
            range_name: Диапазон для очистки
        
        Returns:
            Dict с результатом
        """
        try:
            self.logger.info(f"Очистка диапазона: {range_name}")
            
            if not self.service:
                return {"success": False, "error": "Service не инициализирован"}
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets().values().clear(
                    spreadsheetId=spreadsheet_id,
                    range=range_name
                ).execute()
            )
            
            self.logger.info(f"✓ Диапазон очищен: {result.get('clearedRange')}")
            
            return {
                "success": True,
                "clearedRange": result.get('clearedRange')
            }
            
        except Exception as e:
            self.logger.error(f"✗ Ошибка очистки: {e}")
            return {"success": False, "error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику агента."""
        base_stats = super().get_status()
        base_stats.update({
            "reads": self.reads,
            "writes": self.writes,
            "updates": self.updates,
            "total_operations": self.reads + self.writes + self.updates
        })
        return base_stats


# Пример использования
if __name__ == "__main__":
    async def test_sheets_agent():
        """Тестирование GoogleSheetsAgent."""
        from logging_config import setup_logging
        
        logger = setup_logging("SheetsAgentTest", "INFO")
        logger.info("Тест GoogleSheetsAgent")
        
        # Создание агента
        agent = GoogleSheetsAgent(
            agent_id="sheets_001",
            name="TestSheetsAgent"
        )
        
        agent.start()
        logger.info("Агент запущен")
        
        # Проверка статуса
        stats = agent.get_stats()
        logger.info(f"Статистика: {stats}")
        
        # Для работы нужен credentials file
        logger.info("Для работы с Google Sheets:")
        logger.info("1. Создайте Service Account в Google Cloud Console")
        logger.info("2. Скачайте JSON файл credentials")
        logger.info("3. Установите GOOGLE_SHEETS_CREDENTIALS=/path/to/credentials.json")
        logger.info("4. Дайте Service Account доступ к таблице")
        
        agent.stop()
        logger.info("Агент остановлен")
    
    asyncio.run(test_sheets_agent())
