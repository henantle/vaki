"""Comprehensive logging system for implementation debugging and analysis."""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class LogEntry:
    """Single log entry."""

    timestamp: str
    level: str  # info, warning, error
    phase: str
    message: str
    data: Optional[Dict[str, Any]] = None


class ImplementationLogger:
    """Comprehensive logging for debugging and analysis."""

    def __init__(self, project: str, issue_number: int):
        """
        Initialize implementation logger.

        Args:
            project: Project name
            issue_number: Issue number
        """
        self.project = project
        self.issue_number = issue_number
        self.log_dir = Path(f".vaki/logs/{project}/issue-{issue_number}")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.start_time = datetime.now()
        self.current_phase: Optional[str] = None
        self.logs: List[LogEntry] = []

        # Initialize log files
        self.main_log = self.log_dir / "implementation.log"
        self.agent_log = self.log_dir / "agent_interactions.jsonl"
        self.actions_log = self.log_dir / "actions.jsonl"
        self.metrics_log = self.log_dir / "metrics.json"

        self._write_header()

    def _write_header(self) -> None:
        """Write log file header."""
        with open(self.main_log, 'w') as f:
            f.write(f"Implementation Log - {self.project} Issue #{self.issue_number}\n")
            f.write(f"Started: {self.start_time.isoformat()}\n")
            f.write("=" * 70 + "\n\n")

    def log_phase(self, phase: str, action: str = "start", data: Optional[Dict] = None) -> None:
        """
        Log phase entry/exit.

        Args:
            phase: Phase name
            action: "start" or "end"
            data: Optional phase data
        """
        if action == "start":
            self.current_phase = phase

        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="info",
            phase=phase,
            message=f"Phase {action}: {phase}",
            data=data
        )

        self.logs.append(entry)
        self._write_log(entry)

    def log_info(self, message: str, data: Optional[Dict] = None) -> None:
        """
        Log info message.

        Args:
            message: Log message
            data: Optional additional data
        """
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="info",
            phase=self.current_phase or "unknown",
            message=message,
            data=data
        )

        self.logs.append(entry)
        self._write_log(entry)

    def log_warning(self, message: str, data: Optional[Dict] = None) -> None:
        """
        Log warning message.

        Args:
            message: Warning message
            data: Optional additional data
        """
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="warning",
            phase=self.current_phase or "unknown",
            message=message,
            data=data
        )

        self.logs.append(entry)
        self._write_log(entry)

    def log_error(self, message: str, data: Optional[Dict] = None) -> None:
        """
        Log error message.

        Args:
            message: Error message
            data: Optional additional data
        """
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="error",
            phase=self.current_phase or "unknown",
            message=message,
            data=data
        )

        self.logs.append(entry)
        self._write_log(entry)

    def log_agent_interaction(
        self,
        prompt: str,
        response: str,
        tokens: Optional[Dict[str, int]] = None
    ) -> None:
        """
        Log agent interaction.

        Args:
            prompt: Prompt sent to agent
            response: Agent response
            tokens: Token usage dict {"input": X, "output": Y}
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "phase": self.current_phase,
            "prompt": prompt[:1000] + ("..." if len(prompt) > 1000 else ""),
            "response": response[:1000] + ("..." if len(response) > 1000 else ""),
            "tokens": tokens or {}
        }

        with open(self.agent_log, 'a') as f:
            f.write(json.dumps(interaction) + '\n')

    def log_action(self, action: Dict[str, Any], result: str) -> None:
        """
        Log action execution.

        Args:
            action: Action dict
            result: Result message
        """
        action_log = {
            "timestamp": datetime.now().isoformat(),
            "phase": self.current_phase,
            "action": action,
            "result": result[:500] + ("..." if len(result) > 500 else "")
        }

        with open(self.actions_log, 'a') as f:
            f.write(json.dumps(action_log) + '\n')

    def log_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Log implementation metrics.

        Args:
            metrics: Metrics dictionary
        """
        metrics["timestamp"] = datetime.now().isoformat()
        metrics["duration_seconds"] = (datetime.now() - self.start_time).total_seconds()

        with open(self.metrics_log, 'w') as f:
            json.dump(metrics, f, indent=2)

    def create_debug_bundle(self, workspace: Path) -> Path:
        """
        Create debug bundle with all logs and git history.

        Args:
            workspace: Project workspace

        Returns:
            Path to debug bundle
        """
        bundle_path = self.log_dir / "debug_bundle"
        bundle_path.mkdir(exist_ok=True)

        # Copy all log files
        for log_file in self.log_dir.glob("*.log"):
            shutil.copy2(log_file, bundle_path)

        for log_file in self.log_dir.glob("*.jsonl"):
            shutil.copy2(log_file, bundle_path)

        for log_file in self.log_dir.glob("*.json"):
            shutil.copy2(log_file, bundle_path)

        # Export git history
        try:
            import subprocess
            result = subprocess.run(
                ["git", "log", "--oneline", "-20"],
                cwd=workspace,
                capture_output=True,
                text=True
            )

            with open(bundle_path / "git_history.txt", 'w') as f:
                f.write(result.stdout)

            # Export git diff
            result = subprocess.run(
                ["git", "diff"],
                cwd=workspace,
                capture_output=True,
                text=True
            )

            with open(bundle_path / "git_diff.txt", 'w') as f:
                f.write(result.stdout)

        except Exception:
            pass

        # Create summary
        self._create_summary(bundle_path)

        print(f"📦 Debug bundle created: {bundle_path}")
        return bundle_path

    def _create_summary(self, bundle_path: Path) -> None:
        """
        Create summary file.

        Args:
            bundle_path: Path to bundle directory
        """
        duration = (datetime.now() - self.start_time).total_seconds()

        summary = f"""Implementation Summary
=====================

Project: {self.project}
Issue: #{self.issue_number}
Duration: {duration:.0f}s ({duration/60:.1f}m)
Started: {self.start_time.isoformat()}
Ended: {datetime.now().isoformat()}

Log Statistics:
- Total entries: {len(self.logs)}
- Info: {sum(1 for log in self.logs if log.level == 'info')}
- Warnings: {sum(1 for log in self.logs if log.level == 'warning')}
- Errors: {sum(1 for log in self.logs if log.level == 'error')}

Phases:
"""

        phases = list(set(log.phase for log in self.logs if log.phase))
        for phase in phases:
            phase_logs = [log for log in self.logs if log.phase == phase]
            summary += f"- {phase}: {len(phase_logs)} entries\n"

        with open(bundle_path / "summary.txt", 'w') as f:
            f.write(summary)

    def _write_log(self, entry: LogEntry) -> None:
        """
        Write log entry to file.

        Args:
            entry: Log entry
        """
        with open(self.main_log, 'a') as f:
            timestamp = entry.timestamp.split('T')[1][:8]  # HH:MM:SS
            level_icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}
            icon = level_icon.get(entry.level, "•")

            f.write(f"[{timestamp}] {icon}  [{entry.phase}] {entry.message}\n")

            if entry.data:
                f.write(f"   Data: {json.dumps(entry.data, indent=2)}\n")

    def get_error_count(self) -> int:
        """
        Get count of error log entries.

        Returns:
            Number of errors
        """
        return sum(1 for log in self.logs if log.level == "error")

    def get_warning_count(self) -> int:
        """
        Get count of warning log entries.

        Returns:
            Number of warnings
        """
        return sum(1 for log in self.logs if log.level == "warning")
