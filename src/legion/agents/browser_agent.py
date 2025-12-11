"""Playwright Browser Agent - автоматизация браузера через Playwright.

Предоставляет высокоуровневый API для управления браузером:
- Навигация по страницам
- Взаимодействие с элементами
- Извлечение данных
- Скриншоты
"""

import logging
import asyncio
from typing import Any, Dict, Optional, List
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Any
    Page = Any
    BrowserContext = Any
    async_playwright = None  # type: ignore

from ..base_agent import LegionAgent

logger = logging.getLogger(__name__)


class PlaywrightBrowserAgent(LegionAgent):
    """Агент для автоматизации браузера на Playwright.
    
    Поддерживает:
    - Chromium, Firefox, WebKit
    - Headless и headful режимы
    - Скриншоты и видео
    - Прокси и аутентификация
    
    Attributes:
        browser_type: Тип браузера (chromium/firefox/webkit)
        headless: Режим headless
        browser: Объект браузера
        context: Контекст браузера
        page: Текущая страница
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Инициализация browser agent.
        
        Args:
            agent_id: Уникальный ID агента
            config: Конфигурация:
                - browser: 'chromium' | 'firefox' | 'webkit'
                - headless: bool
                - viewport: {width: int, height: int}
                - user_agent: str
                - proxy: {server: str, username: str, password: str}
                - slow_mo: int (мс задержки)
        
        Raises:
            ImportError: Если Playwright не установлен
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. Install: pip install playwright && playwright install"
            )
        
        super().__init__(agent_id, config)
        
        self.browser_type = self.config.get('browser', 'chromium')
        self.headless = self.config.get('headless', True)
        
        # Playwright объекты (инициализируются при start)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        logger.info(f"PlaywrightBrowserAgent '{agent_id}' created ({self.browser_type}, headless={self.headless})")
    
    async def start(self) -> None:
        """Запустить браузер и создать контекст."""
        if self.is_active:
            logger.warning(f"Agent '{self.agent_id}' already started")
            return
        
        logger.info(f"Starting browser agent '{self.agent_id}'...")
        
        # Запуск Playwright
        self.playwright = await async_playwright().start()
        
        # Выбор браузера
        if self.browser_type == 'firefox':
            browser_type = self.playwright.firefox
        elif self.browser_type == 'webkit':
            browser_type = self.playwright.webkit
        else:  # chromium (default)
            browser_type = self.playwright.chromium
        
        # Запуск браузера
        launch_options = {
            'headless': self.headless
        }
        
        if 'slow_mo' in self.config:
            launch_options['slow_mo'] = self.config['slow_mo']
        
        if 'proxy' in self.config:
            launch_options['proxy'] = self.config['proxy']
        
        self.browser = await browser_type.launch(**launch_options)
        
        # Создание контекста
        context_options = {}
        
        if 'viewport' in self.config:
            context_options['viewport'] = self.config['viewport']
        
        if 'user_agent' in self.config:
            context_options['user_agent'] = self.config['user_agent']
        
        self.context = await self.browser.new_context(**context_options)
        
        # Создание страницы
        self.page = await self.context.new_page()
        
        self.is_active = True
        logger.info(f"✅ Browser agent '{self.agent_id}' started successfully")
    
    async def stop(self) -> None:
        """Остановить браузер и очистить ресурсы."""
        if not self.is_active:
            return
        
        logger.info(f"Stopping browser agent '{self.agent_id}'...")
        
        if self.context:
            await self.context.close()
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        
        self.is_active = False
        logger.info(f"Browser agent '{self.agent_id}' stopped")
    
    async def execute_async(self, task_data: Dict[str, Any]) -> Any:
        """Выполнить задачу в браузере (асинхронно).
        
        Args:
            task_data: Данные задачи:
                - action: 'navigate' | 'click' | 'type' | 'screenshot' | 'extract'
                - params: Параметры действия
        
        Returns:
            Результат выполнения
        """
        if not self.is_active or not self.page:
            raise RuntimeError(f"Agent '{self.agent_id}' not started. Call start() first.")
        
        action = task_data.get('action')
        params = task_data.get('params', {})
        
        logger.debug(f"Executing action: {action} with params: {params}")
        
        if action == 'navigate':
            return await self._navigate(params)
        elif action == 'click':
            return await self._click(params)
        elif action == 'type':
            return await self._type(params)
        elif action == 'screenshot':
            return await self._screenshot(params)
        elif action == 'extract':
            return await self._extract(params)
        elif action == 'wait':
            return await self._wait(params)
        elif action == 'evaluate':
            return await self._evaluate(params)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def execute(self, task_data: Dict[str, Any]) -> Any:
        """Синхронная обёртка для execute_async."""
        return asyncio.run(self.execute_async(task_data))
    
    async def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Перейти на URL."""
        url = params.get('url')
        wait_until = params.get('wait_until', 'load')
        
        logger.info(f"Navigating to: {url}")
        response = await self.page.goto(url, wait_until=wait_until)
        
        return {
            'success': response.ok if response else False,
            'url': self.page.url,
            'title': await self.page.title(),
            'status': response.status if response else None
        }
    
    async def _click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Кликнуть по элементу."""
        selector = params.get('selector')
        logger.info(f"Clicking: {selector}")
        
        await self.page.click(selector)
        return {'success': True, 'selector': selector}
    
    async def _type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ввести текст в поле."""
        selector = params.get('selector')
        text = params.get('text')
        
        logger.info(f"Typing into {selector}: {text}")
        await self.page.fill(selector, text)
        
        return {'success': True, 'selector': selector, 'text': text}
    
    async def _screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Сделать скриншот."""
        path = params.get('path')
        full_page = params.get('full_page', False)
        
        logger.info(f"Taking screenshot: {path}")
        
        screenshot_bytes = await self.page.screenshot(
            path=path,
            full_page=full_page
        )
        
        return {
            'success': True,
            'path': path,
            'size': len(screenshot_bytes) if screenshot_bytes else 0
        }
    
    async def _extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечь данные со страницы."""
        selector = params.get('selector')
        attribute = params.get('attribute', 'textContent')
        
        logger.info(f"Extracting {attribute} from {selector}")
        
        if selector:
            element = await self.page.query_selector(selector)
            if not element:
                return {'success': False, 'error': f"Element not found: {selector}"}
            
            if attribute == 'textContent':
                data = await element.text_content()
            elif attribute == 'innerHTML':
                data = await element.inner_html()
            else:
                data = await element.get_attribute(attribute)
        else:
            # Извлечь всю страницу
            data = await self.page.content()
        
        return {'success': True, 'data': data}
    
    async def _wait(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ожидание элемента или времени."""
        wait_type = params.get('type', 'timeout')
        
        if wait_type == 'selector':
            selector = params.get('selector')
            timeout = params.get('timeout', 30000)
            await self.page.wait_for_selector(selector, timeout=timeout)
            return {'success': True, 'type': 'selector', 'selector': selector}
        
        elif wait_type == 'timeout':
            duration = params.get('duration', 1000)
            await self.page.wait_for_timeout(duration)
            return {'success': True, 'type': 'timeout', 'duration': duration}
        
        elif wait_type == 'load':
            await self.page.wait_for_load_state('load')
            return {'success': True, 'type': 'load'}
        
        else:
            raise ValueError(f"Unknown wait type: {wait_type}")
    
    async def _evaluate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить JavaScript на странице."""
        script = params.get('script')
        
        logger.info("Evaluating JavaScript")
        result = await self.page.evaluate(script)
        
        return {'success': True, 'result': result}
    
    async def cleanup(self) -> None:
        """Очистка ресурсов (алиас для stop)."""
        await self.stop()
    
    def __repr__(self) -> str:
        return f"<PlaywrightBrowserAgent '{self.agent_id}' ({self.browser_type})>"
