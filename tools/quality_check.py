#!/usr/bin/env python3
"""
Code Quality Check Tool for Legion v4.1.0.

Runs:
- isort (import sorting)
- black (code formatting)
- ruff (linting + complexity)
- mypy (type checking)
- pydocstyle (docstring validation)
- pytest (test execution with coverage)
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class QualityChecker:
    """Code quality checker for Legion."""

    def __init__(self, src_dir: str = "src/legion"):
        """Initialize quality checker."""
        self.src_dir = Path(src_dir)
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """Run a command and return success status."""
        print(f"\n{'='*80}")
        print(f"🔍 {description}")
        print(f"{'='*80}")
        print(f"Command: {' '.join(cmd)}\n")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

            if result.returncode == 0:
                print(f"✅ {description} PASSED")
                self.passed += 1
                return True, result.stdout
            else:
                print(f"❌ {description} FAILED (exit code: {result.returncode})")
                self.failed += 1
                return False, result.stdout + result.stderr

        except FileNotFoundError:
            print(f"⚠️ Tool not found for: {description}")
            self.warnings += 1
            return False, "Tool not found"
        except Exception as e:
            print(f"❌ {description} ERROR: {e}")
            self.failed += 1
            return False, str(e)

    def check_isort(self) -> bool:
        """Run isort."""
        success, _ = self.run_command(
            ["isort", "--check-only", "--diff", str(self.src_dir)],
            "Import Sorting (isort)",
        )
        return success

    def check_black(self) -> bool:
        """Run black."""
        success, _ = self.run_command(
            ["black", "--check", "--diff", str(self.src_dir)],
            "Code Formatting (black)",
        )
        return success

    def check_ruff(self) -> bool:
        """Run ruff."""
        success, _ = self.run_command(
            ["ruff", "check", str(self.src_dir)],
            "Linting (ruff)",
        )
        return success

    def check_mypy(self) -> bool:
        """Run mypy."""
        success, _ = self.run_command(
            ["mypy", str(self.src_dir), "--ignore-missing-imports"],
            "Type Checking (mypy)",
        )
        return success

    def check_pydocstyle(self) -> bool:
        """Run pydocstyle."""
        success, _ = self.run_command(
            ["pydocstyle", str(self.src_dir), "--convention=google"],
            "Docstring Validation (pydocstyle)",
        )
        return success

    def run_tests(self) -> bool:
        """Run pytest with coverage."""
        success, output = self.run_command(
            [
                "pytest",
                "tests/",
                "-v",
                "--cov=legion",
                "--cov-report=xml",
                "--cov-report=term",
                "--maxfail=1",
            ],
            "Test Suite (pytest)",
        )

        # Extract coverage percentage
        if "TOTAL" in output:
            lines = output.split("\n")
            for line in lines:
                if "TOTAL" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        coverage_str = parts[-1].rstrip("%")
                        try:
                            coverage = float(coverage_str)
                            print(f"\n📊 Coverage: {coverage}%")
                            if coverage < 80.0:
                                print(f"⚠️ Coverage below target (80%)")
                                self.warnings += 1
                        except ValueError:
                            pass

        return success

    def run_all(self) -> bool:
        """Run all quality checks."""
        print("\n" + "="*80)
        print("🚀 LEGION v4.1.0 - CODE QUALITY CHECK")
        print("="*80)

        # Run all checks
        self.check_isort()
        self.check_black()
        self.check_ruff()
        self.check_mypy()
        self.check_pydocstyle()
        self.run_tests()

        # Summary
        print("\n" + "="*80)
        print("📊 QUALITY CHECK SUMMARY")
        print("="*80)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⚠️ Warnings: {self.warnings}")
        print("="*80)

        if self.failed == 0:
            print("\n🎉 ALL QUALITY CHECKS PASSED!")
            return True
        else:
            print(f"\n❌ {self.failed} QUALITY CHECKS FAILED")
            return False


def main():
    """Main entry point."""
    checker = QualityChecker()
    success = checker.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
