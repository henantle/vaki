"""GitHub API client for issue and PR management."""

from typing import List, Optional
from github import Github
from github.Issue import Issue
from github.Repository import Repository
from github.PullRequest import PullRequest


class GitHubClient:
    """Handles GitHub API interactions."""

    def __init__(self, token: str):
        self.github = Github(token)
        self.token = token

    def get_repository(self, repo_name: str) -> Repository:
        """Get a GitHub repository."""
        return self.github.get_repo(repo_name)

    def get_assigned_issues(
        self,
        repo_name: str,
        assignee: str,
        labels: Optional[List[str]] = None,
        state: str = "open"
    ) -> List[Issue]:
        """Get issues assigned to a user."""
        repo = self.get_repository(repo_name)

        # Build query parameters
        kwargs = {
            "state": state,
            "assignee": assignee
        }

        if labels:
            kwargs["labels"] = labels

        issues = repo.get_issues(**kwargs)

        # Filter out pull requests (GitHub API includes them in issues)
        return [issue for issue in issues if not issue.pull_request]

    def get_issue(self, repo_name: str, issue_number: int) -> Issue:
        """Get a specific issue by number."""
        repo = self.get_repository(repo_name)
        return repo.get_issue(issue_number)

    def create_pull_request(
        self,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str
    ) -> PullRequest:
        """Create a pull request."""
        repo = self.get_repository(repo_name)
        return repo.create_pull(
            title=title,
            body=body,
            head=head,
            base=base
        )

    def get_repo_url_with_token(self, repo_name: str) -> str:
        """Get repository clone URL with authentication token."""
        return f"https://{self.token}@github.com/{repo_name}.git"

    def comment_on_issue(self, repo_name: str, issue_number: int, message: str):
        """Add a comment to an issue."""
        issue = self.get_issue(repo_name, issue_number)
        issue.create_comment(message)

    def close_issue(self, repo_name: str, issue_number: int):
        """Close an issue."""
        issue = self.get_issue(repo_name, issue_number)
        issue.edit(state="closed")
