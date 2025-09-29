"""Configuration loader for project settings."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class GitHubConfig:
    repo: str
    base_branch: str
    username: str
    email: str


@dataclass
class IssueFilters:
    assignee: str
    labels: List[str]
    state: str


@dataclass
class WorkspaceConfig:
    temp_dir: str


@dataclass
class ProjectConfig:
    name: str
    description: str
    github: GitHubConfig
    filters: IssueFilters
    workspace: WorkspaceConfig
    context: Optional[str]
    prompt_template: Optional[str]


class ConfigLoader:
    """Loads and manages project configurations."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.projects_dir = self.base_dir / "projects"

    def load_project(self, project_name: str) -> ProjectConfig:
        """Load a specific project configuration."""
        config_file = self.projects_dir / f"{project_name}.yml"

        if not config_file.exists():
            raise FileNotFoundError(f"Project config not found: {config_file}")

        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)

        return ProjectConfig(
            name=data['name'],
            description=data['description'],
            github=GitHubConfig(**data['github']),
            filters=IssueFilters(**data['filters']),
            workspace=WorkspaceConfig(**data['workspace']),
            context=data.get('context'),
            prompt_template=data.get('prompt_template')
        )

    def list_projects(self) -> List[str]:
        """List all available project configurations."""
        if not self.projects_dir.exists():
            return []

        return [
            f.stem for f in self.projects_dir.glob("*.yml")
        ]

    def load_context(self, context_path: Optional[str]) -> str:
        """Load project context file."""
        if not context_path:
            return ""

        full_path = self.base_dir / context_path
        if not full_path.exists():
            return ""

        with open(full_path, 'r') as f:
            return f.read()

    def load_prompt_template(self, template_path: Optional[str]) -> str:
        """Load system prompt template."""
        if not template_path:
            return ""

        full_path = self.base_dir / template_path
        if not full_path.exists():
            return ""

        with open(full_path, 'r') as f:
            return f.read()
