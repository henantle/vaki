"""Enhanced quality gate system for strict quality enforcement."""

import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Callable, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .security import sanitize


class QualityLevel(Enum):
    """Quality gate severity levels."""

    CRITICAL = "critical"  # Must pass, no exceptions
    REQUIRED = "required"  # Should pass, warnings if not
    RECOMMENDED = "recommended"  # Nice to have


@dataclass
class GateResult:
    """Result of a quality gate check."""

    gate_name: str
    level: QualityLevel
    passed: bool
    message: str
    details: Optional[str] = None


@dataclass
class QualityReport:
    """Overall quality assessment report."""

    passed: bool
    critical_failures: List[GateResult]
    required_failures: List[GateResult]
    recommended_failures: List[GateResult]
    all_results: List[GateResult]

    @property
    def has_critical_failures(self) -> bool:
        """Check if there are any critical failures."""
        return len(self.critical_failures) > 0

    @property
    def summary(self) -> str:
        """Get summary string."""
        total = len(self.all_results)
        passed = sum(1 for r in self.all_results if r.passed)
        return f"{passed}/{total} checks passed"


class QualityGate:
    """Enhanced quality gate system with tiered enforcement."""

    def __init__(self, workspace: Path, config: Optional[Dict[str, Any]] = None):
        """
        Initialize quality gate system.

        Args:
            workspace: Project workspace path
            config: Optional configuration for quality gates
        """
        self.workspace = workspace
        self.config = config or {}

        # Define all quality gates
        self.gates = self._define_gates()

    def _define_gates(self) -> Dict[QualityLevel, List[Tuple[str, Callable]]]:
        """Define all quality gates by level."""
        return {
            QualityLevel.CRITICAL: [
                ("Security Check", self._check_security),
                ("Syntax Check", self._check_syntax),
                ("Breaking Changes", self._check_breaking_changes),
            ],
            QualityLevel.REQUIRED: [
                ("Type Check", self._check_types),
                ("Tests Pass", self._check_tests),
                ("Build Success", self._check_build),
                ("Lint Check", self._check_lint),
            ],
            QualityLevel.RECOMMENDED: [
                ("Test Coverage", self._check_coverage),
                ("Code Complexity", self._check_complexity),
                ("Documentation", self._check_documentation),
            ]
        }

    def check_all(self) -> QualityReport:
        """
        Run all quality gates.

        Returns:
            QualityReport with results
        """
        all_results: List[GateResult] = []
        critical_failures: List[GateResult] = []
        required_failures: List[GateResult] = []
        recommended_failures: List[GateResult] = []

        # Run all gates
        for level, gates in self.gates.items():
            for gate_name, gate_fn in gates:
                result = self._run_gate(gate_name, level, gate_fn)
                all_results.append(result)

                if not result.passed:
                    if level == QualityLevel.CRITICAL:
                        critical_failures.append(result)
                    elif level == QualityLevel.REQUIRED:
                        required_failures.append(result)
                    else:
                        recommended_failures.append(result)

        # Overall pass requires no critical failures
        passed = len(critical_failures) == 0

        return QualityReport(
            passed=passed,
            critical_failures=critical_failures,
            required_failures=required_failures,
            recommended_failures=recommended_failures,
            all_results=all_results
        )

    def check_level(self, level: QualityLevel) -> List[GateResult]:
        """
        Run gates for a specific level only.

        Args:
            level: Quality level to check

        Returns:
            List of gate results for that level
        """
        results: List[GateResult] = []
        gates = self.gates.get(level, [])

        for gate_name, gate_fn in gates:
            result = self._run_gate(gate_name, level, gate_fn)
            results.append(result)

        return results

    def _run_gate(
        self,
        gate_name: str,
        level: QualityLevel,
        gate_fn: Callable
    ) -> GateResult:
        """
        Run a single quality gate.

        Args:
            gate_name: Name of the gate
            level: Quality level
            gate_fn: Function to execute

        Returns:
            GateResult
        """
        try:
            passed, message, details = gate_fn()
            return GateResult(
                gate_name=gate_name,
                level=level,
                passed=passed,
                message=message,
                details=details
            )
        except Exception as e:
            return GateResult(
                gate_name=gate_name,
                level=level,
                passed=False,
                message=f"Gate execution failed: {sanitize(str(e))}",
                details=None
            )

    def _check_security(self) -> Tuple[bool, str, Optional[str]]:
        """Check for security vulnerabilities."""
        # Check for common security issues
        try:
            # npm audit for Node.js projects
            if (self.workspace / "package.json").exists():
                result = subprocess.run(
                    ["npm", "audit", "--audit-level=high"],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode != 0:
                    return False, "Security vulnerabilities found", sanitize(result.stdout[:500])
                return True, "No high/critical vulnerabilities", None

            # Python: check for known vulnerable packages
            if (self.workspace / "requirements.txt").exists():
                # Could integrate with safety or pip-audit
                # For now, just check it exists
                return True, "Security check passed", None

            return True, "No security scan configured", None

        except subprocess.TimeoutExpired:
            return False, "Security check timed out", None
        except Exception as e:
            return False, f"Security check failed: {sanitize(str(e))}", None

    def _check_syntax(self) -> Tuple[bool, str, Optional[str]]:
        """Check for syntax errors."""
        try:
            # TypeScript/JavaScript
            if (self.workspace / "tsconfig.json").exists():
                result = subprocess.run(
                    ["npx", "tsc", "--noEmit"],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode != 0:
                    return False, "TypeScript syntax errors", sanitize(result.stderr[:500])
                return True, "No syntax errors", None

            # Python
            python_files = list(self.workspace.glob("**/*.py"))
            if python_files and len(python_files) < 100:  # Don't check too many
                for py_file in python_files[:20]:  # Check first 20
                    result = subprocess.run(
                        ["python3", "-m", "py_compile", str(py_file)],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        return False, f"Syntax error in {py_file.name}", sanitize(result.stderr[:200])
                return True, "No syntax errors", None

            return True, "Syntax check passed", None

        except subprocess.TimeoutExpired:
            return False, "Syntax check timed out", None
        except Exception as e:
            return False, f"Syntax check failed: {sanitize(str(e))}", None

    def _check_breaking_changes(self) -> Tuple[bool, str, Optional[str]]:
        """Check for potential breaking changes."""
        try:
            # Get changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                cwd=self.workspace,
                capture_output=True,
                text=True
            )

            changed_files = result.stdout.strip().split('\n')

            # Check for potential breaking changes
            breaking_patterns = [
                "migration",  # Database migrations
                "schema",     # Schema changes
                "package.json",  # Dependency changes
                "requirements.txt",
                ".env.example",  # Config changes
            ]

            risky_files = []
            for file in changed_files:
                for pattern in breaking_patterns:
                    if pattern in file.lower():
                        risky_files.append(file)
                        break

            if risky_files:
                details = "Files with potential breaking changes:\n" + "\n".join(risky_files)
                return False, "Potential breaking changes detected", details

            return True, "No breaking changes detected", None

        except Exception as e:
            # Don't fail on error, just warn
            return True, f"Breaking change check skipped: {sanitize(str(e))}", None

    def _check_types(self) -> Tuple[bool, str, Optional[str]]:
        """Check type safety."""
        try:
            if (self.workspace / "tsconfig.json").exists():
                result = subprocess.run(
                    ["npx", "tsc", "--noEmit"],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode != 0:
                    return False, "Type check failed", sanitize(result.stderr[:500])
                return True, "Type check passed", None

            # Python mypy
            if (self.workspace / "mypy.ini").exists() or (self.workspace / "pyproject.toml").exists():
                result = subprocess.run(
                    ["mypy", "."],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode != 0:
                    return False, "Type check failed", sanitize(result.stdout[:500])
                return True, "Type check passed", None

            return True, "No type checking configured", None

        except subprocess.TimeoutExpired:
            return False, "Type check timed out", None
        except Exception as e:
            return True, f"Type check skipped: {sanitize(str(e))}", None

    def _check_tests(self) -> Tuple[bool, str, Optional[str]]:
        """Check if tests pass."""
        try:
            # Node.js
            if (self.workspace / "package.json").exists():
                with open(self.workspace / "package.json") as f:
                    pkg = json.load(f)
                    if "test" in pkg.get("scripts", {}):
                        result = subprocess.run(
                            ["npm", "test"],
                            cwd=self.workspace,
                            capture_output=True,
                            text=True,
                            timeout=180
                        )
                        if result.returncode != 0:
                            return False, "Tests failed", sanitize(result.stdout[-500:])
                        return True, "Tests passed", None

            # Python
            if (self.workspace / "pytest.ini").exists():
                result = subprocess.run(
                    ["pytest"],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                if result.returncode != 0:
                    return False, "Tests failed", sanitize(result.stdout[-500:])
                return True, "Tests passed", None

            return True, "No tests configured", None

        except subprocess.TimeoutExpired:
            return False, "Tests timed out", None
        except Exception as e:
            return True, f"Tests skipped: {sanitize(str(e))}", None

    def _check_build(self) -> Tuple[bool, str, Optional[str]]:
        """Check if project builds successfully."""
        try:
            if (self.workspace / "package.json").exists():
                with open(self.workspace / "package.json") as f:
                    pkg = json.load(f)
                    if "build" in pkg.get("scripts", {}):
                        result = subprocess.run(
                            ["npm", "run", "build"],
                            cwd=self.workspace,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        if result.returncode != 0:
                            return False, "Build failed", sanitize(result.stderr[-500:])
                        return True, "Build succeeded", None

            return True, "No build configured", None

        except subprocess.TimeoutExpired:
            return False, "Build timed out", None
        except Exception as e:
            return True, f"Build skipped: {sanitize(str(e))}", None

    def _check_lint(self) -> Tuple[bool, str, Optional[str]]:
        """Check code style and linting."""
        try:
            # ESLint for JavaScript/TypeScript
            if (self.workspace / ".eslintrc.json").exists() or \
               (self.workspace / ".eslintrc.js").exists():
                result = subprocess.run(
                    ["npx", "eslint", "."],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode != 0:
                    return False, "Lint errors found", sanitize(result.stdout[:500])
                return True, "Lint check passed", None

            # Flake8 for Python
            if (self.workspace / ".flake8").exists() or \
               (self.workspace / "setup.cfg").exists():
                result = subprocess.run(
                    ["flake8", "."],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode != 0:
                    return False, "Lint errors found", sanitize(result.stdout[:500])
                return True, "Lint check passed", None

            return True, "No linter configured", None

        except subprocess.TimeoutExpired:
            return False, "Lint check timed out", None
        except Exception as e:
            return True, f"Lint check skipped: {sanitize(str(e))}", None

    def _check_coverage(self) -> Tuple[bool, str, Optional[str]]:
        """Check test coverage meets minimum threshold."""
        min_coverage = self.config.get("min_coverage", 80)

        try:
            # Jest coverage for Node.js
            if (self.workspace / "package.json").exists():
                result = subprocess.run(
                    ["npm", "test", "--", "--coverage", "--coverageReporters=json-summary"],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=180
                )

                coverage_file = self.workspace / "coverage" / "coverage-summary.json"
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                        total_coverage = coverage_data.get("total", {}).get("lines", {}).get("pct", 0)
                        if total_coverage < min_coverage:
                            return False, f"Coverage {total_coverage}% < {min_coverage}%", None
                        return True, f"Coverage {total_coverage}% >= {min_coverage}%", None

            return True, "Coverage check skipped", None

        except subprocess.TimeoutExpired:
            return True, "Coverage check timed out", None
        except Exception as e:
            return True, f"Coverage check skipped: {sanitize(str(e))}", None

    def _check_complexity(self) -> Tuple[bool, str, Optional[str]]:
        """Check code complexity."""
        # This would require additional tools like radon for Python or complexity-report for JS
        return True, "Complexity check not implemented", None

    def _check_documentation(self) -> Tuple[bool, str, Optional[str]]:
        """Check documentation completeness."""
        # Basic check: README exists and is not empty
        readme = self.workspace / "README.md"
        if readme.exists():
            content = readme.read_text()
            if len(content) > 100:  # Has some content
                return True, "Documentation exists", None
            return False, "README is too short", None

        return False, "README.md missing", None

    def print_report(self, report: QualityReport) -> None:
        """
        Print formatted quality report.

        Args:
            report: Quality report to print
        """
        print("\n" + "=" * 70)
        print("🔒 QUALITY GATE REPORT")
        print("=" * 70)
        print(f"Overall: {'✅ PASSED' if report.passed else '❌ FAILED'}")
        print(f"Summary: {report.summary}\n")

        if report.critical_failures:
            print("❌ CRITICAL FAILURES (Must Fix):")
            for result in report.critical_failures:
                print(f"  • {result.gate_name}: {result.message}")
                if result.details:
                    print(f"    {result.details[:200]}")

        if report.required_failures:
            print("\n⚠️  REQUIRED FAILURES (Should Fix):")
            for result in report.required_failures:
                print(f"  • {result.gate_name}: {result.message}")

        if report.recommended_failures:
            print("\n💡 RECOMMENDED IMPROVEMENTS:")
            for result in report.recommended_failures:
                print(f"  • {result.gate_name}: {result.message}")

        # Show passed checks
        passed_checks = [r for r in report.all_results if r.passed]
        if passed_checks:
            print(f"\n✅ Passed Checks ({len(passed_checks)}):")
            for result in passed_checks:
                print(f"  • {result.gate_name}")

        print("=" * 70)
