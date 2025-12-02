#!/usr/bin/env python3
"""Validate architectural rules and constraints."""

import ast
import sys
from pathlib import Path
from typing import List, Set, Tuple


class ArchitectureValidator(ast.NodeVisitor):
    """AST visitor to validate architectural rules."""
    
    def __init__(self):
        self.violations: List[Tuple[str, str, int]] = []
        self.current_file: str = ""
    
    def validate_file(self, filepath: Path) -> None:
        """Validate a single Python file."""
        self.current_file = str(filepath)
        
        try:
            with open(filepath) as f:
                tree = ast.parse(f.read(), filename=str(filepath))
            self.visit(tree)
        except SyntaxError as e:
            self.violations.append((
                self.current_file,
                f"Syntax error: {e}",
                e.lineno or 0
            ))
    
    def visit_Import(self, node: ast.Import) -> None:
        """Check import statements."""
        for alias in node.names:
            # Rule: No wildcard imports
            if alias.name == '*':
                self.violations.append((
                    self.current_file,
                    "Wildcard import detected",
                    node.lineno
                ))
            
            # Rule: Core modules should not import from agents
            if 'core' in self.current_file and 'agents' in alias.name:
                # Exception: base agent is allowed
                if 'base' not in alias.name:
                    self.violations.append((
                        self.current_file,
                        f"Core module importing from agents: {alias.name}",
                        node.lineno
                    ))
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check from...import statements."""
        if node.module:
            # Rule: No circular imports
            # (simplified check - full implementation would need dependency graph)
            
            # Rule: Utils should not import from core or agents
            if 'utils' in self.current_file:
                if any(x in node.module for x in ['core', 'agents']):
                    self.violations.append((
                        self.current_file,
                        f"Utils module importing from {node.module}",
                        node.lineno
                    ))
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function definitions."""
        # Rule: Public functions should have docstrings
        if not node.name.startswith('_'):
            docstring = ast.get_docstring(node)
            if not docstring and 'test_' not in self.current_file:
                self.violations.append((
                    self.current_file,
                    f"Public function '{node.name}' missing docstring",
                    node.lineno
                ))
        
        self.generic_visit(node)


def validate_project_structure() -> List[str]:
    """Validate high-level project structure."""
    violations = []
    
    required_dirs = [
        'src/legion',
        'src/legion/agents',
        'src/legion/utils',
        'tests',
        'docs'
    ]
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            violations.append(f"Missing required directory: {dir_path}")
    
    # Check for __init__.py files
    python_dirs = [
        'src/legion',
        'src/legion/agents',
        'src/legion/utils'
    ]
    
    for dir_path in python_dirs:
        init_file = Path(dir_path) / '__init__.py'
        if not init_file.exists():
            violations.append(f"Missing __init__.py in {dir_path}")
    
    return violations


def main() -> int:
    """Main validation function."""
    print("="*80)
    print("🏗️  ARCHITECTURE VALIDATION")
    print("="*80)
    
    # Validate project structure
    print("\n📁 Validating project structure...")
    structure_violations = validate_project_structure()
    
    if structure_violations:
        print("\n❌ Structure violations:")
        for violation in structure_violations:
            print(f"   • {violation}")
    else:
        print("✅ Project structure valid")
    
    # Validate code architecture
    print("\n📝 Validating code architecture...")
    validator = ArchitectureValidator()
    
    src_path = Path('src/legion')
    if src_path.exists():
        for py_file in src_path.rglob('*.py'):
            validator.validate_file(py_file)
    
    if validator.violations:
        print(f"\n❌ {len(validator.violations)} architectural violation(s):")
        for filepath, message, lineno in validator.violations:
            print(f"   • {filepath}:{lineno} - {message}")
    else:
        print("✅ No architectural violations")
    
    total_violations = len(structure_violations) + len(validator.violations)
    
    print("\n" + "="*80)
    if total_violations == 0:
        print("✅ Architecture validation PASSED")
        return 0
    else:
        print(f"❌ Architecture validation FAILED ({total_violations} violations)")
        return 1


if __name__ == '__main__':
    sys.exit(main())
