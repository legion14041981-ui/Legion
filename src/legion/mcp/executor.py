"""Code Execution Engine - безопасное выполнение кода в sandbox.

Предоставляет изолированную среду для выполнения сгенерированного AI кода
с контролем доступа, timeout и валидацией.
"""

import logging
import asyncio
from typing import Any, Dict, Optional
from RestrictedPython import compile_restricted, safe_globals
import sys
from io import StringIO

logger = logging.getLogger(__name__)


class CodeExecutionEngine:
    """Движок безопасного выполнения кода.
    
    Использует RestrictedPython для изоляции выполнения и предотвращения
    небезопасных операций (file I/O, network, system calls).
    
    Attributes:
        tool_registry: Реестр доступных инструментов
        timeout: Максимальное время выполнения (секунды)
        max_iterations: Максимум итераций в циклах
    """
    
    def __init__(self, tool_registry: Any, timeout: int = 30, max_iterations: int = 10000):
        """Инициализация движка выполнения.
        
        Args:
            tool_registry: LegionToolRegistry для доступа к инструментам
            timeout: Максимальное время выполнения (сек)
            max_iterations: Ограничение на количество итераций
        """
        self.tool_registry = tool_registry
        self.timeout = timeout
        self.max_iterations = max_iterations
        logger.info(f"CodeExecutionEngine initialized (timeout={timeout}s)")
    
    def _prepare_safe_globals(self) -> Dict[str, Any]:
        """Подготовить безопасное глобальное окружение.
        
        Returns:
            Словарь с разрешёнными глобальными объектами
        """
        # Базовые безопасные глобальные объекты
        safe_env = safe_globals.copy()
        
        # Добавить доступ к инструментам через tools proxy
        class ToolsProxy:
            def __init__(self, registry):
                self.registry = registry
            
            async def execute(self, tool_name: str, **kwargs):
                """Вызов инструмента через реестр."""
                return await self.registry.execute(tool_name, **kwargs)
            
            def list(self, category: Optional[str] = None):
                """Список доступных инструментов."""
                return [t.name for t in self.registry.list_tools(category)]
        
        safe_env['tools'] = ToolsProxy(self.tool_registry)
        
        # Добавить базовые безопасные библиотеки
        safe_env['__builtins__'] = {
            'print': print,
            'len': len,
            'range': range,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'True': True,
            'False': False,
            'None': None,
        }
        
        return safe_env
    
    async def execute(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Выполнить код в безопасном окружении.
        
        Args:
            code: Python код для выполнения
            context: Дополнительный контекст (переменные)
            
        Returns:
            Результат выполнения:
            {
                'success': bool,
                'result': Any,
                'output': str,
                'error': Optional[str]
            }
        """
        logger.info("Executing code in sandbox...")
        logger.debug(f"Code length: {len(code)} chars")
        
        try:
            # Компиляция с RestrictedPython
            byte_code = compile_restricted(
                code,
                filename='<sandbox>',
                mode='exec'
            )
            
            # Проверка на ошибки компиляции
            if byte_code.errors:
                error_msg = "\n".join(byte_code.errors)
                logger.error(f"Compilation errors: {error_msg}")
                return {
                    'success': False,
                    'result': None,
                    'output': '',
                    'error': f"Compilation error: {error_msg}"
                }
            
            # Подготовка окружения
            safe_env = self._prepare_safe_globals()
            
            # Добавить контекст пользователя
            if context:
                safe_env.update(context)
            
            # Захват вывода
            stdout_capture = StringIO()
            old_stdout = sys.stdout
            sys.stdout = stdout_capture
            
            result = None
            try:
                # Выполнение с timeout
                exec_task = asyncio.create_task(
                    asyncio.to_thread(exec, byte_code.code, safe_env)
                )
                
                await asyncio.wait_for(exec_task, timeout=self.timeout)
                
                # Попытка получить результат (если есть переменная 'result')
                result = safe_env.get('result')
                
                output = stdout_capture.getvalue()
                logger.info("Code executed successfully")
                
                return {
                    'success': True,
                    'result': result,
                    'output': output,
                    'error': None
                }
                
            except asyncio.TimeoutError:
                logger.error(f"Execution timeout ({self.timeout}s)")
                return {
                    'success': False,
                    'result': None,
                    'output': stdout_capture.getvalue(),
                    'error': f"Execution timeout ({self.timeout}s)"
                }
            
            except Exception as e:
                logger.error(f"Execution error: {e}")
                return {
                    'success': False,
                    'result': None,
                    'output': stdout_capture.getvalue(),
                    'error': str(e)
                }
            
            finally:
                # Восстановить stdout
                sys.stdout = old_stdout
        
        except Exception as e:
            logger.error(f"Sandbox error: {e}")
            return {
                'success': False,
                'result': None,
                'output': '',
                'error': f"Sandbox error: {str(e)}"
            }
    
    async def execute_script(
        self,
        script_path: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Выполнить скрипт из файла.
        
        Args:
            script_path: Путь к Python файлу
            context: Дополнительный контекст
            
        Returns:
            Результат выполнения
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            return await self.execute(code, context)
        
        except FileNotFoundError:
            logger.error(f"Script file not found: {script_path}")
            return {
                'success': False,
                'result': None,
                'output': '',
                'error': f"File not found: {script_path}"
            }
        except Exception as e:
            logger.error(f"Error reading script: {e}")
            return {
                'success': False,
                'result': None,
                'output': '',
                'error': f"Error reading script: {str(e)}"
            }
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """Валидация кода перед выполнением.
        
        Args:
            code: Python код
            
        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        errors = []
        warnings = []
        
        # Компиляция для проверки синтаксиса
        try:
            byte_code = compile_restricted(
                code,
                filename='<validation>',
                mode='exec'
            )
            
            if byte_code.errors:
                errors.extend(byte_code.errors)
            
            if byte_code.warnings:
                warnings.extend(byte_code.warnings)
        
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
        except Exception as e:
            errors.append(f"Compilation error: {str(e)}")
        
        # Дополнительные проверки
        forbidden_imports = ['os', 'sys', 'subprocess', 'socket', 'requests']
        for forbidden in forbidden_imports:
            if f"import {forbidden}" in code or f"from {forbidden}" in code:
                warnings.append(f"Potentially unsafe import: {forbidden}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def __repr__(self) -> str:
        return f"<CodeExecutionEngine timeout={self.timeout}s>"
