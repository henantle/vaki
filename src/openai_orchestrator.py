"""OpenAI-powered automated implementation orchestrator."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, TypedDict, Union, Literal
from github.Issue import Issue

from .config import ConfigLoader, ProjectConfig
from .github_client import GitHubClient
from .workspace import WorkspaceManager
from .openai_agent import OpenAIAgent
from .security import sanitize

# Import new enhancement modules
from .ticket_analyzer import TicketAnalyzer
from .quality_gates import QualityGate
from .codebase_analyzer import CodebaseAnalyzer
from .resource_manager import ResourceManager, BudgetConfig
from .checkpoint_manager import CheckpointManager
from .implementation_tracker import ImplementationTracker, ImplementationOutcome
from .strategy_evaluator import StrategyEvaluator
from .incremental_validator import IncrementalValidator
from .implementation_logger import ImplementationLogger


# Action type definitions
class ReadFileAction(TypedDict):
    """Action to read a file."""
    action: Literal["read_file"]
    path: str


class WriteFileAction(TypedDict):
    """Action to write a file."""
    action: Literal["write_file"]
    path: str
    content: str


class EditFileAction(TypedDict):
    """Action to edit a file."""
    action: Literal["edit_file"]
    path: str
    search: str
    replace: str


class RunCommandAction(TypedDict):
    """Action to run a command."""
    action: Literal["run_command"]
    command: str


class CommitAction(TypedDict):
    """Action to create a commit."""
    action: Literal["commit"]
    message: str


class DoneAction(TypedDict):
    """Action to signal completion."""
    action: Literal["done"]
    summary: str


# Union of all action types
Action = Union[
    ReadFileAction,
    WriteFileAction,
    EditFileAction,
    RunCommandAction,
    CommitAction,
    DoneAction
]


class OpenAIOrchestrator:
    """Orchestrates fully automated workflow using OpenAI API."""

    def __init__(self, github_token: str, openai_api_key: str, base_dir: str = ".") -> None:
        self.github_token = github_token
        self.config_loader = ConfigLoader(base_dir)
        self.github_client = GitHubClient(github_token)
        self.workspace_manager = WorkspaceManager()
        self.agent = OpenAIAgent(openai_api_key)
        self.max_iterations = 20  # Safety limit

        # Initialize enhancement modules
        self.ticket_analyzer = TicketAnalyzer(self.agent, self.github_client)
        self.strategy_evaluator = StrategyEvaluator(self.agent)
        self.tracker = ImplementationTracker()

        # Resource manager will be initialized with config-specific budget
        self.resource_manager: Optional[ResourceManager] = None

    def run_project(self, project_name: str, issue_number: Optional[int] = None) -> None:
        """
        Run the automated workflow for a project.

        Args:
            project_name: Name of the project (YAML config name)
            issue_number: Specific issue number, or None to process all assigned issues
        """
        # Load project configuration
        config = self.config_loader.load_project(project_name)
        print(f"\n{'=' * 70}")
        print(f"📦 PROJECT: {config.name} (OpenAI Automated Mode)")
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

    def run_manual_ticket(self, project_name: str, manual_ticket) -> None:
        """
        Process a manual ticket from external sources (Slack, email, Jira, etc.).

        Args:
            project_name: Name of the project (YAML config name)
            manual_ticket: ManualTicket object with ticket details
        """
        # Load project configuration
        config = self.config_loader.load_project(project_name)
        print(f"\n{'=' * 70}")
        print(f"📦 PROJECT: {config.name} (OpenAI Automated Mode)")
        print(f"📝 {config.description}")
        print(f"{'=' * 70}\n")

        print(f"📋 Processing manual ticket:")
        print(f"   Source: {manual_ticket.source}")
        print(f"   #{manual_ticket.number}: {manual_ticket.title}\n")

        # Process the manual ticket
        self._process_issue(manual_ticket, config, is_manual=True)

    def _process_issue(self, issue, config: ProjectConfig, is_manual: bool = False) -> None:
        """
        Process a single issue with enhanced workflow.

        Args:
            issue: GitHub Issue or ManualTicket object
            config: Project configuration
            is_manual: True if processing a manual ticket
        """
        print(f"\n{'=' * 70}")
        if is_manual:
            print(f"🤖 AUTO-PROCESSING MANUAL TICKET #{issue.number}")
        else:
            print(f"🤖 AUTO-PROCESSING ISSUE #{issue.number}")
        print(f"{'=' * 70}")
        print(f"Title: {issue.title}")
        if not is_manual:
            print(f"URL: {issue.html_url}")
        else:
            print(f"Source: {issue.source}")
        print()

        # Initialize implementation logger
        logger = ImplementationLogger(config.name, issue.number)
        logger.log_phase("initialization", "start")

        # Initialize resource manager with project-specific budget
        if config.resources:
            budget = BudgetConfig(
                daily_cost_limit=config.resources.daily_cost_limit,
                per_issue_cost_limit=config.resources.per_issue_cost_limit,
                per_issue_token_limit=config.resources.per_issue_token_limit
            )
            self.resource_manager = ResourceManager(budget, model="gpt-4o")
            self.resource_manager.start_issue_tracking()
            logger.log_info("Resource tracking enabled", {
                "daily_limit": budget.daily_cost_limit,
                "per_issue_limit": budget.per_issue_cost_limit
            })

        # Find project directory
        workspace = self.workspace_manager.find_project_directory(config.github.repo)

        if not workspace:
            logger.log_error("Project directory not found")
            print(f"❌ Error: Project directory not found in parent folder")
            print(f"Expected to find: {config.github.repo.split('/')[-1]}")
            return

        # Load context and templates
        context = self.config_loader.load_context(config.context)
        prompt_template = self.config_loader.load_prompt_template(config.prompt_template)

        # PHASE 0: Ticket Analysis
        if config.ticket_analysis and config.ticket_analysis.enabled:
            print("\n" + "=" * 70)
            print("📋 PHASE 0: TICKET ANALYSIS")
            print("=" * 70)
            logger.log_phase("ticket_analysis", "start")

            analysis = self.ticket_analyzer.analyze_ticket(issue, context)
            self.ticket_analyzer.print_analysis_summary(analysis)
            logger.log_info("Ticket analyzed", {
                "clarity_score": analysis.clarity_score,
                "complexity": analysis.estimated_complexity
            })

            if analysis.clarity_score < config.ticket_analysis.min_clarity_score:
                print(f"\n⚠️  Ticket clarity score ({analysis.clarity_score}) below threshold ({config.ticket_analysis.min_clarity_score})")

                if config.ticket_analysis.ask_for_clarification:
                    self.ticket_analyzer.request_clarification(issue, analysis)
                    logger.log_warning("Requested clarification from issue author")
                    print("✅ Posted clarification questions to GitHub issue")
                    return
                else:
                    print("⚠️  Proceeding despite low clarity (ask_for_clarification disabled)")

            logger.log_phase("ticket_analysis", "end")
        else:
            # Simple analysis for complexity estimation
            analysis = self.ticket_analyzer.analyze_ticket(issue, context)

        # Resource budget check
        if self.resource_manager:
            estimate = self.resource_manager.get_cost_estimate(len(context), analysis.estimated_complexity)
            print(f"\n💰 Cost Estimate: ${estimate.cost:.2f} ({estimate.tokens:,} tokens)")

            if not self.resource_manager.check_quota("implement", estimate.tokens):
                logger.log_error("Budget exceeded", {"estimate": estimate.cost})
                print("❌ Implementation would exceed budget limits")
                return

        # Codebase Analysis
        print("\n" + "=" * 70)
        print("🔍 CODEBASE ANALYSIS")
        print("=" * 70)
        logger.log_phase("codebase_analysis", "start")

        codebase_analyzer = CodebaseAnalyzer(workspace)
        architecture = codebase_analyzer.get_architecture_summary()
        print(architecture)
        logger.log_info("Codebase analyzed")
        logger.log_phase("codebase_analysis", "end")

        # Create branch name
        if is_manual:
            branch_name = f"openai/manual-{issue.number}"
        else:
            branch_name = f"openai/issue-{issue.number}"

        # Prepare workspace
        success = self.workspace_manager.prepare_workspace(
            workspace=workspace,
            issue=issue,
            branch_name=branch_name,
            base_branch=config.github.base_branch
        )

        if not success:
            logger.log_error("Failed to prepare workspace")
            print("❌ Failed to prepare workspace")
            return

        # Initialize agent with enhanced project context
        enhanced_context = f"{context}\n\n{architecture}"
        self.agent.initialize_with_project_context(
            project_context=enhanced_context,
            coding_standards=prompt_template
        )

        # Strategy Generation (if enabled)
        strategies = []
        if config.implementation and config.implementation.multi_strategy:
            print("\n" + "=" * 70)
            print("🎯 STRATEGY GENERATION")
            print("=" * 70)
            logger.log_phase("strategy_generation", "start")

            strategies = self.strategy_evaluator.generate_strategies(issue, enhanced_context, analysis)
            self.strategy_evaluator.print_strategies(strategies)

            # Rank strategies
            ranked_strategies = self.strategy_evaluator.rank_strategies(strategies, criteria={
                "safety": 0.4,
                "quality": 0.3,
                "speed": 0.2,
                "simplicity": 0.1
            })
            print(f"\n✅ Generated {len(ranked_strategies)} strategies (ranked by criteria)")
            logger.log_info("Strategies generated", {"count": len(strategies)})
            logger.log_phase("strategy_generation", "end")
        else:
            # Create default strategy
            from .strategy_evaluator import ImplementationStrategy
            ranked_strategies = [ImplementationStrategy(
                name="Standard Implementation",
                approach="Direct implementation following project standards",
                pros=["Straightforward", "Well-tested approach"],
                cons=["May not explore alternatives"],
                estimated_complexity=analysis.estimated_complexity,
                risk_level="medium",
                estimated_time="15-30 minutes"
            )]

        # Initialize quality gate
        quality_gate = None
        if config.quality:
            quality_gate = QualityGate(workspace, config.quality)
            logger.log_info("Quality gates configured", {"mode": config.quality.mode})

        # Initialize checkpoint manager
        checkpoint_mgr = None
        if config.implementation and config.implementation.use_checkpoints:
            checkpoint_mgr = CheckpointManager(workspace)
            logger.log_info("Checkpoint management enabled")

        # Initialize incremental validator
        incremental_validator = None
        if config.implementation and config.implementation.incremental_validation:
            incremental_validator = IncrementalValidator(workspace)
            logger.log_info("Incremental validation enabled")

        # Get insights from past implementations
        insights = self.tracker.get_insights(config.name)
        if insights.total_attempts > 0:
            print(f"\n📊 Historical Insights: {insights.success_rate:.1%} success rate over {insights.total_attempts} attempts")
            suggestions = self.tracker.suggest_improvements(config.name, [label.name for label in issue.labels])
            if suggestions:
                print("💡 Suggestions based on history:")
                for suggestion in suggestions[:3]:
                    print(f"   • {suggestion}")

        # Create task-focused implementation prompt
        initial_prompt = self.agent.create_implementation_prompt(
            issue_title=issue.title,
            issue_body=issue.body or ""
        )

        implementation_start_time = __import__('datetime').datetime.now()

        try:
            # Try strategies with checkpoints and rollback capability
            strategy_success = False
            final_strategy_used = None
            verification_passed = False
            verification_feedback = ""

            for strategy_idx, strategy in enumerate(ranked_strategies, 1):
                print("\n" + "=" * 70)
                print(f"🎯 STRATEGY {strategy_idx}/{len(ranked_strategies)}: {strategy.name}")
                print("=" * 70)
                print(f"Approach: {strategy.approach}")
                print(f"Risk: {strategy.risk_level} | Complexity: {strategy.estimated_complexity}/10")
                logger.log_phase(f"strategy_{strategy_idx}", "start", {"name": strategy.name})

                # Create checkpoint before trying strategy
                if checkpoint_mgr:
                    checkpoint = checkpoint_mgr.create_checkpoint(
                        name=f"before_strategy_{strategy_idx}",
                        description=f"Before attempting: {strategy.name}",
                        quality_score=0.0
                    )
                    if checkpoint:
                        print(f"📍 Checkpoint created: {checkpoint.commit_hash[:8]}")

                # Implementation attempts (up to 3 per strategy)
                max_attempts = 3
                for attempt in range(1, max_attempts + 1):
                    print("\n" + f"{'─' * 70}")
                    print(f"🔄 ATTEMPT {attempt}/{max_attempts} for {strategy.name}")
                    print(f"{'─' * 70}")

                    # PHASE 1: Implementation
                    print("\n⚙️  PHASE 1: IMPLEMENTATION")
                    logger.log_phase("implementation", "start")

                    if attempt == 1:
                        # First attempt: use initial prompt
                        strategy_prompt = f"{initial_prompt}\n\n## STRATEGY TO USE\n{strategy.approach}"
                        self._agent_loop(workspace, strategy_prompt, enhanced_context, prompt_template, incremental_validator, logger)
                    else:
                        # Retry with feedback
                        print("Sending verification feedback for corrections...\n")
                        retry_prompt = f"""The implementation has verification issues that need to be fixed.

# VERIFICATION FEEDBACK
{verification_feedback}

# YOUR TASK
Fix these specific issues. Respond with a JSON array of actions.

Respond NOW with ONLY a JSON array:"""
                        self._agent_loop(workspace, retry_prompt, enhanced_context, prompt_template, incremental_validator, logger)

                    # Check if commits were made
                    if not self.workspace_manager.has_commits(workspace, config.github.base_branch):
                        print("\n⚠️  No commits were made.")
                        logger.log_warning("No commits made")
                        if attempt >= max_attempts:
                            # Try next strategy
                            if checkpoint_mgr and checkpoint:
                                print("🔄 Rolling back to checkpoint")
                                checkpoint_mgr.rollback_to(checkpoint)
                            break
                        continue

                    print("\n✅ Implementation phase complete")
                    logger.log_phase("implementation", "end")

                    # Track usage if enabled
                    if self.resource_manager:
                        usage = self.resource_manager.get_issue_usage()
                        logger.log_metrics({
                            "tokens_used": usage.tokens,
                            "cost_so_far": usage.cost
                        })

                    # Reset conversation for verification (fresh perspective)
                    print("\n🔄 Resetting conversation for verification (fresh perspective)")
                    self.agent.reset_conversation()
                    self.agent.initialize_with_project_context(
                        project_context=enhanced_context,
                        coding_standards=prompt_template
                    )

                    # PHASE 2: Quality Gates
                    print("\n" + "=" * 70)
                    print("🔍 PHASE 2: QUALITY VERIFICATION")
                    print("=" * 70)
                    logger.log_phase("quality_verification", "start")

                    if quality_gate:
                        # Use quality gate system
                        report = quality_gate.check_all()
                        quality_gate.print_report(report)
                        logger.log_info("Quality gates checked", {
                            "passed": report.passed,
                            "critical_failures": len(report.critical_failures)
                        })

                        if report.has_critical_failures:
                            print("\n❌ CRITICAL quality failures - cannot proceed")
                            verification_passed = False
                            verification_feedback = "\n".join([
                                f"CRITICAL: {f.message}" for f in report.critical_failures
                            ])
                        elif not report.passed:
                            print("\n⚠️  Some quality checks failed")
                            verification_passed = False
                            verification_feedback = "\n".join([
                                f.message for f in report.required_failures + report.recommended_failures
                            ])
                        else:
                            print("\n✅ All quality gates passed!")
                            verification_passed = True
                    else:
                        # Fall back to legacy verification
                        verification_passed, verification_feedback = self._verify_implementation_combined(
                            workspace, enhanced_context, prompt_template, issue
                        )

                    logger.log_phase("quality_verification", "end", {"passed": verification_passed})

                    if verification_passed:
                        print("\n✅ Strategy succeeded!")
                        strategy_success = True
                        final_strategy_used = strategy.name
                        break  # Exit attempt loop

                    print(f"\n⚠️  Verification failed on attempt {attempt}/{max_attempts}")

                    if attempt >= max_attempts:
                        print(f"\n⚠️  Max attempts reached for {strategy.name}")
                        # Will try next strategy or exit

                # Check if strategy succeeded
                if strategy_success:
                    break  # Exit strategy loop

                # Strategy failed - rollback and try next
                if checkpoint_mgr and checkpoint:
                    print(f"\n🔄 Strategy failed. Rolling back to checkpoint...")
                    checkpoint_mgr.rollback_to(checkpoint)
                    logger.log_info("Rolled back to checkpoint")
                else:
                    print(f"\n⚠️  Strategy failed (no checkpoint available)")

            # After all strategies tried
            implementation_end_time = __import__('datetime').datetime.now()
            duration = (implementation_end_time - implementation_start_time).total_seconds()

            # Calculate final metrics
            if not strategy_success and not self.workspace_manager.has_commits(workspace, config.github.base_branch):
                print("\n❌ All strategies failed with no successful commits")
                logger.log_error("All strategies exhausted without success")

                # Record failure
                outcome = ImplementationOutcome(
                    success=False,
                    attempts=len(ranked_strategies) * max_attempts,
                    quality_passed=False,
                    cost=self.resource_manager.get_issue_usage().cost if self.resource_manager else 0.0,
                    time_seconds=duration,
                    files_changed=0,
                    lines_changed=0,
                    strategy_used="none",
                    error_messages=[verification_feedback] if verification_feedback else ["No commits made"]
                )
                self.tracker.record_implementation(config.name, issue, outcome)
                logger.log_metrics({"success": False, "duration": duration})

                # Create debug bundle
                bundle = logger.create_debug_bundle(workspace)
                print(f"\n💡 Debug bundle created at: {bundle}")

                self.workspace_manager.return_to_base_branch(workspace, config.github.base_branch)
                return

            # Show summary
            self.workspace_manager.show_summary(workspace, config.github.base_branch)

            # Count changes
            result = subprocess.run(
                ["git", "diff", config.github.base_branch, "--shortstat"],
                cwd=workspace,
                capture_output=True,
                text=True
            )
            stats = result.stdout.strip()
            files_changed = 0
            lines_changed = 0
            if "file" in stats:
                import re
                file_match = re.search(r'(\d+) file', stats)
                if file_match:
                    files_changed = int(file_match.group(1))
                lines_match = re.search(r'(\d+) insertion', stats)
                if lines_match:
                    lines_changed = int(lines_match.group(1))

            # Record successful outcome
            outcome = ImplementationOutcome(
                success=True,
                attempts=strategy_idx if strategy_success else len(ranked_strategies),
                quality_passed=verification_passed,
                cost=self.resource_manager.get_issue_usage().cost if self.resource_manager else 0.0,
                time_seconds=duration,
                files_changed=files_changed,
                lines_changed=lines_changed,
                strategy_used=final_strategy_used or "unknown",
                error_messages=[] if verification_passed else [verification_feedback]
            )
            self.tracker.record_implementation(config.name, issue, outcome)
            logger.log_metrics({
                "success": True,
                "duration": duration,
                "strategy": final_strategy_used,
                "quality_passed": verification_passed
            })

            # Push and create PR
            print("\n" + "=" * 70)
            print("🚀 CREATING PULL REQUEST")
            print("=" * 70)
            logger.log_phase("pr_creation", "start")

            self.workspace_manager.push_changes(workspace, branch_name)

            # Create PR body
            if is_manual:
                # Manual ticket - include source information
                pr_body = f"""🤖 Automated implementation by VÄKI AI

**Strategy Used:** {final_strategy_used or 'Standard Implementation'}
**Quality Status:** {'✅ All checks passed' if verification_passed else '⚠️ See quality notes below'}
**Files Changed:** {files_changed}
**Implementation Time:** {duration/60:.1f}m

---

{issue.to_pr_reference()}

**Description:**
{issue.body or 'No description provided'}
"""
            else:
                # GitHub issue - standard format
                pr_body = f"""🤖 Automated implementation by VÄKI AI

**Strategy Used:** {final_strategy_used or 'Standard Implementation'}
**Quality Status:** {'✅ All checks passed' if verification_passed else '⚠️ See quality notes below'}
**Files Changed:** {files_changed}
**Implementation Time:** {duration/60:.1f}m

Closes #{issue.number}

---

{issue.body or 'No description provided'}
"""

            if not verification_passed:
                pr_body += f"\n\n## ⚠️ Quality Notice\n\nSome automated quality checks did not pass. Please review carefully:\n\n{verification_feedback}\n"

            if self.resource_manager:
                usage = self.resource_manager.get_issue_usage()
                pr_body += f"\n\n---\n*Cost: ${usage.cost:.2f} | Tokens: {usage.tokens:,}*"

            # Create PR with appropriate title
            if is_manual:
                pr_title = f"[VÄKI] {issue.title} (from {issue.source})"
            else:
                pr_title = f"[VÄKI] {issue.title}"

            pr = self.github_client.create_pull_request(
                repo_name=config.github.repo,
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=config.github.base_branch
            )
            print(f"\n✅ Pull Request created: {pr.html_url}")
            logger.log_info("PR created", {"url": pr.html_url})
            logger.log_phase("pr_creation", "end")

            # Print resource usage summary
            if self.resource_manager:
                print("\n" + "=" * 70)
                print("💰 RESOURCE USAGE")
                print("=" * 70)
                self.resource_manager.print_usage_summary()

            # Return to base branch
            self.workspace_manager.return_to_base_branch(workspace, config.github.base_branch)

        except Exception as e:
            print(f"\n❌ Error during automated implementation: {sanitize(str(e))}")
            print(f"\n💡 You can manually check the branch:")
            print(f"  cd {workspace}")
            print(f"  git checkout {branch_name}")
            self.workspace_manager.return_to_base_branch(workspace, config.github.base_branch)

    def _agent_loop(
        self,
        workspace: Path,
        initial_prompt: str,
        context: str,
        prompt_template: str,
        incremental_validator: Optional[IncrementalValidator] = None,
        logger: Optional[ImplementationLogger] = None
    ) -> None:
        """
        Run the agent loop to implement changes.

        Args:
            workspace: Project workspace path
            initial_prompt: Initial prompt to send to agent
            context: Project context (kept for re-initialization if needed)
            prompt_template: Coding standards template (kept for re-initialization if needed)
            incremental_validator: Optional validator for real-time feedback
            logger: Optional logger for recording actions

        Note:
            Agent should already be initialized with project context via
            initialize_with_project_context() before calling this method.
        """
        iteration = 0
        response = self.agent.send_message(initial_prompt)

        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n{'─' * 70}")
            print(f"🔄 Iteration {iteration}/{self.max_iterations}")
            print(f"{'─' * 70}\n")

            # Parse response
            parsed = self.agent.parse_json_response(response)

            if not parsed:
                print("⚠️  Could not parse agent response. Asking for clarification...")
                response = self.agent.send_message(
                    """ERROR: Invalid response format.

Respond with ONLY a valid JSON array of actions. Example:
[
  {"action": "read_file", "path": "src/example.ts"},
  {"action": "edit_file", "path": "src/example.ts", "search": "old", "replace": "new"},
  {"action": "commit", "message": "Fix issues"},
  {"action": "done", "summary": "All issues fixed"}
]

Respond NOW with JSON array only:"""
                )
                continue

            # Handle initial plan
            if isinstance(parsed, dict) and "plan" in parsed:
                print(f"📋 Plan: {parsed.get('plan', 'No plan provided')}\n")

                # Read requested files
                files_to_read = parsed.get('files_to_read', [])
                file_contents = self._read_files(workspace, files_to_read)

                response = self.agent.send_message(
                    f"Here are the file contents:\n\n{file_contents}\n\n"
                    f"Now provide your actions as a JSON array."
                )
                continue

            # Handle actions
            if isinstance(parsed, list):
                # Validate actions have correct structure
                valid_actions = []
                for action in parsed:
                    if isinstance(action, dict) and 'action' in action:
                        valid_actions.append(action)
                    else:
                        print(f"⚠️  Skipping invalid action: {action}")

                if not valid_actions:
                    print("⚠️  No valid actions found. Asking agent to provide correct format...")
                    response = self.agent.send_message(
                        """ERROR: No valid actions in your response.

Each action must be a JSON object with an "action" field.

Valid actions:
- {"action": "read_file", "path": "file.ts"}
- {"action": "write_file", "path": "file.ts", "content": "..."}
- {"action": "edit_file", "path": "file.ts", "search": "...", "replace": "..."}
- {"action": "commit", "message": "..."}
- {"action": "done", "summary": "..."}

Respond with JSON array of actions:"""
                    )
                    continue

                feedback = self._execute_actions(workspace, valid_actions, logger)

                # Incremental validation after actions
                if incremental_validator:
                    for action in valid_actions:
                        action_type = action.get('action')
                        if incremental_validator.should_validate(action_type):
                            file_path = action.get('path') if action_type in ['write_file', 'edit_file'] else None
                            validation_result = incremental_validator.validate_change(file_path)

                            if not validation_result.passed:
                                print(f"\n⚠️  Incremental validation failed:")
                                for error in validation_result.errors:
                                    print(f"   • {error}")
                                feedback += f"\n\n⚠️ VALIDATION ERRORS:\n" + "\n".join(validation_result.errors)
                                if logger:
                                    logger.log_warning("Incremental validation failed", {
                                        "errors": validation_result.errors
                                    })
                            elif validation_result.warnings:
                                print(f"\n💡 Validation warnings:")
                                for warning in validation_result.warnings:
                                    print(f"   • {warning}")

                # Track resource usage
                if self.resource_manager:
                    # Estimate tokens used (rough approximation)
                    self.resource_manager.record_usage(
                        input_tokens=len(str(valid_actions)) // 4,
                        output_tokens=len(feedback) // 4,
                        operation="agent_loop"
                    )

                # Check if done
                if any(action.get('action') == 'done' for action in valid_actions):
                    done_action = next(a for a in valid_actions if a.get('action') == 'done')
                    print(f"\n✅ Implementation complete!")
                    print(f"Summary: {done_action.get('summary', 'No summary provided')}")
                    if logger:
                        logger.log_info("Implementation marked as done", {
                            "summary": done_action.get('summary')
                        })
                    return

                # Send feedback for next iteration
                response = self.agent.send_message(feedback + "\n\nContinue with next actions as JSON array:")
                continue

            # Unknown format
            print("⚠️  Unexpected response format. Asking agent to continue...")
            response = self.agent.send_message(
                "Please continue with your next actions as a JSON array, or use the 'done' action if complete."
            )

        print(f"\n⚠️  Reached maximum iterations ({self.max_iterations}). Stopping.")

    def _read_files(self, workspace: Path, file_paths: List[str]) -> str:
        """Read multiple files and return their contents with moderate truncation."""
        contents: List[str] = []
        max_file_size = 12000  # ~3k tokens per file
        max_total_size = 48000  # ~12k tokens total
        total_size = 0

        for file_path in file_paths:
            if total_size >= max_total_size:
                contents.append(f"## ... (remaining files truncated)")
                break

            full_path = workspace / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Truncate large files
                    if len(content) > max_file_size:
                        content = content[:max_file_size] + f"\n... (truncated, total: {len(content)} chars)"

                    file_content = f"## {file_path}\n```\n{content}\n```\n"
                    contents.append(file_content)
                    total_size += len(file_content)
                except UnicodeDecodeError:
                    contents.append(f"## {file_path}\nError reading: Binary or non-UTF-8 file\n")
                except IOError as e:
                    contents.append(f"## {file_path}\nError reading: {sanitize(str(e))}\n")
                except Exception as e:
                    contents.append(f"## {file_path}\nError reading: {sanitize(str(e))}\n")
            else:
                contents.append(f"## {file_path}\nFile not found\n")

        return "\n".join(contents) if contents else "No files to read"

    def _execute_actions(self, workspace: Path, actions: List[Action], logger: Optional[ImplementationLogger] = None) -> str:
        """
        Execute a list of actions.

        Args:
            workspace: Project workspace
            actions: List of action dictionaries with proper type annotations
            logger: Optional logger for recording actions

        Returns:
            Feedback message about executed actions
        """
        results: List[str] = []

        for action in actions:
            action_type = action.get('action')

            if action_type == 'read_file':
                result = self._action_read_file(workspace, action)  # type: ignore
            elif action_type == 'write_file':
                result = self._action_write_file(workspace, action)  # type: ignore
            elif action_type == 'edit_file':
                result = self._action_edit_file(workspace, action)  # type: ignore
            elif action_type == 'run_command':
                result = self._action_run_command(workspace, action)  # type: ignore
            elif action_type == 'commit':
                result = self._action_commit(workspace, action)  # type: ignore
            elif action_type == 'done':
                result = "✅ Marked as done"
            else:
                result = f"❌ Unknown action: {action_type}"

            results.append(result)
            print(result)

            # Log action
            if logger:
                logger.log_action(action, result)

        return "\n".join(results)

    def _action_read_file(self, workspace: Path, action: ReadFileAction) -> str:
        """Read a file."""
        file_path = action.get('path')
        if not file_path:
            return "❌ Error: No path specified"

        full_path = workspace / file_path

        if not full_path.exists():
            return f"❌ File not found: {file_path}"

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"✅ Read file: {file_path}\n```\n{content}\n```"
        except Exception as e:
            return f"❌ Error reading {file_path}: {sanitize(str(e))}"

    def _action_write_file(self, workspace: Path, action: WriteFileAction) -> str:
        """Write/create a file."""
        file_path = action.get('path')
        content = action.get('content', '')

        if not file_path:
            return "❌ Error: No path specified"

        full_path = workspace / file_path

        try:
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ Wrote file: {file_path}"
        except Exception as e:
            return f"❌ Error writing {file_path}: {sanitize(str(e))}"

    def _action_edit_file(self, workspace: Path, action: EditFileAction) -> str:
        """Edit a file by replacing text."""
        file_path = action.get('path')
        search = action.get('search', '')
        replace = action.get('replace', '')

        if not file_path:
            return "❌ Error: No path specified"

        full_path = workspace / file_path

        if not full_path.exists():
            return f"❌ File not found: {file_path}"

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if search not in content:
                return f"⚠️  Search string not found in {file_path}"

            new_content = content.replace(search, replace, 1)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return f"✅ Edited file: {file_path}"
        except Exception as e:
            return f"❌ Error editing {file_path}: {sanitize(str(e))}"

    def _action_run_command(self, workspace: Path, action: RunCommandAction) -> str:
        """Run a shell command."""
        command = action.get('command')

        if not command:
            return "❌ Error: No command specified"

        try:
            result = subprocess.run(
                command,
                cwd=workspace,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )

            output = sanitize(result.stdout + result.stderr)
            if result.returncode == 0:
                return f"✅ Command succeeded: {command}\n{output[:200]}"
            else:
                return f"⚠️  Command failed (exit {result.returncode}): {command}\n{output[:200]}"
        except subprocess.TimeoutExpired:
            return f"❌ Command timed out after 60 seconds: {command}"
        except Exception as e:
            return f"❌ Error running command: {sanitize(str(e))}"

    def _action_commit(self, workspace: Path, action: CommitAction) -> str:
        """Create a git commit."""
        message = action.get('message', 'Automated commit')

        if not message:
            return "❌ Error: No commit message specified"

        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=workspace,
                check=True,
                capture_output=True
            )

            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=workspace,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return f"✅ Committed: {message}"
            else:
                return f"⚠️  Nothing to commit or commit failed"
        except subprocess.CalledProcessError as e:
            return f"❌ Error adding files to git: {sanitize(str(e))}"
        except Exception as e:
            return f"❌ Error committing: {sanitize(str(e))}"

    def _verify_implementation_combined(self, workspace: Path, context: str, prompt_template: str, issue: Issue) -> tuple[bool, str]:
        """
        Combined verification - all checks in ONE API call to save tokens.

        Args:
            workspace: Project workspace path
            context: Project context
            prompt_template: Coding standards template
            issue: GitHub issue object

        Returns:
            Tuple of (verification passed boolean, feedback string)
        """
        print("\n📋 Running automated quality checks...")

        # Run automated checks (no AI)
        type_check_result, type_check_msg = self._run_type_check(workspace)
        test_result, test_msg = self._run_tests(workspace)
        build_result, build_msg = self._run_build(workspace)

        print(f"   {'✅' if type_check_result else '❌'} Type Check")
        print(f"   {'✅' if test_result else '❌'} Tests")
        print(f"   {'✅' if build_result else '❌'} Build")

        # Get changed files
        print("\n🤖 AI reviewing code quality, requirements, and UI...")
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        changed_files = result.stdout.strip().split('\n')[:5]

        # Read changed files (moderate truncation)
        file_contents = []
        max_file_chars = 10000  # ~2.5k tokens per file
        for file_path in changed_files[:5]:
            full_path = workspace / file_path
            if full_path.exists() and full_path.stat().st_size < 60000:
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if len(content) > max_file_chars:
                        content = content[:max_file_chars] + f"\n...(truncated)"
                    file_contents.append(f"## {file_path}\n```\n{content}\n```\n")
                except (UnicodeDecodeError, IOError, OSError):
                    # Skip files that can't be read (binary, permissions, etc.)
                    pass

        if not file_contents:
            return True, "No files to review"

        # Get git diff
        diff_result = subprocess.run(
            ["git", "diff", "HEAD~1"],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        diff_content = sanitize(diff_result.stdout[:6000])  # ~1.5k tokens

        # SINGLE combined verification prompt
        # Context is already in system message
        combined_prompt = f"""Review this implementation against ALL quality criteria in ONE analysis.

# ORIGINAL ISSUE
**Title**: {issue.title}
**Description**: {issue.body or 'No description'}

# CHANGES (git diff summary)
```diff
{diff_content}
```

# CHANGED FILES
{''.join(file_contents[:3])}

# YOUR TASK
Analyze and respond with JSON covering ALL these areas:

1. **Code Quality**: Does code follow project standards you were given?
2. **Requirements**: Does it address all issue requirements?
3. **UI/UX**: If UI changes, will it work from user perspective?
4. **Concerns**: Any bugs, missing features, or quality issues?

Respond with JSON:
{{
  "code_quality_passed": true/false,
  "requirements_met": true/false,
  "ui_functional": true/false or "n/a",
  "issues": ["issue1", "issue2"],
  "summary": "brief overall assessment"
}}
"""

        response = self.agent.send_message(combined_prompt)
        review = self.agent.parse_json_response(response)

        if not review:
            print("   ⚠️  Could not parse review")
            return True, "Could not parse review"

        # Check results
        code_quality = review.get('code_quality_passed', True)
        requirements = review.get('requirements_met', True)
        ui_check = review.get('ui_functional', 'n/a')
        ui_ok = ui_check == 'n/a' or ui_check == True

        print(f"   {'✅' if code_quality else '❌'} Code Quality")
        print(f"   {'✅' if requirements else '❌'} Requirements Met")
        print(f"   {'✅' if ui_ok else '❌'} UI Functional")

        # Overall pass requires: automated checks + AI checks
        all_passed = (type_check_result and test_result and build_result and
                     code_quality and requirements and ui_ok)

        # Build feedback
        feedback_items = []
        if not type_check_result:
            feedback_items.append(f"Type Check: {type_check_msg}")
        if not test_result:
            feedback_items.append(f"Tests: {test_msg}")
        if not build_result:
            feedback_items.append(f"Build: {build_msg}")
        if not code_quality or not requirements or not ui_ok:
            feedback_items.extend(review.get('issues', []))

        feedback = "\n".join(feedback_items) if feedback_items else "All checks passed"

        print(f"\n📊 Overall: {'✅ PASSED' if all_passed else '❌ FAILED'}")
        if review.get('summary'):
            print(f"   {review['summary']}")

        return all_passed, feedback


    def _run_type_check(self, workspace: Path) -> tuple[bool, str]:
        """Run TypeScript type checking or equivalent."""
        # Check for TypeScript project
        if (workspace / "tsconfig.json").exists():
            result = subprocess.run(
                ["npm", "run", "build", "--", "--noEmit"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print("     ✅ Type checking passed")
                return True, "Type checking passed"
            else:
                error_msg = sanitize(result.stderr[:500])
                print(f"     ❌ Type errors found")
                return False, error_msg

        # Check for Python typing
        if (workspace / "pyproject.toml").exists() or any((workspace / "src").glob("*.py")) if (workspace / "src").exists() else False:
            result = subprocess.run(
                ["mypy", "."],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print("     ✅ Type checking passed")
                return True, "Type checking passed"
            else:
                return False, sanitize(result.stdout[:500])

        print("     ⚠️  No type checking configured, skipping")
        return True, "No type checking configured"

    def _run_tests(self, workspace: Path) -> tuple[bool, str]:
        """Run project tests."""
        package_json = workspace / "package.json"

        # Node.js project
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    import json
                    pkg = json.load(f)
                    if "test" in pkg.get("scripts", {}):
                        result = subprocess.run(
                            ["npm", "test"],
                            cwd=workspace,
                            capture_output=True,
                            text=True,
                            timeout=180
                        )
                        if result.returncode == 0:
                            print("     ✅ Tests passed")
                            return True, "Tests passed"
                        else:
                            error_msg = sanitize(result.stdout[-500:])
                            print(f"     ❌ Tests failed")
                            return False, error_msg
            except Exception as e:
                print(f"     ⚠️  Error running tests: {sanitize(str(e))}")
                return False, sanitize(str(e))

        # Python project
        if (workspace / "pytest.ini").exists() or (workspace / "pyproject.toml").exists():
            result = subprocess.run(
                ["pytest"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode == 0:
                print("     ✅ Tests passed")
                return True, "Tests passed"
            else:
                error_msg = sanitize(result.stdout[-500:])
                print(f"     ❌ Tests failed")
                return False, error_msg

        print("     ⚠️  No tests configured, skipping")
        return True, "No tests configured"

    def _run_build(self, workspace: Path) -> tuple[bool, str]:
        """Run project build."""
        package_json = workspace / "package.json"

        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    import json
                    pkg = json.load(f)
                    if "build" in pkg.get("scripts", {}):
                        result = subprocess.run(
                            ["npm", "run", "build"],
                            cwd=workspace,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        if result.returncode == 0:
                            print("     ✅ Build succeeded")
                            return True, "Build succeeded"
                        else:
                            error_msg = sanitize(result.stderr[-500:])
                            print(f"     ❌ Build failed")
                            return False, error_msg
            except Exception as e:
                print(f"     ⚠️  Error running build: {sanitize(str(e))}")
                return False, sanitize(str(e))

        print("     ⚠️  No build configured, skipping")
        return True, "No build configured"

    def _review_code_quality(self, workspace: Path, context: str, prompt_template: str) -> tuple[bool, str]:
        """Use OpenAI to review code quality against guidelines."""
        try:
            # Get list of changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                cwd=workspace,
                capture_output=True,
                text=True
            )
            changed_files = result.stdout.strip().split('\n')[:5]  # Review up to 5 files

            # Read changed files with aggressive truncation
            file_contents = []
            max_file_chars = 6000  # ~1.5k tokens per file (aggressive)
            for file_path in changed_files[:3]:  # Only 3 files max
                full_path = workspace / file_path
                if full_path.exists() and full_path.stat().st_size < 50000:  # Skip large files
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Aggressive truncation
                        if len(content) > max_file_chars:
                            content = content[:max_file_chars] + f"\n...(truncated)"

                        file_contents.append(f"## {file_path}\n```\n{content}\n```\n")
                    except (UnicodeDecodeError, IOError, OSError):
                        # Skip files that can't be read (binary, permissions, etc.)
                        pass

            if not file_contents:
                print("     ⚠️  No files to review")
                return True, "No files to review"

            # Context is already in system message
            review_prompt = f"""Review this code implementation against the project guidelines.

# CHANGED FILES
{''.join(file_contents)}

Respond with JSON:
{{"passed": true/false, "issues": ["issue1", "issue2"], "summary": "overall assessment"}}

Check for:
- Adherence to coding standards you were given
- Code quality and best practices
- Potential bugs or issues
- Test coverage
"""

            response = self.agent.send_message(review_prompt)
            review = self.agent.parse_json_response(response)

            if not review:
                print("     ⚠️  Could not parse review response")
                return True, "Could not parse review"

            if review.get('passed', True):
                print(f"     ✅ Code quality check passed")
                if review.get('summary'):
                    print(f"        {review['summary']}")
                return True, "Code quality passed"
            else:
                issues_text = '\n        - '.join(review.get('issues', []))
                print(f"     ❌ Code quality issues found:")
                print(f"        - {issues_text}")
                return False, f"Quality Issues:\n{issues_text}"

        except Exception as e:
            print(f"     ⚠️  Error during quality review: {sanitize(str(e))}")
            return True, f"Error: {sanitize(str(e))}"

    def list_projects(self) -> None:
        """List all available projects."""
        projects = self.config_loader.list_projects()
        if not projects:
            print("No projects configured yet.")
            return

        print(f"\n📦 Available Projects ({len(projects)}):\n")
        for project in projects:
            config = self.config_loader.load_project(project)
            print(f"  • {config.name}")
            print(f"    {config.description}")
            print(f"    Repo: {config.github.repo}")
            print()
