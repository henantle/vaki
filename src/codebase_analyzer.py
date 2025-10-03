"""Codebase analysis for understanding project structure and patterns."""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Information about a file in the codebase."""

    path: str
    summary: str
    size: int
    language: str


@dataclass
class CodebaseStructure:
    """High-level codebase structure information."""

    tech_stack: List[str]
    frameworks: List[str]
    key_directories: List[str]
    entry_points: List[str]
    test_directories: List[str]
    patterns: List[str]


class CodebaseAnalyzer:
    """Analyzes codebase structure and provides context for implementation."""

    def __init__(self, workspace: Path):
        """
        Initialize codebase analyzer.

        Args:
            workspace: Project workspace path
        """
        self.workspace = workspace
        self._structure: Optional[CodebaseStructure] = None

    def get_architecture_summary(self) -> str:
        """
        Generate high-level architecture summary.

        Returns:
            Formatted architecture summary string
        """
        structure = self._analyze_structure()

        summary_parts = []

        # Tech stack
        if structure.tech_stack:
            summary_parts.append(f"**Tech Stack:** {', '.join(structure.tech_stack)}")

        # Frameworks
        if structure.frameworks:
            summary_parts.append(f"**Frameworks:** {', '.join(structure.frameworks)}")

        # Key directories
        if structure.key_directories:
            summary_parts.append(f"**Structure:** {', '.join(structure.key_directories)}")

        # Entry points
        if structure.entry_points:
            summary_parts.append(f"**Entry Points:** {', '.join(structure.entry_points)}")

        # Common patterns
        if structure.patterns:
            summary_parts.append(f"**Patterns:** {', '.join(structure.patterns)}")

        # Test info
        if structure.test_directories:
            summary_parts.append(f"**Tests:** {', '.join(structure.test_directories)}")

        return "\n".join(summary_parts)

    def find_relevant_files(
        self,
        query: str,
        max_files: int = 10
    ) -> List[FileInfo]:
        """
        Find files relevant to a query using simple keyword matching.

        Args:
            query: Search query (issue title/description keywords)
            max_files: Maximum number of files to return

        Returns:
            List of relevant FileInfo objects
        """
        # Simple keyword-based search
        keywords = self._extract_keywords(query.lower())

        relevant_files: List[tuple[str, int]] = []  # (path, score)

        # Search common code directories
        code_dirs = ["src", "lib", "app", "components", "api", "routes", "controllers", "models"]

        for dir_name in code_dirs:
            dir_path = self.workspace / dir_name
            if not dir_path.exists():
                continue

            # Find files matching keywords
            for file_path in dir_path.rglob("*"):
                if not file_path.is_file():
                    continue

                # Skip large files, node_modules, etc.
                if file_path.stat().st_size > 100000:  # 100KB
                    continue

                if any(exclude in str(file_path) for exclude in ['node_modules', '__pycache__', '.git', 'dist', 'build']):
                    continue

                # Score based on filename and path
                score = self._score_file(file_path, keywords)
                if score > 0:
                    relevant_files.append((str(file_path.relative_to(self.workspace)), score))

        # Sort by score and return top results
        relevant_files.sort(key=lambda x: x[1], reverse=True)

        results = []
        for file_path, score in relevant_files[:max_files]:
            full_path = self.workspace / file_path
            language = self._detect_language(full_path)
            summary = self._generate_file_summary(full_path)

            results.append(FileInfo(
                path=file_path,
                summary=summary,
                size=full_path.stat().st_size,
                language=language
            ))

        return results

    def find_similar_patterns(self, description: str) -> List[str]:
        """
        Find similar code patterns or implementations in the codebase.

        Args:
            description: Description of what to look for

        Returns:
            List of example file paths with similar patterns
        """
        # Simple implementation: find files with similar names
        keywords = self._extract_keywords(description.lower())

        examples = []
        for keyword in keywords[:3]:  # Top 3 keywords
            # Use git grep to find files containing keyword
            try:
                result = subprocess.run(
                    ["git", "grep", "-l", keyword],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    files = result.stdout.strip().split('\n')[:3]
                    examples.extend(files)

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        return list(set(examples))[:5]  # Return up to 5 unique examples

    def _analyze_structure(self) -> CodebaseStructure:
        """
        Analyze codebase structure.

        Returns:
            CodebaseStructure with analysis results
        """
        if self._structure:
            return self._structure

        tech_stack = []
        frameworks = []
        key_directories = []
        entry_points = []
        test_directories = []
        patterns = []

        # Detect tech stack from package files
        if (self.workspace / "package.json").exists():
            try:
                with open(self.workspace / "package.json") as f:
                    pkg = json.load(f)

                    # Tech stack
                    tech_stack.append("Node.js")

                    # Detect frameworks from dependencies
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                    if "react" in deps:
                        frameworks.append("React")
                    if "next" in deps:
                        frameworks.append("Next.js")
                    if "express" in deps:
                        frameworks.append("Express")
                    if "vue" in deps:
                        frameworks.append("Vue")
                    if "@angular/core" in deps:
                        frameworks.append("Angular")
                    if "typescript" in deps or (self.workspace / "tsconfig.json").exists():
                        tech_stack.append("TypeScript")

            except (json.JSONDecodeError, IOError):
                pass

        # Python detection
        if (self.workspace / "requirements.txt").exists() or \
           (self.workspace / "pyproject.toml").exists() or \
           (self.workspace / "setup.py").exists():
            tech_stack.append("Python")

            # Detect Python frameworks
            try:
                req_file = self.workspace / "requirements.txt"
                if req_file.exists():
                    requirements = req_file.read_text().lower()
                    if "django" in requirements:
                        frameworks.append("Django")
                    if "flask" in requirements:
                        frameworks.append("Flask")
                    if "fastapi" in requirements:
                        frameworks.append("FastAPI")
            except IOError:
                pass

        # Detect key directories
        common_dirs = [
            "src", "lib", "app", "components", "pages", "api",
            "routes", "controllers", "models", "services", "utils",
            "views", "templates", "static", "public"
        ]

        for dir_name in common_dirs:
            if (self.workspace / dir_name).exists():
                key_directories.append(dir_name)

        # Detect entry points
        entry_files = [
            "index.js", "index.ts", "main.py", "app.py",
            "server.js", "server.ts", "index.html"
        ]

        for entry_file in entry_files:
            if (self.workspace / entry_file).exists():
                entry_points.append(entry_file)

            # Check in src directory
            if (self.workspace / "src" / entry_file).exists():
                entry_points.append(f"src/{entry_file}")

        # Detect test directories
        test_dirs = ["test", "tests", "__tests__", "spec"]
        for test_dir in test_dirs:
            if (self.workspace / test_dir).exists():
                test_directories.append(test_dir)

        # Detect patterns from README
        if (self.workspace / "README.md").exists():
            try:
                readme = (self.workspace / "README.md").read_text().lower()

                pattern_keywords = [
                    "mvc", "repository", "service layer", "clean architecture",
                    "microservices", "monorepo", "rest api", "graphql",
                    "serverless", "event-driven"
                ]

                for keyword in pattern_keywords:
                    if keyword in readme:
                        patterns.append(keyword.title())

            except IOError:
                pass

        self._structure = CodebaseStructure(
            tech_stack=tech_stack,
            frameworks=frameworks,
            key_directories=key_directories,
            entry_points=entry_points,
            test_directories=test_directories,
            patterns=patterns
        )

        return self._structure

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract relevant keywords from text.

        Args:
            text: Input text

        Returns:
            List of keywords
        """
        # Simple keyword extraction
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'can', 'could', 'may', 'might', 'must', 'this', 'that', 'these', 'those'
        }

        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]

        return keywords[:10]  # Return top 10 keywords

    def _score_file(self, file_path: Path, keywords: List[str]) -> int:
        """
        Score a file's relevance based on keywords.

        Args:
            file_path: Path to file
            keywords: Keywords to match

        Returns:
            Relevance score
        """
        score = 0
        file_str = str(file_path).lower()

        # Score based on filename and path
        for keyword in keywords:
            if keyword in file_str:
                score += 10

        # Bonus for common code file extensions
        if file_path.suffix in ['.ts', '.tsx', '.js', '.jsx', '.py', '.vue', '.java', '.go', '.rb']:
            score += 5

        # Bonus for files in common directories
        if any(d in file_str for d in ['src/', 'lib/', 'app/', 'api/']):
            score += 3

        return score

    def _detect_language(self, file_path: Path) -> str:
        """
        Detect programming language from file extension.

        Args:
            file_path: Path to file

        Returns:
            Language name
        """
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.jsx': 'JavaScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
        }

        return extension_map.get(file_path.suffix, 'Unknown')

    def _generate_file_summary(self, file_path: Path) -> str:
        """
        Generate brief summary of file contents.

        Args:
            file_path: Path to file

        Returns:
            Summary string
        """
        try:
            # Read first few lines
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f.readlines()[:20]]

            # Look for comments, docstrings, or exports
            for line in lines:
                if line.startswith('"""') or line.startswith("'''"):
                    # Python docstring
                    return line.strip('"\' ')
                elif line.startswith('//') or line.startswith('/*'):
                    # JS/TS comment
                    return line.lstrip('/*/ ').rstrip('*/ ')
                elif line.startswith('export') and 'class' in line:
                    # Export statement
                    return f"Exports {line.split('class')[1].split()[0]}"
                elif line.startswith('class '):
                    # Class definition
                    return f"Defines {line.split('class')[1].split()[0]}"
                elif 'function' in line and not line.strip().startswith('//'):
                    # Function definition
                    parts = line.split('function')
                    if len(parts) > 1:
                        func_name = parts[1].split('(')[0].strip()
                        return f"Contains {func_name}()"

            return f"{file_path.suffix[1:].upper()} file"

        except (IOError, UnicodeDecodeError):
            return "Binary or unreadable file"
