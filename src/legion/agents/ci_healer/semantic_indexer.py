"""SemanticIndexer — поиск релевантных файлов для патчинга.

Использует AST и semantic search для нахождения файлов, связанных с ошибкой.
"""

import ast
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class SemanticIndexer:
    """AST-based индексатор для semantic search."""
    
    def __init__(self):
        self.index = {}
        self.logger = logger
    
    def build_index(self, source_tree: Dict[str, str]):
        """
        Строит AST-индекс для всех Python файлов.
        
        Args:
            source_tree: {filepath: content}
        """
        logger.info(f"[SemanticIndexer] Building index for {len(source_tree)} files")
        
        for filepath, content in source_tree.items():
            if not filepath.endswith(".py"):
                continue
            
            try:
                tree = ast.parse(content)
                self.index[filepath] = self._extract_symbols(tree)
            except SyntaxError:
                # Файл с синтаксической ошибкой — всё равно индексируем
                self.index[filepath] = {"has_syntax_error": True}
            except Exception as e:
                logger.error(f"[SemanticIndexer] Failed to parse {filepath}: {e}")
        
        logger.info(f"[SemanticIndexer] Indexed {len(self.index)} files")
    
    def search(self, problem, source_tree: Dict[str, str]) -> Dict[str, str]:
        """
        Ищет релевантные файлы для проблемы.
        
        Args:
            problem: CIProblem объект
            source_tree: Полное дерево проекта
        
        Returns:
            Dict с релевантными файлами {path: content}
        """
        relevant = {}
        
        # Если файл указан явно — возвращаем его
        if problem.file:
            if problem.file in source_tree:
                relevant[problem.file] = source_tree[problem.file]
                return relevant
        
        # Semantic search по индексу
        # Ищем файлы, где встречаются ключевые слова из ошибки
        keywords = self._extract_keywords(problem.message)
        
        for filepath, symbols in self.index.items():
            if self._matches(symbols, keywords):
                if filepath in source_tree:
                    relevant[filepath] = source_tree[filepath]
        
        logger.info(f"[SemanticIndexer] Found {len(relevant)} relevant files")
        return relevant
    
    def _extract_symbols(self, tree: ast.AST) -> Dict:
        """
        Извлекает символы из AST (функции, классы, импорты).
        
        Args:
            tree: AST дерево
        
        Returns:
            Dict с метаданными
        """
        symbols = {
            "functions": [],
            "classes": [],
            "imports": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols["functions"].append(node.name)
            elif isinstance(node, ast.ClassDef):
                symbols["classes"].append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    symbols["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    symbols["imports"].append(node.module)
        
        return symbols
    
    def _extract_keywords(self, message: str) -> List[str]:
        """
        Извлекает ключевые слова из сообщения об ошибке.
        
        Args:
            message: Текст ошибки
        
        Returns:
            Список ключевых слов
        """
        import re
        
        # Извлекаем имена функций, классов, переменных
        words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", message)
        
        # Фильтруем служебные слова
        stopwords = {"error", "exception", "line", "file", "at", "in", "from", "import"}
        keywords = [w for w in words if w.lower() not in stopwords]
        
        return keywords[:10]  # Топ-10 ключевых слов
    
    def _matches(self, symbols: Dict, keywords: List[str]) -> bool:
        """
        Проверяет, содержит ли файл какие-либо keywords.
        
        Args:
            symbols: Метаданные файла
            keywords: Ключевые слова для поиска
        
        Returns:
            True если есть совпадения
        """
        all_symbols = (
            symbols.get("functions", []) +
            symbols.get("classes", []) +
            symbols.get("imports", [])
        )
        
        for keyword in keywords:
            if keyword in all_symbols:
                return True
        
        return False
