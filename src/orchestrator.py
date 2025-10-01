"""Main orchestrator for the agentic workflow."""

import os
from pathlib import Path
from typing import Optional
from github.Issue import Issue

from .config import ConfigLoader, ProjectConfig
from .github_client import GitHubClient
from .workspace import WorkspaceManager


class AgentOrchestrator:
    """Orchestrates the full workflow: fetch issues → implement → create PR."""

    def __init__(self, github_token: str, base_dir: str = ".") -> None:
        self.github_token = github_token
        self.config_loader = ConfigLoader(base_dir)
        self.github_client = GitHubClient(github_token)
        self.workspace_manager = WorkspaceManager()

    def run_project(self, project_name: str, issue_number: Optional[int] = None) -> None:
        """
        Run the workflow for a project.

        Args:
            project_name: Name of the project (YAML config name)
            issue_number: Specific issue number, or None to process all assigned issues
        """
        # Load project configuration
        config = self.config_loader.load_project(project_name)
        print(f"\n{'=' * 70}")
        print(f"📦 PROJECT: {config.name}")
        print(f"📝 {config.description}")
        print(f"{'=' * 70}\n")

        # Get issues
        if issue_number:
            issues = [self.github_client.get_issue(config.github.repo, issue_number)]
        else:
            issues = self.github_client.get_assigned_issues(
                repo_name=config.github.repo,
                assignee=config.filters.assignee,
                labels=config.filters.labels,
                state=config.filters.state
            )

        if not issues:
            print("✅ No issues found to process")
            return

        print(f"📋 Found {len(issues)} issue(s) to process:\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. #{issue.number}: {issue.title}")
        print()

        # Process each issue
        for issue in issues:
            self._process_issue(issue, config)

    def _process_issue(self, issue: Issue, config: ProjectConfig) -> None:
        """Process a single issue."""
        print(f"\n{'=' * 70}")
        print(f"🎯 PROCESSING ISSUE #{issue.number}")
        print(f"{'=' * 70}")
        print(f"Title: {issue.title}")
        print(f"URL: {issue.html_url}\n")

        # Find project directory in parent folder
        workspace = self.workspace_manager.find_project_directory(config.github.repo)

        if not workspace:
            print(f"❌ Error: Project directory not found in parent folder")
            print(f"Expected to find: {config.github.repo.split('/')[-1]}")
            print(f"Searched in: {os.path.abspath('../')}")
            print("\n💡 Make sure:")
            print(f"  1. Your project is cloned in the parent directory")
            print(f"  2. VÄKI and your project are sibling folders")
            return

        # Create branch name
        branch_name = f"fix/issue-{issue.number}"

        # Prepare workspace (create branch, etc.)
        success = self.workspace_manager.prepare_workspace(
            workspace=workspace,
            issue=issue,
            branch_name=branch_name,
            base_branch=config.github.base_branch
        )

        if not success:
            print("❌ Failed to prepare workspace")
            return

        # Load context and templates
        context = self.config_loader.load_context(config.context)
        prompt_template = self.config_loader.load_prompt_template(config.prompt_template)

        # Create task file
        self.workspace_manager.create_task_file(
            workspace=workspace,
            issue=issue,
            context=context,
            prompt_template=prompt_template
        )

        # Print instructions for manual implementation
        print("\n" + "=" * 70)
        print("📋 WORKSPACE READY - NOW IMPLEMENT WITH CLAUDE CODE")
        print("=" * 70)
        print("\n✨ Copy and paste these commands:\n")
        print(f"cd {workspace}")
        print(f"claude-code")
        print("\n💡 Claude Code will start. Tell it:")
        print('   "Read TASK.md and implement the issue. Make clear commits."')
        print("\n⚠️  When done, type 'exit' in Claude Code, then come back here.")
        print("=" * 70)

        input("\n⏸️  Press ENTER when you've finished implementing and exited Claude Code...")
        print()

        # Clean up TASK.md
        self.workspace_manager.cleanup_task_file(workspace)

        # Check if commits were made
        if not self.workspace_manager.has_commits(workspace, config.github.base_branch):
            print("\n❌ No commits found. Skipping PR creation.")
            self.workspace_manager.return_to_base_branch(workspace, config.github.base_branch)
            return

        # Show summary
        self.workspace_manager.show_summary(workspace, config.github.base_branch)

        # Push changes and create PR automatically
        print("\n" + "=" * 70)
        print("🚀 CREATING PULL REQUEST")
        print("=" * 70)

        try:
            # Push
            self.workspace_manager.push_changes(workspace, branch_name)

            # Create PR
            pr = self.github_client.create_pull_request(
                repo_name=config.github.repo,
                title=f"Fix: {issue.title}",
                body=f"Closes #{issue.number}\n\n{issue.body or ''}",
                head=branch_name,
                base=config.github.base_branch
            )
            print(f"\n✅ Pull Request created: {pr.html_url}")

            # Return to base branch
            self.workspace_manager.return_to_base_branch(workspace, config.github.base_branch)

        except Exception as e:
            from .security import sanitize
            print(f"\n❌ Error creating PR: {sanitize(str(e))}")
            print("\n💡 You can manually push and create PR:")
            print(f"  cd {workspace}")
            print(f"  git push origin {branch_name}")
            self.workspace_manager.return_to_base_branch(workspace, config.github.base_branch)

    def _handle_interruption(self, workspace: Path, config: ProjectConfig) -> None:
        """Handle workflow interruption."""
        print("\n" + "=" * 70)
        print("What would you like to do?")
        print("  1. Continue later (preserve workspace)")
        print("  2. Abort and clean up workspace")
        choice = input("Choice (1/2): ")

        if choice == "2":
            self.workspace_manager.cleanup(workspace)
        else:
            print(f"\n📂 Workspace preserved: {workspace}")
            print("You can continue working later")

    def list_projects(self) -> None:
        """List all available projects."""
        projects = self.config_loader.list_projects()
        if not projects:
            print("No projects configured yet.")
            print("Add project configs to the 'projects/' directory")
            return

        print(f"\n📦 Available Projects ({len(projects)}):\n")
        for project in projects:
            config = self.config_loader.load_project(project)
            print(f"  • {config.name}")
            print(f"    {config.description}")
            print(f"    Repo: {config.github.repo}")
            print()
