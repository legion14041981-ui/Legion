"""
Legion Database Module - интеграция с Supabase
"""
from supabase import create_client, Client
import os
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class LegionDatabase:
    """Класс для работы с Supabase БД"""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Инициализация подключения к Supabase
        
        Args:
            url: URL проекта Supabase (или из переменной SUPABASE_URL)
            key: API ключ (или из переменной SUPABASE_KEY)
        """
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL и KEY должны быть указаны")
        
        self.client: Client = create_client(self.url, self.key)
        logger.info(f"Connected to Supabase: {self.url}")
    
    def register_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> Dict:
        """Регистрация агента в БД"""
        try:
            response = self.client.table('agents').insert({
                'agent_id': agent_id,
                'name': name,
                'config': config,
                'status': 'Not started'
            }).execute()
            logger.info(f"Agent '{agent_id}' registered in database")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            raise
    
    def update_agent_status(self, agent_id: str, status: str) -> Dict:
        """Обновление статуса агента"""
        response = self.client.table('agents').update({
            'status': status,
            'last_activity': 'now()'
        }).eq('agent_id', agent_id).execute()
        return response.data[0] if response.data else {}
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Получить данные агента"""
        response = self.client.table('agents').select('*').eq('agent_id', agent_id).execute()
        return response.data[0] if response.data else None
    
    def get_all_agents(self) -> List[Dict]:
        """Получить всех агентов"""
        response = self.client.table('agents').select('*').execute()
        return response.data
    
    def create_task(self, task_id: str, agent_id: str, task_data: Dict[str, Any]) -> Dict:
        """Создание задачи"""
        response = self.client.table('tasks').insert({
            'task_id': task_id,
            'agent_id': agent_id,
            'task_data': task_data,
            'status': 'pending'
        }).execute()
        logger.info(f"Task '{task_id}' created for agent '{agent_id}'")
        return response.data[0] if response.data else {}
    
    def update_task_status(self, task_id: str, status: str, result: Optional[Dict] = None) -> Dict:
        """Обновление статуса задачи"""
        update_data = {'status': status}
        if result:
            update_data['result'] = result
        if status == 'completed':
            update_data['completed_at'] = 'now()'
        
        response = self.client.table('tasks').update(update_data).eq('task_id', task_id).execute()
        return response.data[0] if response.data else {}
    
    def get_pending_tasks(self, agent_id: Optional[str] = None) -> List[Dict]:
        """Получить задачи в ожидании"""
        query = self.client.table('tasks').select('*').eq('status', 'pending')
        if agent_id:
            query = query.eq('agent_id', agent_id)
        response = query.execute()
        return response.data
