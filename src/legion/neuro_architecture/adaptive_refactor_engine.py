"""
Adaptive Refactor Engine - Архитектурная модернизация кода.

Возможности:
- Code smell detection
- Pattern modernization (legacy → modern)
- Interface updates (type hints, docstrings)
- Test generation
- Backward compatibility preservation
"""

import ast
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import json

logger = logging.getLogger(__name__)


@dataclass
class RefactorProposal:
    """Предложение по рефакторингу."""
    id: str
    target_file: str
    refactor_type: str  # 'modernize', 'simplify', 'optimize', 'document'
    old_pattern: str
    new_pattern: str
    reasoning: str
    affected_lines: List[int]
    risk_score: float
    backward_compatible: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'target_file': self.target_file,
            'refactor_type': self.refactor_type,
            'old_pattern': self.old_pattern,
            'new_pattern': self.new_pattern,
            'reasoning': self.reasoning,
            'affected_lines': self.affected_lines,
            'risk_score': self.risk_score,
            'backward_compatible': self.backward_compatible
        }


class AdaptiveRefactorEngine:
    """
    Движок адаптивного рефакторинга.
    
    Операции:
    1. Detect legacy patterns
    2. Propose modern alternatives
    3. Update interfaces (type hints, docs)
    4. Generate tests
    5. Ensure backward compatibility
    """
    
    # Patterns для модернизации
    LEGACY_PATTERNS = {
        # Sync → Async (где уместно)
        r'def\s+(\w+)\(([^)]*)\):\s*\n\s+""".*?"""\s*\n\s+time\.sleep': {
            'modern': 'async def {func}({params}):\n    """..."""\n    await asyncio.sleep',
            'reasoning': 'Async improves concurrency'
        },
        
        # String formatting: % → f-strings
        r'["\'].*?%[sd].*?["\']\s*%\s*\(': {
            'modern': 'f"...{var}..."',
            'reasoning': 'f-strings more readable and faster'
        },
        
        # Dict.get() instead of try/except KeyError
        r'try:\s*\n\s+.*?\[([^]]+)\]\s*\n\s*except KeyError:': {
            'modern': '.get({key}, default)',
            'reasoning': 'More Pythonic error handling'
        }
    }
    
    def __init__(
        self,
        src_dir: str = "src/legion",
        preserve_compatibility: bool = True
    ):
        """
        Инициализация Adaptive Refactor Engine.
        
        Args:
            src_dir: Директория с исходниками
            preserve_compatibility: Сохранять backward compatibility
        """
        self.src_dir = Path(src_dir)
        self.preserve_compatibility = preserve_compatibility
        
        logger.info("✅ AdaptiveRefactorEngine initialized")
        logger.info(f"   Backward compatibility: {preserve_compatibility}")
    
    def analyze_codebase(self) -> List[RefactorProposal]:
        """
        Анализировать кодовую базу и найти возможности рефакторинга.
        
        Returns:
            Список предложений по рефакторингу
        """
        logger.info("🔍 Analyzing codebase for refactoring opportunities...")
        
        proposals = []
        
        for py_file in self.src_dir.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue
            
            file_proposals = self._analyze_file(py_file)
            proposals.extend(file_proposals)
            
            if file_proposals:
                logger.debug(f"   {py_file.name}: {len(file_proposals)} proposals")
        
        logger.info(f"   Found {len(proposals)} refactoring opportunities")
        
        return proposals
    
    def _analyze_file(self, file_path: Path) -> List[RefactorProposal]:
        """
        Анализировать отдельный файл.
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            Список предложений
        """
        proposals = []
        
        try:
            code = file_path.read_text()
            tree = ast.parse(code)
            
            # Check for missing type hints
            proposals.extend(self._find_missing_type_hints(file_path, tree, code))
            
            # Check for missing docstrings
            proposals.extend(self._find_missing_docstrings(file_path, tree, code))
            
            # Check for legacy patterns
            proposals.extend(self._find_legacy_patterns(file_path, code))
            
            # Check for complex functions
            proposals.extend(self._find_complex_functions(file_path, tree, code))
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to analyze {file_path}: {e}")
        
        return proposals
    
    def _find_missing_type_hints(self, file_path: Path, tree: ast.AST, code: str) -> List[RefactorProposal]:
        """
        Найти функции без type hints.
        
        Args:
            file_path: Путь к файлу
            tree: AST дерево
            code: Исходный код
        
        Returns:
            Список предложений
        """
        proposals = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if missing return type
                if node.returns is None and node.name != '__init__':
                    proposals.append(RefactorProposal(
                        id=f"type_hint_{file_path.stem}_{node.name}",
                        target_file=str(file_path),
                        refactor_type='document',
                        old_pattern=f"def {node.name}(",
                        new_pattern=f"def {node.name}(...) -> ReturnType:",
                        reasoning="Add type hints for better IDE support and type checking",
                        affected_lines=[node.lineno],
                        risk_score=0.1,
                        backward_compatible=True
                    ))
        
        return proposals
    
    def _find_missing_docstrings(self, file_path: Path, tree: ast.AST, code: str) -> List[RefactorProposal]:
        """
        Найти функции без docstrings.
        
        Args:
            file_path: Путь к файлу
            tree: AST дерево
            code: Исходный код
        
        Returns:
            Список предложений
        """
        proposals = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node)
                
                if not docstring and not node.name.startswith('_'):
                    proposals.append(RefactorProposal(
                        id=f"docstring_{file_path.stem}_{node.name}",
                        target_file=str(file_path),
                        refactor_type='document',
                        old_pattern=f"def {node.name}(",
                        new_pattern=f"def {node.name}(...):\n    \"\"\"Function description.\"\"\"",
                        reasoning="Add docstring for better documentation",
                        affected_lines=[node.lineno],
                        risk_score=0.05,
                        backward_compatible=True
                    ))
        
        return proposals
    
    def _find_legacy_patterns(self, file_path: Path, code: str) -> List[RefactorProposal]:
        """
        Найти legacy patterns.
        
        Args:
            file_path: Путь к файлу
            code: Исходный код
        
        Returns:
            Список предложений
        """
        proposals = []
        
        lines = code.split('\n')
        
        # Check for old-style string formatting
        for i, line in enumerate(lines, 1):
            if '%s' in line or '%d' in line:
                if '"' in line or "'" in line:
                    proposals.append(RefactorProposal(
                        id=f"modernize_string_{file_path.stem}_{i}",
                        target_file=str(file_path),
                        refactor_type='modernize',
                        old_pattern=line.strip(),
                        new_pattern="Use f-strings instead",
                        reasoning="f-strings are more readable and faster",
                        affected_lines=[i],
                        risk_score=0.2,
                        backward_compatible=True
                    ))
        
        return proposals
    
    def _find_complex_functions(self, file_path: Path, tree: ast.AST, code: str) -> List[RefactorProposal]:
        """
        Найти слишком сложные функции.
        
        Args:
            file_path: Путь к файлу
            tree: AST дерево
            code: Исходный код
        
        Returns:
            Список предложений
        """
        proposals = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate complexity
                complexity = self._calculate_complexity(node)
                
                if complexity > 10:
                    proposals.append(RefactorProposal(
                        id=f"simplify_{file_path.stem}_{node.name}",
                        target_file=str(file_path),
                        refactor_type='simplify',
                        old_pattern=node.name,
                        new_pattern="Split into smaller functions",
                        reasoning=f"High complexity ({complexity}) makes code hard to maintain",
                        affected_lines=[node.lineno],
                        risk_score=0.4,
                        backward_compatible=True
                    ))
        
        return proposals
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """
        Вычислить cyclomatic complexity функции.
        
        Args:
            node: AST node функции
        
        Returns:
            Complexity score
        """
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def apply_refactor(self, proposal: RefactorProposal) -> bool:
        """
        Применить рефакторинг.
        
        Args:
            proposal: Предложение по рефакторингу
        
        Returns:
            True если успешно
        """
        logger.info(f"🔧 Applying refactor: {proposal.id}")
        
        # Check backward compatibility
        if self.preserve_compatibility and not proposal.backward_compatible:
            logger.warning(f"   ⚠️ Skipping: breaks backward compatibility")
            return False
        
        # TODO: Implement actual refactoring
        # For now, just log
        logger.info(f"   Type: {proposal.refactor_type}")
        logger.info(f"   Risk: {proposal.risk_score:.2f}")
        logger.info(f"   Reasoning: {proposal.reasoning}")
        
        return True
    
    def generate_tests(self, file_path: Path) -> List[str]:
        """
        Сгенерировать тесты для файла.
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            Список сгенерированных тестов
        """
        logger.info(f"🧪 Generating tests for {file_path.name}...")
        
        tests = []
        
        try:
            code = file_path.read_text()
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    # Generate basic test template
                    test_code = f"""
def test_{node.name}():
    \"\"\"Test {node.name} function.\"\"\"
    # TODO: Implement test
    pass
"""
                    tests.append(test_code)
        
        except Exception as e:
            logger.error(f"❌ Failed to generate tests: {e}")
        
        logger.info(f"   Generated {len(tests)} test templates")
        
        return tests
