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

    def _process_issue(self, issue: Issue, config: ProjectConfig) -> None:
        """Process a single issue with OpenAI agent."""
        print(f"\n{'=' * 70}")
        print(f"🤖 AUTO-PROCESSING ISSUE #{issue.number}")
        print(f"{'=' * 70}")
        print(f"Title: {issue.title}")
        print(f"URL: {issue.html_url}\n")

        # Find project directory
        workspace = self.workspace_manager.find_project_directory(config.github.repo)

        if not workspace:
            print(f"❌ Error: Project directory not found in parent folder")
            print(f"Expected to find: {config.github.repo.split('/')[-1]}")
            return

        # Create branch name
        branch_name = f"openai/issue-{issue.number}"

        # Prepare workspace
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

        # Create implementation prompt
        initial_prompt = self.agent.create_implementation_prompt(
            issue_title=issue.title,
            issue_body=issue.body or "",
            project_context=context,
            prompt_template=prompt_template
        )

        try:
            # Implementation and verification loop (max 3 attempts)
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                print("\n" + "=" * 70)
                print(f"🔄 ATTEMPT {attempt}/{max_attempts}")
                print("=" * 70)

                # PHASE 1: Implementation
                print("\n" + "=" * 70)
                if attempt == 1:
                    print("⚙️  PHASE 1: IMPLEMENTATION")
                    print("=" * 70)
                    print(f"Agent will read codebase and implement changes...")
                    print()
                    self._agent_loop(workspace, initial_prompt)
                else:
                    print("🔄 PHASE 6: RETRY WITH FEEDBACK")
                    print("=" * 70)
                    print("Sending verification feedback to agent for corrections...\n")

                    # Send feedback to agent for retry and continue loop
                    # Re-include full context to prevent drift
                    retry_prompt = f"""The implementation has verification issues that need to be fixed.

# PROJECT CONTEXT
{context}

# CODING STANDARDS
{prompt_template}

# ISSUE
**Title**: {issue.title}
**Description**: {issue.body or 'No description'}

# VERIFICATION FEEDBACK - ISSUES TO FIX
{verification_feedback}

# YOUR TASK
Fix these specific issues. Respond with a JSON array of actions.

IMPORTANT: Use ONLY these action types:
- {{"action": "read_file", "path": "path/to/file"}}
- {{"action": "write_file", "path": "path/to/file", "content": "full content"}}
- {{"action": "edit_file", "path": "path/to/file", "search": "old text", "replace": "new text"}}
- {{"action": "run_command", "command": "npm test"}}
- {{"action": "commit", "message": "Fixed verification issues"}}
- {{"action": "done", "summary": "what was fixed"}}

Example response:
[
  {{"action": "read_file", "path": "src/App.tsx"}},
  {{"action": "edit_file", "path": "src/App.tsx", "search": "old code", "replace": "fixed code"}},
  {{"action": "commit", "message": "Fix: applied verification feedback"}},
  {{"action": "done", "summary": "Fixed all verification issues"}}
]

Respond NOW with ONLY a JSON array:"""

                    # Continue the agent loop with retry feedback
                    self._agent_loop(workspace, retry_prompt)

                # Check if commits were made
                if not self.workspace_manager.has_commits(workspace, config.github.base_branch):
                    print("\n⚠️  No commits were made. Aborting.")
                    self.workspace_manager.return_to_base_branch(workspace, config.github.base_branch)
                    return

                print("\n✅ Implementation phase complete")

                # Reset conversation for verification (fresh context, saves tokens)
                print("\n   🔄 Resetting conversation for verification (fresh perspective)")
                self.agent.reset_conversation()

                # PHASE 2: Single Combined Verification
                print("\n" + "=" * 70)
                print("🔍 PHASE 2: COMBINED VERIFICATION")
                print("=" * 70)
                print("Running all quality checks in single pass...")

                verification_passed, verification_feedback = self._verify_implementation_combined(
                    workspace, context, prompt_template, issue
                )

                if verification_passed:
                    print("\n✅ All verifications passed!")
                    break
                else:
                    print(f"\n⚠️  Verification failed on attempt {attempt}/{max_attempts}")

                    if attempt >= max_attempts:
                        print("\n⚠️  Max attempts reached. Creating PR anyway with quality warnings...")
                        break

            # Show summary
            self.workspace_manager.show_summary(workspace, config.github.base_branch)

            # Push and create PR
            print("\n" + "=" * 70)
            print("🚀 CREATING PULL REQUEST")
            print("=" * 70)

            self.workspace_manager.push_changes(workspace, branch_name)

            # Create PR body with quality warnings if verification failed
            pr_body = f"🤖 Automated implementation by OpenAI\n\nCloses #{issue.number}\n\n{issue.body or ''}"

            if not verification_passed:
                pr_body += f"\n\n---\n\n⚠️ **Quality Notice:** This PR was created after {max_attempts} attempts; some automated quality checks did not pass and require manual review."

            pr = self.github_client.create_pull_request(
                repo_name=config.github.repo,
                title=f"[OpenAI] {issue.title}",
                body=pr_body,
                head=branch_name,
                base=config.github.base_branch
            )
            print(f"\n✅ Pull Request created: {pr.html_url}")

            # Return to base branch
            self.workspace_manager.return_to_base_branch(workspace, config.github.base_branch)

        except Exception as e:
            print(f"\n❌ Error during automated implementation: {sanitize(str(e))}")
            print(f"\n💡 You can manually check the branch:")
            print(f"  cd {workspace}")
            print(f"  git checkout {branch_name}")
            self.workspace_manager.return_to_base_branch(workspace, config.github.base_branch)

    def _agent_loop(self, workspace: Path, initial_prompt: str) -> None:
        """
        Run the agent loop to implement changes.

        Args:
            workspace: Project workspace path
            initial_prompt: Initial prompt to send to agent
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

                feedback = self._execute_actions(workspace, valid_actions)

                # Check if done
                if any(action.get('action') == 'done' for action in valid_actions):
                    done_action = next(a for a in valid_actions if a.get('action') == 'done')
                    print(f"\n✅ Implementation complete!")
                    print(f"Summary: {done_action.get('summary', 'No summary provided')}")
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

    def _execute_actions(self, workspace: Path, actions: List[Action]) -> str:
        """
        Execute a list of actions.

        Args:
            workspace: Project workspace
            actions: List of action dictionaries with proper type annotations

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
        combined_prompt = f"""Review this implementation against ALL quality criteria in ONE analysis.

# PROJECT CONTEXT
{context}

# CODING STANDARDS
{prompt_template}

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

1. **Code Quality**: Does code follow project standards?
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

            review_prompt = f"""Review this code implementation against the project guidelines:

# PROJECT CONTEXT
{context}

# CODING STANDARDS
{prompt_template}

# CHANGED FILES
{''.join(file_contents)}

Respond with JSON:
{{"passed": true/false, "issues": ["issue1", "issue2"], "summary": "overall assessment"}}

Check for:
- Adherence to coding standards
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
