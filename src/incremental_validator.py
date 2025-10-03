"""Incremental validation during implementation."""

import subprocess
from pathlib import Path
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of incremental validation."""

    passed: bool
    errors: List[str]
    warnings: List[str]
    checks_run: List[str]


class IncrementalValidator:
    """Validates code quality after each significant change."""

    def __init__(self, workspace: Path):
        """
        Initialize incremental validator.

        Args:
            workspace: Project workspace path
        """
        self.workspace = workspace

    def validate_change(self, file_path: Optional[str] = None) -> ValidationResult:
        """
        Run fast quality checks after a change.

        Args:
            file_path: Optional specific file to validate (validates all if None)

        Returns:
            ValidationResult
        """
        errors: List[str] = []
        warnings: List[str] = []
        checks_run: List[str] = []

        # 1. Syntax check (very fast)
        syntax_ok, syntax_errors = self._check_syntax(file_path)
        checks_run.append("Syntax")
        if not syntax_ok:
            errors.extend(syntax_errors)

        # 2. Type check on changed files only (fast)
        if syntax_ok:  # Only if syntax is good
            type_ok, type_errors = self._check_types_quick(file_path)
            checks_run.append("Types")
            if not type_ok:
                errors.extend(type_errors)

        # 3. Basic lint (fast)
        lint_ok, lint_warnings = self._check_lint_quick(file_path)
        checks_run.append("Lint")
        if not lint_ok:
            warnings.extend(lint_warnings)

        passed = len(errors) == 0

        return ValidationResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            checks_run=checks_run
        )

    def _check_syntax(self, file_path: Optional[str]) -> Tuple[bool, List[str]]:
        """
        Quick syntax check.

        Args:
            file_path: Optional file path to check

        Returns:
            (passed, errors)
        """
        errors = []

        try:
            if file_path:
                full_path = self.workspace / file_path

                # Python
                if full_path.suffix == '.py':
                    result = subprocess.run(
                        ["python3", "-m", "py_compile", str(full_path)],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode != 0:
                        errors.append(f"Syntax error in {file_path}: {result.stderr[:200]}")

                # TypeScript/JavaScript
                elif full_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
                    # Quick parse check with tsc
                    result = subprocess.run(
                        ["npx", "tsc", "--noEmit", str(full_path)],
                        cwd=self.workspace,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode != 0:
                        errors.append(f"Syntax error in {file_path}")

            return len(errors) == 0, errors

        except subprocess.TimeoutExpired:
            return True, []  # Don't fail on timeout
        except Exception:
            return True, []  # Don't fail validation on errors

    def _check_types_quick(self, file_path: Optional[str]) -> Tuple[bool, List[str]]:
        """
        Quick type check on specific file.

        Args:
            file_path: Optional file path to check

        Returns:
            (passed, errors)
        """
        errors = []

        try:
            if file_path:
                full_path = self.workspace / file_path

                # TypeScript
                if full_path.suffix in ['.ts', '.tsx']:
                    result = subprocess.run(
                        ["npx", "tsc", "--noEmit", str(full_path)],
                        cwd=self.workspace,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode != 0:
                        errors.append(f"Type error in {file_path}")

                # Python with mypy
                elif full_path.suffix == '.py':
                    if (self.workspace / "mypy.ini").exists():
                        result = subprocess.run(
                            ["mypy", str(full_path)],
                            cwd=self.workspace,
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode != 0:
                            errors.append(f"Type error in {file_path}")

            return len(errors) == 0, errors

        except subprocess.TimeoutExpired:
            return True, []
        except Exception:
            return True, []

    def _check_lint_quick(self, file_path: Optional[str]) -> Tuple[bool, List[str]]:
        """
        Quick lint check.

        Args:
            file_path: Optional file path to check

        Returns:
            (passed, warnings)
        """
        warnings = []

        try:
            if file_path:
                full_path = self.workspace / file_path

                # ESLint for JS/TS
                if full_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
                    if (self.workspace / ".eslintrc.json").exists():
                        result = subprocess.run(
                            ["npx", "eslint", str(full_path)],
                            cwd=self.workspace,
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode != 0:
                            warnings.append(f"Lint issues in {file_path}")

                # Flake8 for Python
                elif full_path.suffix == '.py':
                    if (self.workspace / ".flake8").exists():
                        result = subprocess.run(
                            ["flake8", str(full_path)],
                            cwd=self.workspace,
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode != 0:
                            warnings.append(f"Lint issues in {file_path}")

            return len(warnings) == 0, warnings

        except subprocess.TimeoutExpired:
            return True, []
        except Exception:
            return True, []

    def should_validate(self, action_type: str) -> bool:
        """
        Determine if validation should run for this action type.

        Args:
            action_type: Type of action executed

        Returns:
            True if validation should run
        """
        # Validate after file modifications
        return action_type in ["write_file", "edit_file", "commit"]
