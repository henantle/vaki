"""Configuration loader for project settings."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field


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
class QualityConfig:
    """Quality gate configuration."""
    mode: str = "standard"  # strict, standard, permissive
    critical_gates: List[str] = field(default_factory=lambda: [
        "security_check", "syntax_check", "breaking_changes"
    ])
    required_gates: List[str] = field(default_factory=lambda: [
        "type_check", "tests_pass", "build", "lint"
    ])
    min_coverage: int = 80


@dataclass
class TicketAnalysisConfig:
    """Ticket analysis configuration."""
    enabled: bool = True
    min_clarity_score: int = 70
    ask_for_clarification: bool = True


@dataclass
class ImplementationConfig:
    """Implementation strategy configuration."""
    mode: str = "progressive"  # progressive, single-shot
    phases: List[str] = field(default_factory=lambda: [
        "research", "design", "implement", "test"
    ])
    incremental_validation: bool = True
    multi_strategy: bool = True
    max_strategies: int = 3
    use_checkpoints: bool = True


@dataclass
class HumanOversightConfig:
    """Human oversight configuration."""
    mode: str = "auto"  # auto, checkpoints, interactive
    require_approval_for: List[str] = field(default_factory=lambda: [
        "breaking_changes", "security_changes", "database_migrations"
    ])


@dataclass
class ResourceLimitsConfig:
    """Resource and cost limits configuration."""
    daily_cost_limit: float = 50.00
    per_issue_cost_limit: float = 10.00
    per_issue_token_limit: int = 200000
    max_implementation_time: int = 1800  # 30 minutes


@dataclass
class LearningConfig:
    """Learning and tracking configuration."""
    enabled: bool = True
    track_outcomes: bool = True
    use_insights: bool = True


@dataclass
class ProjectConfig:
    name: str
    description: str
    github: GitHubConfig
    filters: IssueFilters
    workspace: WorkspaceConfig
    context: Optional[str]
    prompt_template: Optional[str]
    quality: Optional[QualityConfig] = None
    ticket_analysis: Optional[TicketAnalysisConfig] = None
    implementation: Optional[ImplementationConfig] = None
    human_oversight: Optional[HumanOversightConfig] = None
    resources: Optional[ResourceLimitsConfig] = None
    learning: Optional[LearningConfig] = None


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

        # Load optional enhanced configurations with defaults
        quality_config = None
        if 'quality' in data:
            quality_config = QualityConfig(**data['quality'])

        ticket_analysis_config = None
        if 'ticket_analysis' in data:
            ticket_analysis_config = TicketAnalysisConfig(**data['ticket_analysis'])

        implementation_config = None
        if 'implementation' in data:
            implementation_config = ImplementationConfig(**data['implementation'])

        human_oversight_config = None
        if 'human_oversight' in data:
            human_oversight_config = HumanOversightConfig(**data['human_oversight'])

        resources_config = None
        if 'resources' in data:
            resources_config = ResourceLimitsConfig(**data['resources'])

        learning_config = None
        if 'learning' in data:
            learning_config = LearningConfig(**data['learning'])

        return ProjectConfig(
            name=data['name'],
            description=data['description'],
            github=GitHubConfig(**data['github']),
            filters=IssueFilters(**data['filters']),
            workspace=WorkspaceConfig(**data['workspace']),
            context=data.get('context'),
            prompt_template=data.get('prompt_template'),
            quality=quality_config,
            ticket_analysis=ticket_analysis_config,
            implementation=implementation_config,
            human_oversight=human_oversight_config,
            resources=resources_config,
            learning=learning_config
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
