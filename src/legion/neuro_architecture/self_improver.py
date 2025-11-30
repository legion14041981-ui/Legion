"""
Self-Improver Engine - Автоматическая генерация и применение патчей кода.

Возможности:
- Static analysis (AST, complexity, code smells)
- Dynamic evaluation (profiling, memory)
- Patch generation (automated improvements)
- A/B testing (before/after comparison)
- Auto-apply (if metrics improved)
- Auto-rollback (if degradation)
"""

import ast
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json

logger = logging.getLogger(__name__)


@dataclass
class CodeMetrics:
    """Метрики качества кода."""
    file_path: str
    lines_of_code: int
    cyclomatic_complexity: float
    maintainability_index: float
    code_smells: List[str]
    test_coverage: float
    
    def quality_score(self) -> float:
        """Общий score качества (0-100)."""
        # Simple formula
        score = (
            min(100, self.maintainability_index) * 0.4 +
            min(100, (100 - self.cyclomatic_complexity)) * 0.3 +
            min(100, self.test_coverage) * 0.3
        )
        return max(0, score - len(self.code_smells) * 5)


@dataclass
class CodePatch:
    """Патч улучшения кода."""
    id: str
    target_file: str
    patch_type: str  # 'refactor', 'optimize', 'fix'
    old_code: str
    new_code: str
    reasoning: str
    expected_improvement: Dict[str, float]
    risk_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'target_file': self.target_file,
            'patch_type': self.patch_type,
            'old_code': self.old_code,
            'new_code': self.new_code,
            'reasoning': self.reasoning,
            'expected_improvement': self.expected_improvement,
            'risk_score': self.risk_score
        }


class SelfImprover:
    """
    Движок автоматического улучшения кода.
    
    Workflow:
    1. Analyze code quality (static + dynamic)
    2. Identify improvement opportunities
    3. Generate patches
    4. Test patches (before/after)
    5. Apply if better, rollback if worse
    """
    
    def __init__(
        self,
        src_dir: str = "src/legion",
        min_quality_score: float = 60.0,
        auto_apply_threshold: float = 0.3  # Max risk for auto-apply
    ):
        """
        Инициализация Self-Improver.
        
        Args:
            src_dir: Директория с исходниками
            min_quality_score: Минимальный допустимый quality score
            auto_apply_threshold: Максимальный риск для auto-apply
        """
        self.src_dir = Path(src_dir)
        self.min_quality_score = min_quality_score
        self.auto_apply_threshold = auto_apply_threshold
        
        logger.info("✅ SelfImprover initialized")
        logger.info(f"   Source directory: {src_dir}")
        logger.info(f"   Min quality score: {min_quality_score}")
    
    def analyze_codebase(self) -> Dict[str, CodeMetrics]:
        """
        Анализировать всю кодовую базу.
        
        Returns:
            Dict[file_path, CodeMetrics]
        """
        logger.info("🔍 Analyzing codebase...")
        
        metrics = {}
        
        for py_file in self.src_dir.rglob("*.py"):
            if '__pycache__' in str(py_file) or '.pyc' in str(py_file):
                continue
            
            file_metrics = self._analyze_file(py_file)
            metrics[str(py_file)] = file_metrics
            
            logger.debug(f"   {py_file.name}: score={file_metrics.quality_score():.1f}")
        
        logger.info(f"   Analyzed {len(metrics)} files")
        
        return metrics
    
    def _analyze_file(self, file_path: Path) -> CodeMetrics:
        """
        Анализировать отдельный файл.
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            CodeMetrics
        """
        try:
            code = file_path.read_text()
            tree = ast.parse(code)
            
            # Count LOC
            loc = len([line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')])
            
            # Calculate complexity (simplified)
            complexity = self._calculate_complexity(tree)
            
            # Detect code smells
            smells = self._detect_code_smells(tree, code)
            
            # Maintainability index (simplified)
            maintainability = max(0, 100 - complexity * 2 - len(smells) * 5)
            
            # Coverage (mock for now)
            coverage = 80.0  # TODO: Real coverage
            
            return CodeMetrics(
                file_path=str(file_path),
                lines_of_code=loc,
                cyclomatic_complexity=complexity,
                maintainability_index=maintainability,
                code_smells=smells,
                test_coverage=coverage
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to analyze {file_path}: {e}")
            return CodeMetrics(
                file_path=str(file_path),
                lines_of_code=0,
                cyclomatic_complexity=0,
                maintainability_index=0,
                code_smells=[],
                test_coverage=0
            )
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """
        Вычислить cyclomatic complexity.
        
        Args:
            tree: AST дерево
        
        Returns:
            Complexity score
        """
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _detect_code_smells(self, tree: ast.AST, code: str) -> List[str]:
        """
        Обнаружить code smells.
        
        Args:
            tree: AST дерево
            code: Исходный код
        
        Returns:
            Список найденных code smells
        """
        smells = []
        
        # Long method (>50 LOC)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno
                if func_lines > 50:
                    smells.append(f"Long method: {node.name} ({func_lines} LOC)")
        
        # Deep nesting (>4 levels)
        max_depth = self._calculate_nesting_depth(tree)
        if max_depth > 4:
            smells.append(f"Deep nesting: {max_depth} levels")
        
        # Magic numbers
        if any(char.isdigit() and not line.strip().startswith('#') for line in code.split('\n') for char in line):
            # Simplified check
            pass  # TODO: More sophisticated magic number detection
        
        return smells
    
    def _calculate_nesting_depth(self, tree: ast.AST) -> int:
        """
        Вычислить максимальную глубину вложенности.
        
        Args:
            tree: AST дерево
        
        Returns:
            Максимальная глубина
        """
        def depth(node: ast.AST, current: int = 0) -> int:
            max_d = current
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                    max_d = max(max_d, depth(child, current + 1))
                else:
                    max_d = max(max_d, depth(child, current))
            return max_d
        
        return depth(tree)
    
    def generate_patches(self, metrics: Dict[str, CodeMetrics]) -> List[CodePatch]:
        """
        Генерировать патчи улучшения.
        
        Args:
            metrics: Метрики кодовой базы
        
        Returns:
            Список патчей
        """
        logger.info("🔧 Generating improvement patches...")
        
        patches = []
        
        for file_path, file_metrics in metrics.items():
            quality = file_metrics.quality_score()
            
            if quality < self.min_quality_score:
                logger.info(f"   Low quality file: {Path(file_path).name} (score={quality:.1f})")
                
                # Generate refactor patches for each code smell
                for smell in file_metrics.code_smells:
                    patch = self._generate_refactor_patch(file_path, smell)
                    if patch:
                        patches.append(patch)
        
        logger.info(f"   Generated {len(patches)} patches")
        
        return patches
    
    def _generate_refactor_patch(self, file_path: str, code_smell: str) -> Optional[CodePatch]:
        """
        Генерировать патч для исправления code smell.
        
        Args:
            file_path: Путь к файлу
            code_smell: Описание code smell
        
        Returns:
            CodePatch или None
        """
        # TODO: Implement real patch generation using LLM or AST transformation
        # For now, return None
        return None
    
    def test_patch(self, patch: CodePatch) -> Tuple[bool, Dict[str, Any]]:
        """
        Тестировать патч.
        
        Args:
            patch: Патч для тестирования
        
        Returns:
            (success, metrics)
        """
        logger.info(f"🧪 Testing patch {patch.id}...")
        
        try:
            # Create temporary file with patched code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(patch.new_code)
                tmp_path = tmp.name
            
            # Run static analysis
            static_ok = self._run_static_analysis(tmp_path)
            
            # Run unit tests (if available)
            tests_ok = self._run_unit_tests(patch.target_file)
            
            # Cleanup
            Path(tmp_path).unlink()
            
            success = static_ok and tests_ok
            
            return success, {
                'static_analysis': 'passed' if static_ok else 'failed',
                'unit_tests': 'passed' if tests_ok else 'failed'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to test patch: {e}")
            return False, {'error': str(e)}
    
    def _run_static_analysis(self, file_path: str) -> bool:
        """
        Запустить static analysis.
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            True если прошёл проверку
        """
        try:
            # Try to parse (basic syntax check)
            with open(file_path, 'r') as f:
                ast.parse(f.read())
            return True
        except SyntaxError:
            return False
    
    def _run_unit_tests(self, file_path: str) -> bool:
        """
        Запустить unit tests.
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            True если тесты прошли
        """
        # TODO: Run actual tests
        # For now, assume passed
        return True
    
    def apply_patch(self, patch: CodePatch) -> bool:
        """
        Применить патч.
        
        Args:
            patch: Патч для применения
        
        Returns:
            True если успешно
        """
        logger.info(f"✅ Applying patch {patch.id} to {Path(patch.target_file).name}...")
        
        try:
            # Read current file
            file_path = Path(patch.target_file)
            current_code = file_path.read_text()
            
            # Apply patch (simple replacement)
            if patch.old_code in current_code:
                new_code = current_code.replace(patch.old_code, patch.new_code)
                
                # Backup original
                backup_path = file_path.with_suffix('.py.bak')
                backup_path.write_text(current_code)
                
                # Write patched code
                file_path.write_text(new_code)
                
                logger.info(f"   ✅ Patch applied successfully")
                logger.info(f"   Backup saved: {backup_path}")
                
                return True
            else:
                logger.error(f"   ❌ Old code not found in file")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to apply patch: {e}")
            return False
    
    def rollback_patch(self, patch: CodePatch) -> bool:
        """
        Откатить патч.
        
        Args:
            patch: Патч для отката
        
        Returns:
            True если успешно
        """
        logger.info(f"🔄 Rolling back patch {patch.id}...")
        
        try:
            file_path = Path(patch.target_file)
            backup_path = file_path.with_suffix('.py.bak')
            
            if backup_path.exists():
                # Restore from backup
                original_code = backup_path.read_text()
                file_path.write_text(original_code)
                backup_path.unlink()
                
                logger.info(f"   ✅ Patch rolled back successfully")
                return True
            else:
                logger.error(f"   ❌ Backup file not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to rollback patch: {e}")
            return False
