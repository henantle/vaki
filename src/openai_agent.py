"""OpenAI Agent for automated code implementation."""

import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI


class OpenAIAgent:
    """Agent that uses OpenAI API to implement code changes."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize OpenAI agent.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.conversation_history: List[Dict[str, Any]] = []

    def create_implementation_prompt(
        self,
        issue_title: str,
        issue_body: str,
        project_context: str,
        prompt_template: str
    ) -> str:
        """
        Create initial prompt for implementation.

        Args:
            issue_title: Issue title
            issue_body: Issue description
            project_context: Project context and guidelines
            prompt_template: Prompt template with coding standards

        Returns:
            Formatted prompt
        """
        prompt = f"""You are an expert software engineer tasked with implementing a GitHub issue.

# PROJECT CONTEXT
{project_context}

# CODING STANDARDS
{prompt_template}

# ISSUE TO IMPLEMENT
**Title**: {issue_title}

**Description**:
{issue_body or 'No description provided'}

# YOUR TASK
Implement this issue following the project context and coding standards above.

You will work iteratively:
1. First, respond with your implementation plan as a JSON object with this structure:
   {{"plan": "Step-by-step plan", "files_to_read": ["file1.py", "file2.ts"]}}

2. I will provide you with the file contents you requested.

3. Then respond with actions to take as a JSON array:
   [
     {{"action": "read_file", "path": "path/to/file"}},
     {{"action": "write_file", "path": "path/to/file", "content": "full file content"}},
     {{"action": "edit_file", "path": "path/to/file", "search": "old code", "replace": "new code"}},
     {{"action": "run_command", "command": "npm install package"}},
     {{"action": "commit", "message": "commit message"}},
     {{"action": "done", "summary": "what was implemented"}}
   ]

4. I will execute those actions and give you results.

5. Continue until you use the "done" action.

IMPORTANT RULES:
- Always provide valid JSON responses
- Read files before editing them
- Make atomic, focused commits
- Test your changes when possible
- Use "done" action when implementation is complete

Start by responding with your implementation plan.
"""
        return prompt

    def send_message(self, message: str, system_prompt: Optional[str] = None) -> str:
        """
        Send message to OpenAI and get response.

        Args:
            message: User message
            system_prompt: Optional system prompt for first message

        Returns:
            Assistant response
        """
        # Validate message is not None or empty
        if not message:
            raise ValueError("Message cannot be None or empty")

        # Initialize conversation with system prompt if provided
        if system_prompt and not self.conversation_history:
            self.conversation_history.append({
                "role": "system",
                "content": system_prompt
            })

        # Add user message
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        # Get response from OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history,
            temperature=0.7,
            max_tokens=4096
        )

        assistant_message = response.choices[0].message.content

        # Validate assistant response
        if assistant_message is None:
            assistant_message = ""
            print("⚠️  Warning: OpenAI returned null content")

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def parse_json_response(self, response: str) -> Any:
        """
        Parse JSON from response.

        Args:
            response: Raw response text

        Returns:
            Parsed JSON object
        """
        # Try to find JSON in code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
        else:
            # Try to parse entire response as JSON
            json_str = response.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON: {e}")
            print(f"Response: {response[:200]}...")
            return None

    def reset_conversation(self):
        """Reset conversation history."""
        self.conversation_history = []

    def prune_conversation(self, keep_recent: int = 5):
        """
        Prune conversation history to prevent token limit issues.
        Keeps system message and recent N message pairs.

        Args:
            keep_recent: Number of recent message pairs to keep
        """
        if len(self.conversation_history) <= keep_recent * 2 + 1:
            return  # No need to prune

        # Keep system message (if exists)
        system_messages = [msg for msg in self.conversation_history if msg.get("role") == "system"]

        # Keep recent messages (user/assistant pairs)
        recent_messages = self.conversation_history[-(keep_recent * 2):]

        # Rebuild conversation
        self.conversation_history = system_messages + recent_messages
        print(f"   🔄 Pruned conversation history (kept {len(recent_messages)} recent messages)")

    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimate of token count (1 token ≈ 4 characters).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def get_conversation_token_estimate(self) -> int:
        """
        Get estimated token count for current conversation.

        Returns:
            Estimated total tokens in conversation
        """
        total = 0
        for msg in self.conversation_history:
            content = msg.get("content", "")
            total += self.estimate_tokens(content)
        return total
