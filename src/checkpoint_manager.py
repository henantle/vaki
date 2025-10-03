"""Checkpoint management for implementation rollback capability."""

import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Checkpoint:
    """Represents a code checkpoint for rollback."""

    name: str
    timestamp: datetime
    commit_hash: str
    description: str
    quality_score: float = 0.0


class CheckpointManager:
    """Manages implementation checkpoints for safe rollback."""

    def __init__(self, workspace: Path):
        """
        Initialize checkpoint manager.

        Args:
            workspace: Project workspace path
        """
        self.workspace = workspace
        self.checkpoints: List[Checkpoint] = []

    def create_checkpoint(
        self,
        name: str,
        description: str = "",
        quality_score: float = 0.0
    ) -> Optional[Checkpoint]:
        """
        Create a checkpoint of current state.

        Args:
            name: Checkpoint name
            description: Description of what was completed
            quality_score: Quality assessment score (0-100)

        Returns:
            Checkpoint object if successful, None otherwise
        """
        try:
            # Create a git commit to mark this checkpoint
            # First, stage all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.workspace,
                check=True,
                capture_output=True
            )

            # Create checkpoint commit
            commit_message = f"[CHECKPOINT] {name}\n\n{description}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_message, "--allow-empty"],
                cwd=self.workspace,
                capture_output=True,
                text=True
            )

            # Get commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                check=True
            )

            commit_hash = hash_result.stdout.strip()

            checkpoint = Checkpoint(
                name=name,
                timestamp=datetime.now(),
                commit_hash=commit_hash,
                description=description,
                quality_score=quality_score
            )

            self.checkpoints.append(checkpoint)
            print(f"📍 Checkpoint created: {name} ({commit_hash[:7]})")

            return checkpoint

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to create checkpoint: {e}")
            return None

    def rollback_to(self, checkpoint: Checkpoint) -> bool:
        """
        Rollback to a specific checkpoint.

        Args:
            checkpoint: Checkpoint to rollback to

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"⏪ Rolling back to checkpoint: {checkpoint.name}")

            # Reset to checkpoint commit
            subprocess.run(
                ["git", "reset", "--hard", checkpoint.commit_hash],
                cwd=self.workspace,
                check=True,
                capture_output=True
            )

            print(f"✅ Rolled back to {checkpoint.name}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to rollback: {e}")
            return False

    def get_best_checkpoint(self) -> Optional[Checkpoint]:
        """
        Get checkpoint with highest quality score.

        Returns:
            Best checkpoint or None if no checkpoints exist
        """
        if not self.checkpoints:
            return None

        return max(self.checkpoints, key=lambda c: c.quality_score)

    def list_checkpoints(self) -> List[Checkpoint]:
        """
        Get list of all checkpoints.

        Returns:
            List of checkpoints
        """
        return self.checkpoints.copy()

    def cleanup_checkpoints(self) -> None:
        """Remove checkpoint commits (squash them)."""
        # This would squash checkpoint commits
        # For now, just clear the list
        self.checkpoints.clear()
