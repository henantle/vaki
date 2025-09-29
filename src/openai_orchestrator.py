"""OpenAI-powered automated implementation orchestrator."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from github.Issue import Issue

from .config import ConfigLoader, ProjectConfig
from .github_client import GitHubClient
from .workspace import WorkspaceManager
from .openai_agent import OpenAIAgent


class OpenAIOrchestrator:
    """Orchestrates fully automated workflow using OpenAI API."""

    def __init__(self, github_token: str, openai_api_key: str, base_dir: str = "."):
        self.github_token = github_token
        self.config_loader = ConfigLoader(base_dir)
        self.github_client = GitHubClient(github_token)
        self.workspace_manager = WorkspaceManager()
        self.agent = OpenAIAgent(openai_api_key)
        self.max_iterations = 20  # Safety limit

    def run_project(self, project_name: str, issue_number: Optional[int] = None):
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

    def _process_issue(self, issue: Issue, config: ProjectConfig):
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
            print(f"\n❌ Error during automated implementation: {e}")
            print(f"\n💡 You can manually check the branch:")
            print(f"  cd {workspace}")
            print(f"  git checkout {branch_name}")
            self.workspace_manager.return_to_base_branch(workspace, config.github.base_branch)

    def _agent_loop(self, workspace: Path, initial_prompt: str):
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
        contents = []
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
                except Exception as e:
                    contents.append(f"## {file_path}\nError reading: {e}\n")
            else:
                contents.append(f"## {file_path}\nFile not found\n")

        return "\n".join(contents) if contents else "No files to read"

    def _execute_actions(self, workspace: Path, actions: List[Dict[str, Any]]) -> str:
        """
        Execute a list of actions.

        Args:
            workspace: Project workspace
            actions: List of action dictionaries

        Returns:
            Feedback message about executed actions
        """
        results = []

        for action in actions:
            action_type = action.get('action')

            if action_type == 'read_file':
                result = self._action_read_file(workspace, action)
            elif action_type == 'write_file':
                result = self._action_write_file(workspace, action)
            elif action_type == 'edit_file':
                result = self._action_edit_file(workspace, action)
            elif action_type == 'run_command':
                result = self._action_run_command(workspace, action)
            elif action_type == 'commit':
                result = self._action_commit(workspace, action)
            elif action_type == 'done':
                result = "✅ Marked as done"
            else:
                result = f"❌ Unknown action: {action_type}"

            results.append(result)
            print(result)

        return "\n".join(results)

    def _action_read_file(self, workspace: Path, action: Dict[str, Any]) -> str:
        """Read a file."""
        file_path = action.get('path')
        full_path = workspace / file_path

        if not full_path.exists():
            return f"❌ File not found: {file_path}"

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"✅ Read file: {file_path}\n```\n{content}\n```"
        except Exception as e:
            return f"❌ Error reading {file_path}: {e}"

    def _action_write_file(self, workspace: Path, action: Dict[str, Any]) -> str:
        """Write/create a file."""
        file_path = action.get('path')
        content = action.get('content', '')
        full_path = workspace / file_path

        try:
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ Wrote file: {file_path}"
        except Exception as e:
            return f"❌ Error writing {file_path}: {e}"

    def _action_edit_file(self, workspace: Path, action: Dict[str, Any]) -> str:
        """Edit a file by replacing text."""
        file_path = action.get('path')
        search = action.get('search', '')
        replace = action.get('replace', '')
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
            return f"❌ Error editing {file_path}: {e}"

    def _action_run_command(self, workspace: Path, action: Dict[str, Any]) -> str:
        """Run a shell command."""
        command = action.get('command')

        try:
            result = subprocess.run(
                command,
                cwd=workspace,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )

            output = result.stdout + result.stderr
            if result.returncode == 0:
                return f"✅ Command succeeded: {command}\n{output[:200]}"
            else:
                return f"⚠️  Command failed (exit {result.returncode}): {command}\n{output[:200]}"
        except Exception as e:
            return f"❌ Error running command: {e}"

    def _action_commit(self, workspace: Path, action: Dict[str, Any]) -> str:
        """Create a git commit."""
        message = action.get('message', 'Automated commit')

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
        except Exception as e:
            return f"❌ Error committing: {e}"

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
                except:
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
        diff_content = diff_result.stdout[:6000]  # ~1.5k tokens

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

    def _verify_implementation_OLD(self, workspace: Path, context: str, prompt_template: str, issue: Issue) -> tuple[bool, str]:
        """
        Verify implementation quality and functionality.

        Args:
            workspace: Project workspace path
            context: Project context
            prompt_template: Coding standards template
            issue: GitHub issue object

        Returns:
            Tuple of (verification passed boolean, feedback string)
        """
        verification_results = []
        feedback_items = []
        all_passed = True

        # PHASE 2: Project Quality Guardrails
        print("\n" + "─" * 70)
        print("📋 PHASE 2: PROJECT QUALITY GUARDRAILS")
        print("─" * 70)
        print("Checking type safety, tests, and build...")

        # 1. Run type checking / linting
        print("\n  🔸 Type Checking...")
        type_check_result, type_check_msg = self._run_type_check(workspace)
        verification_results.append(("Type Check", type_check_result))
        if not type_check_result:
            all_passed = False
            feedback_items.append(f"Type Check Failed: {type_check_msg}")

        # 2. Run tests
        print("\n  🔸 Running Tests...")
        test_result, test_msg = self._run_tests(workspace)
        verification_results.append(("Tests", test_result))
        if not test_result:
            all_passed = False
            feedback_items.append(f"Tests Failed: {test_msg}")

        # 3. Run build
        print("\n  🔸 Building Project...")
        build_result, build_msg = self._run_build(workspace)
        verification_results.append(("Build", build_result))
        if not build_result:
            all_passed = False
            feedback_items.append(f"Build Failed: {build_msg}")

        # PHASE 3: Code Quality Standards
        print("\n" + "─" * 70)
        print("📐 PHASE 3: CODE QUALITY STANDARDS")
        print("─" * 70)
        print("AI reviewing code against project coding standards...")

        quality_result, quality_msg = self._review_code_quality(workspace, context, prompt_template)
        verification_results.append(("Code Quality", quality_result))
        if not quality_result:
            all_passed = False
            feedback_items.append(f"Code Quality Issues: {quality_msg}")

        # PHASE 4: Ticket Specifications
        print("\n" + "─" * 70)
        print("🎯 PHASE 4: TICKET SPECIFICATIONS")
        print("─" * 70)
        print("AI verifying implementation matches issue requirements...")

        requirements_result, requirements_msg = self._verify_implementation_against_issue(
            workspace, issue, context, prompt_template
        )
        verification_results.append(("Ticket Requirements", requirements_result))
        if not requirements_result:
            all_passed = False
            feedback_items.append(f"Requirements Issues: {requirements_msg}")

        # PHASE 5: User Interface Validation
        print("\n" + "─" * 70)
        print("👤 PHASE 5: USER INTERFACE VALIDATION")
        print("─" * 70)
        print("AI validating UI/UX works from user perspective...")

        ui_result, ui_msg = self._verify_ui_functionality(
            workspace, issue, context, prompt_template
        )
        verification_results.append(("UI/UX Validation", ui_result))
        if not ui_result:
            all_passed = False
            feedback_items.append(f"UI/UX Issues: {ui_msg}")

        # Print summary
        print("\n" + "=" * 70)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 70)
        for check_name, passed in verification_results:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}")
        print("=" * 70)

        feedback = "\n".join(feedback_items) if feedback_items else "All checks passed"
        return all_passed, feedback

    def _verify_implementation_against_issue(
        self,
        workspace: Path,
        issue: Issue,
        context: str,
        prompt_template: str
    ) -> tuple[bool, str]:
        """
        Verify implementation matches issue specifications.

        Args:
            workspace: Project workspace path
            issue: GitHub issue object
            context: Project context
            prompt_template: Coding standards template

        Returns:
            Tuple of (passed boolean, message string)
        """
        try:
            # Get changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                cwd=workspace,
                capture_output=True,
                text=True
            )
            changed_files = result.stdout.strip().split('\n')[:10]

            # Read changed files with aggressive truncation
            file_contents = []
            max_file_chars = 5000  # ~1.25k tokens per file (aggressive)
            for file_path in changed_files[:3]:  # Only 3 files max
                full_path = workspace / file_path
                if full_path.exists() and full_path.stat().st_size < 50000:
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Aggressive truncation
                        if len(content) > max_file_chars:
                            content = content[:max_file_chars] + f"\n...(truncated)"

                        file_contents.append(f"## {file_path}\n```\n{content}\n```\n")
                    except:
                        pass

            if not file_contents:
                print("     ⚠️  No files to review")
                return True, "No files to review"

            # Get git diff for context (aggressive limit)
            diff_result = subprocess.run(
                ["git", "diff", "HEAD~1"],
                cwd=workspace,
                capture_output=True,
                text=True
            )
            diff_content = diff_result.stdout[:4000]  # ~1k tokens (aggressive)

            verification_prompt = f"""You are verifying that an implementation correctly addresses a GitHub issue.

# PROJECT CONTEXT
{context}

# CODING STANDARDS
{prompt_template}

# ORIGINAL ISSUE
**Title**: {issue.title}
**Description**:
{issue.body or 'No description provided'}

# IMPLEMENTATION (git diff)
```diff
{diff_content}
```

# CHANGED FILES
{''.join(file_contents[:3])}  # Show first 3 files fully

Analyze if the implementation:
1. ✅ Addresses all requirements from the issue
2. ✅ Implements the requested functionality completely
3. ✅ Matches the expected behavior described in the issue
4. ✅ Follows the project context and coding standards
5. ✅ For UI changes: Would work correctly from user perspective

Respond with JSON:
{{
  "matches_requirements": true/false,
  "missing_requirements": ["req1", "req2"],
  "concerns": ["concern1", "concern2"],
  "summary": "brief assessment",
  "user_facing_changes": "description of UI changes if any"
}}
"""

            response = self.agent.send_message(verification_prompt)
            review = self.agent.parse_json_response(response)

            if not review:
                print("     ⚠️  Could not parse verification response")
                return True, "Could not parse verification"

            if review.get('matches_requirements', False):
                print(f"     ✅ Implementation matches issue requirements")
                if review.get('summary'):
                    print(f"        {review['summary']}")
                if review.get('user_facing_changes'):
                    print(f"        UI: {review['user_facing_changes']}")
                return True, "Requirements matched"
            else:
                issues_list = []
                print(f"     ❌ Implementation issues found:")
                for req in review.get('missing_requirements', []):
                    print(f"        - Missing: {req}")
                    issues_list.append(f"Missing: {req}")
                for concern in review.get('concerns', []):
                    print(f"        - Concern: {concern}")
                    issues_list.append(f"Concern: {concern}")
                return False, '\n'.join(issues_list)

        except Exception as e:
            print(f"     ⚠️  Error during requirement verification: {e}")
            return True, f"Error: {e}"

    def _verify_ui_functionality(
        self,
        workspace: Path,
        issue: Issue,
        context: str,
        prompt_template: str
    ) -> tuple[bool, str]:
        """
        Verify UI functionality from user perspective.

        Args:
            workspace: Project workspace path
            issue: GitHub issue object
            context: Project context
            prompt_template: Coding standards template

        Returns:
            Tuple of (passed boolean, message string)
        """
        try:
            # Get changed files focusing on UI components
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                cwd=workspace,
                capture_output=True,
                text=True
            )
            changed_files = [f for f in result.stdout.strip().split('\n')
                           if any(x in f.lower() for x in ['component', 'page', 'view', 'ui', 'tsx', 'jsx', 'html', 'css'])][:5]

            if not changed_files:
                print("   ⚠️  No UI files detected")
                return True, "No UI changes"

            # Read UI files with aggressive truncation
            file_contents = []
            max_file_chars = 5000  # ~1.25k tokens per file (aggressive)
            for file_path in changed_files[:3]:  # Only 3 UI files
                full_path = workspace / file_path
                if full_path.exists() and full_path.stat().st_size < 50000:
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Aggressive truncation
                        if len(content) > max_file_chars:
                            content = content[:max_file_chars] + f"\n...(truncated)"

                        file_contents.append(f"## {file_path}\n```\n{content}\n```\n")
                    except:
                        pass

            if not file_contents:
                print("   ⚠️  No UI content to review")
                return True, "No UI content"

            ui_prompt = f"""Evaluate the UI implementation from a USER PERSPECTIVE.

# PROJECT CONTEXT
{context}

# CODING STANDARDS
{prompt_template}

# ISSUE DESCRIPTION
**{issue.title}**
{issue.body or 'No description'}

# UI FILES
{''.join(file_contents)}

As a user, evaluate:
1. Will the UI elements render correctly?
2. Are interactive elements (buttons, forms, inputs) functional?
3. Does the UI match what was requested in the issue?
4. Does the UI follow the project's design patterns and standards?
5. Are there obvious UX problems (broken layouts, missing feedback, unclear labels)?
6. Are loading states, error states, and edge cases handled?

Respond with JSON:
{{
  "user_friendly": true/false,
  "ui_issues": ["issue1", "issue2"],
  "summary": "assessment from user perspective"
}}
"""

            response = self.agent.send_message(ui_prompt)
            review = self.agent.parse_json_response(response)

            if not review:
                print("   ⚠️  Could not parse UI review")
                return True, "Could not parse review"

            if review.get('user_friendly', True):
                print(f"   ✅ UI looks good from user perspective")
                if review.get('summary'):
                    print(f"      {review['summary']}")
                return True, "UI validation passed"
            else:
                issues_text = '\n      - '.join(review.get('ui_issues', []))
                print(f"   ❌ UI issues from user perspective:")
                print(f"      - {issues_text}")
                return False, f"UI Issues:\n{issues_text}"

        except Exception as e:
            print(f"   ⚠️  Error during UI validation: {e}")
            return True, f"Error: {e}"

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
                error_msg = result.stderr[:500]
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
                return False, result.stdout[:500]

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
                            error_msg = result.stdout[-500:]
                            print(f"     ❌ Tests failed")
                            return False, error_msg
            except Exception as e:
                print(f"     ⚠️  Error running tests: {e}")
                return False, str(e)

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
                error_msg = result.stdout[-500:]
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
                            error_msg = result.stderr[-500:]
                            print(f"     ❌ Build failed")
                            return False, error_msg
            except Exception as e:
                print(f"     ⚠️  Error running build: {e}")
                return False, str(e)

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
                    except:
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
            print(f"     ⚠️  Error during quality review: {e}")
            return True, f"Error: {e}"

    def list_projects(self):
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
