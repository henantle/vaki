"""Workspace management for issue implementation."""

import os
import subprocess
from pathlib import Path
from typing import Optional
from github.Issue import Issue
from .security import sanitize, sanitize_url


class WorkspaceManager:
    """Manages in-place workspace for issue implementation."""

    def find_project_directory(self, repo_name: str) -> Optional[Path]:
        """
        Find project directory in parent folder.

        Args:
            repo_name: Repository name (e.g., "vainamoinen")

        Returns:
            Path to project directory or None if not found
        """
        # Extract repo name from full name (e.g., "henantle/vainamoinen" -> "vainamoinen")
        if "/" in repo_name:
            repo_name = repo_name.split("/")[1]

        # Check parent directory
        parent = Path.cwd().parent
        project_path = parent / repo_name

        if project_path.exists() and project_path.is_dir():
            # Verify it's a git repository
            if (project_path / ".git").exists():
                return project_path

        return None

    def prepare_workspace(
        self,
        workspace: Path,
        issue: Issue,
        branch_name: str,
        base_branch: str = "main"
    ) -> bool:
        """
        Prepare workspace for issue implementation.

        Args:
            workspace: Path to the project directory
            issue: GitHub issue object
            branch_name: New branch name to create
            base_branch: Base branch to branch from

        Returns:
            True if successful, False otherwise
        """
        print(f"📁 Using project directory: {workspace}")

        # Ensure we're on base branch and up to date
        try:
            # Stash any changes
            subprocess.run(
                ["git", "stash"],
                cwd=workspace,
                capture_output=True
            )

            # Checkout base branch
            result = subprocess.run(
                ["git", "checkout", base_branch],
                cwd=workspace,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"⚠️  Warning: Could not checkout {base_branch}: {sanitize(result.stderr)}")
                return False

            # Pull latest changes
            subprocess.run(
                ["git", "pull", "origin", base_branch],
                cwd=workspace,
                capture_output=True
            )

            # Create and checkout new branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=workspace,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                # Branch might exist, try to checkout
                subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=workspace,
                    check=True,
                    capture_output=True
                )

            print(f"🌿 Branch: {branch_name}")
            return True

        except Exception as e:
            print(f"❌ Error preparing workspace: {sanitize(str(e))}")
            return False

    def create_task_file(
        self,
        workspace: Path,
        issue: Issue,
        context: str = "",
        prompt_template: str = ""
    ) -> None:
        """
        Create a TASK.md file with issue details and instructions.

        Args:
            workspace: Workspace path
            issue: GitHub issue object
            context: Project-specific context
            prompt_template: System prompt template
        """
        task_content = f"""# Task: {issue.title}

**Issue**: #{issue.number}
**Repository**: {issue.repository.full_name}
**URL**: {issue.html_url}

## Description

{issue.body or 'No description provided'}

"""

        if context:
            task_content += f"""## Project Context

{context}

"""

        if prompt_template:
            task_content += f"""## Guidelines & Best Practices

{prompt_template}

"""

        task_content += """## Instructions

Implement this issue following the guidelines above. Make clear, logical commits with descriptive messages.

When complete:
1. Ensure all changes are committed
2. Run any relevant tests
3. Exit Claude Code

The orchestrator will handle PR creation automatically.
"""

        task_file = workspace / "TASK.md"
        with open(task_file, 'w') as f:
            f.write(task_content)

        print(f"📋 Task file created: TASK.md")

    def cleanup_task_file(self, workspace: Path) -> None:
        """Remove TASK.md file."""
        task_file = workspace / "TASK.md"
        if task_file.exists():
            task_file.unlink()
            print(f"🧹 Removed TASK.md")

    def has_commits(self, workspace: Path, base_branch: str = "main") -> bool:
        """Check if workspace has commits ahead of base branch."""
        result = subprocess.run(
            ["git", "log", f"{base_branch}..HEAD", "--oneline"],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())

    def get_branch_name(self, workspace: Path) -> str:
        """Get current branch name."""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    def push_changes(self, workspace: Path, branch_name: str) -> None:
        """Push changes to remote."""
        print(f"\n🚀 Pushing branch: {branch_name}")

        # Try normal push first
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=workspace,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # If normal push failed, try force push with lease (safer than force)
            if "rejected" in result.stderr or "non-fast-forward" in result.stderr:
                print("⚠️  Branch exists on remote, force pushing...")
                subprocess.run(
                    ["git", "push", "--force-with-lease", "origin", branch_name],
                    cwd=workspace,
                    check=True
                )
            else:
                # Other error, raise it
                print(f"❌ Push failed: {sanitize(result.stderr)}")
                raise subprocess.CalledProcessError(result.returncode, result.args, sanitize(result.stderr))

        print("✅ Changes pushed")

    def show_summary(self, workspace: Path, base_branch: str = "main") -> None:
        """Show summary of changes."""
        print("\n" + "=" * 70)
        print("📊 CHANGES SUMMARY")
        print("=" * 70)

        # Show commits
        result = subprocess.run(
            ["git", "log", f"{base_branch}..HEAD", "--oneline"],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        print("\nCommits:")
        print(result.stdout)

        # Show file stats
        subprocess.run(
            ["git", "diff", base_branch, "--stat"],
            cwd=workspace
        )
        print("=" * 70)

    def return_to_base_branch(self, workspace: Path, base_branch: str = "main") -> None:
        """Return to base branch after PR creation."""
        try:
            subprocess.run(
                ["git", "checkout", base_branch],
                cwd=workspace,
                check=True,
                capture_output=True
            )
            print(f"✅ Returned to {base_branch} branch")
        except Exception as e:
            print(f"⚠️  Could not return to {base_branch}: {sanitize(str(e))}")
