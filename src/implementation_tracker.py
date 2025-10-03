"""Implementation tracking for learning and continuous improvement."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from github.Issue import Issue


@dataclass
class ImplementationOutcome:
    """Outcome of an implementation attempt."""

    success: bool
    attempts: int
    quality_passed: bool
    cost: float
    time_seconds: float
    files_changed: int
    lines_changed: int
    strategy_used: str
    error_messages: List[str]


@dataclass
class ProjectInsights:
    """Insights for a project."""

    total_implementations: int
    success_rate: float
    avg_attempts: float
    avg_cost: float
    avg_time_seconds: float
    common_failure_patterns: List[str]
    best_strategies: List[str]


class ImplementationTracker:
    """Tracks implementation outcomes and provides insights."""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize implementation tracker.

        Args:
            storage_path: Path to store tracking data
        """
        self.storage_path = storage_path or Path(".vaki/implementations.jsonl")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def record_implementation(
        self,
        project: str,
        issue: Issue,
        outcome: ImplementationOutcome,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record implementation outcome.

        Args:
            project: Project name
            issue: GitHub issue
            outcome: Implementation outcome
            metadata: Optional additional metadata
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "project": project,
            "issue_number": issue.number,
            "issue_title": issue.title,
            "issue_labels": [label.name for label in issue.labels],
            "outcome": asdict(outcome),
            "metadata": metadata or {}
        }

        # Append to JSONL file
        try:
            with open(self.storage_path, 'a') as f:
                f.write(json.dumps(record) + '\n')

            print(f"📊 Recorded implementation outcome for issue #{issue.number}")

        except IOError as e:
            print(f"⚠️  Failed to record implementation: {e}")

    def get_insights(self, project: str, limit: int = 100) -> ProjectInsights:
        """
        Get insights for a project.

        Args:
            project: Project name
            limit: Maximum number of recent records to analyze

        Returns:
            ProjectInsights
        """
        records = self._load_records(project, limit)

        if not records:
            return ProjectInsights(
                total_implementations=0,
                success_rate=0.0,
                avg_attempts=0.0,
                avg_cost=0.0,
                avg_time_seconds=0.0,
                common_failure_patterns=[],
                best_strategies=[]
            )

        # Calculate metrics
        total = len(records)
        successful = sum(1 for r in records if r["outcome"]["success"])
        success_rate = (successful / total) * 100 if total > 0 else 0.0

        avg_attempts = sum(r["outcome"]["attempts"] for r in records) / total
        avg_cost = sum(r["outcome"]["cost"] for r in records) / total
        avg_time = sum(r["outcome"]["time_seconds"] for r in records) / total

        # Find common failure patterns
        failures = [r for r in records if not r["outcome"]["success"]]
        failure_patterns: Dict[str, int] = {}

        for failure in failures:
            for error in failure["outcome"]["error_messages"]:
                # Simplify error message
                pattern = error.split(':')[0][:50]
                failure_patterns[pattern] = failure_patterns.get(pattern, 0) + 1

        common_failures = sorted(
            failure_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Find best strategies
        successes = [r for r in records if r["outcome"]["success"]]
        strategy_counts: Dict[str, int] = {}

        for success in successes:
            strategy = success["outcome"]["strategy_used"]
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        best_strategies = sorted(
            strategy_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        return ProjectInsights(
            total_implementations=total,
            success_rate=success_rate,
            avg_attempts=avg_attempts,
            avg_cost=avg_cost,
            avg_time_seconds=avg_time,
            common_failure_patterns=[f"{pattern} ({count}x)" for pattern, count in common_failures],
            best_strategies=[f"{strategy} ({count}x)" for strategy, count in best_strategies]
        )

    def suggest_improvements(
        self,
        project: str,
        issue_labels: List[str]
    ) -> List[str]:
        """
        Suggest improvements based on historical data.

        Args:
            project: Project name
            issue_labels: Labels for current issue

        Returns:
            List of suggestions
        """
        records = self._load_records(project, limit=50)

        if not records:
            return []

        suggestions = []

        # Find similar successful implementations
        similar_successes = [
            r for r in records
            if r["outcome"]["success"] and
            any(label in r["issue_labels"] for label in issue_labels)
        ]

        if similar_successes:
            # Get most common strategy for similar issues
            strategies = [r["outcome"]["strategy_used"] for r in similar_successes]
            if strategies:
                most_common = max(set(strategies), key=strategies.count)
                suggestions.append(f"Strategy '{most_common}' works well for similar issues")

        # Check for common pitfalls
        similar_failures = [
            r for r in records
            if not r["outcome"]["success"] and
            any(label in r["issue_labels"] for label in issue_labels)
        ]

        if similar_failures:
            errors = []
            for failure in similar_failures[:3]:
                errors.extend(failure["outcome"]["error_messages"])

            if errors:
                suggestions.append(f"Common pitfall: {errors[0][:100]}")

        return suggestions

    def print_insights(self, insights: ProjectInsights) -> None:
        """
        Print formatted insights.

        Args:
            insights: Insights to print
        """
        print("\n" + "=" * 70)
        print("📊 IMPLEMENTATION INSIGHTS")
        print("=" * 70)
        print(f"Total Implementations: {insights.total_implementations}")
        print(f"Success Rate: {insights.success_rate:.1f}%")
        print(f"Avg Attempts: {insights.avg_attempts:.1f}")
        print(f"Avg Cost: ${insights.avg_cost:.2f}")
        print(f"Avg Time: {insights.avg_time_seconds:.0f}s")

        if insights.best_strategies:
            print("\n✅ Best Strategies:")
            for strategy in insights.best_strategies:
                print(f"   • {strategy}")

        if insights.common_failure_patterns:
            print("\n❌ Common Failures:")
            for pattern in insights.common_failure_patterns:
                print(f"   • {pattern}")

        print("=" * 70)

    def _load_records(self, project: str, limit: int) -> List[Dict[str, Any]]:
        """
        Load implementation records for a project.

        Args:
            project: Project name
            limit: Maximum records to load

        Returns:
            List of records
        """
        if not self.storage_path.exists():
            return []

        records = []

        try:
            with open(self.storage_path, 'r') as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        if record.get("project") == project:
                            records.append(record)

                            if len(records) >= limit:
                                break

                    except json.JSONDecodeError:
                        continue

        except IOError:
            return []

        return records
