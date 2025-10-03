#!/usr/bin/env python3
"""
VÄKI Agent - Automated GitHub Issue Implementation

Usage:
    python main.py list                          # List all projects
    python main.py run <project>                 # Process all issues (Claude Code mode)
    python main.py run <project> <issue>         # Process specific issue (Claude Code mode)
    python main.py run <project> --mode=openai   # Process with OpenAI automation
    python main.py run <project> <issue> --mode=openai  # Process specific issue with OpenAI
    python main.py ticket <project>              # Process manual ticket (from stdin or file)
"""

import os
import sys
from dotenv import load_dotenv
from src.orchestrator import AgentOrchestrator
from src.openai_orchestrator import OpenAIOrchestrator


def print_banner():
    """Print application banner."""
    print("""
╦  ╦╔═╗╦╔═╦
╚╗╔╝╠═╣╠╩╗║
 ╚╝ ╩ ╩╩ ╩╩

Agentic Workflow System
Automated GitHub Issue Implementation
""")


def print_usage():
    """Print usage information."""
    print("""Usage:
  python main.py list                              List all configured projects
  python main.py run <project>                     Process all assigned issues (Claude Code)
  python main.py run <project> <issue>             Process specific issue (Claude Code)
  python main.py run <project> --mode=openai       Process all issues (OpenAI auto)
  python main.py run <project> <issue> --mode=openai  Process specific issue (OpenAI auto)
  python main.py ticket <project> [options]        Process manual ticket (from any source)

Ticket Command Options:
  --source=<name>     Source name (slack, email, jira, manual) [default: manual]
  --file=<path>       Read ticket from file instead of stdin
  --mode=<mode>       Processing mode (claude, openai) [default: openai]

Modes:
  claude (default)  Semi-automated with Claude Code CLI (human-in-the-loop)
  openai           Fully automated with OpenAI API (no human intervention)

Examples:
  python main.py list
  python main.py run vainamoinen
  python main.py run vainamoinen 42
  python main.py run vainamoinen --mode=openai
  python main.py run vainamoinen 42 --mode=openai

  # Manual tickets (paste ticket text when prompted)
  python main.py ticket vainamoinen
  python main.py ticket vainamoinen --source=slack
  echo "Fix login bug\nUsers cannot login" | python main.py ticket vainamoinen
  python main.py ticket vainamoinen --file=ticket.txt --source=jira

Environment Variables:
  GITHUB_TOKEN      GitHub personal access token (required)
  OPENAI_API_KEY    OpenAI API key (required for --mode=openai)

Configuration:
  - Add project configs to projects/<name>.yml
  - Add project contexts to contexts/<name>.md
  - Add prompt templates to prompts/templates/<name>.md
""")


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Check for GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ Error: GITHUB_TOKEN not found in environment")
        print("Please set GITHUB_TOKEN in .env file or environment")
        sys.exit(1)

    # Register tokens for sanitization (SECURITY)
    from src.security import register_token
    register_token(github_token)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        register_token(openai_api_key)

    # Parse command line arguments
    if len(sys.argv) < 2:
        print_banner()
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "list":
            print_banner()
            # Create orchestrator (either works for listing)
            orchestrator = AgentOrchestrator(github_token)
            orchestrator.list_projects()

        elif command == "run":
            if len(sys.argv) < 3:
                print("❌ Error: Project name required")
                print("Usage: python main.py run <project> [issue-number] [--mode=openai]")
                sys.exit(1)

            # Parse arguments
            project_name = sys.argv[2]
            issue_number = None
            mode = "claude"  # Default mode

            # Parse remaining arguments
            for arg in sys.argv[3:]:
                if arg.startswith("--mode="):
                    mode = arg.split("=")[1].lower()
                elif arg.isdigit():
                    issue_number = int(arg)

            print_banner()

            # Create appropriate orchestrator based on mode
            if mode == "openai":
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key:
                    print("❌ Error: OPENAI_API_KEY not found in environment")
                    print("Please set OPENAI_API_KEY in .env file or environment")
                    sys.exit(1)

                orchestrator = OpenAIOrchestrator(github_token, openai_api_key)
            else:
                orchestrator = AgentOrchestrator(github_token)

            orchestrator.run_project(project_name, issue_number)

        elif command == "ticket":
            if len(sys.argv) < 3:
                print("❌ Error: Project name required")
                print("Usage: python main.py ticket <project> [--source=slack] [--file=path] [--mode=openai]")
                sys.exit(1)

            # Parse arguments
            project_name = sys.argv[2]
            source = "manual"
            file_path = None
            mode = "openai"  # Default to OpenAI for manual tickets

            # Parse options
            for arg in sys.argv[3:]:
                if arg.startswith("--source="):
                    source = arg.split("=")[1]
                elif arg.startswith("--file="):
                    file_path = arg.split("=")[1]
                elif arg.startswith("--mode="):
                    mode = arg.split("=")[1].lower()

            print_banner()
            print(f"📋 Processing manual ticket for project: {project_name}")
            print(f"   Source: {source}")
            print()

            # Read ticket text
            if file_path:
                print(f"Reading ticket from: {file_path}")
                try:
                    with open(file_path, 'r') as f:
                        ticket_text = f.read()
                except FileNotFoundError:
                    print(f"❌ Error: File not found: {file_path}")
                    sys.exit(1)
                except Exception as e:
                    print(f"❌ Error reading file: {e}")
                    sys.exit(1)
            else:
                # Read from stdin
                import select
                if select.select([sys.stdin], [], [], 0.0)[0]:
                    # Data available on stdin (piped input)
                    ticket_text = sys.stdin.read()
                else:
                    # Interactive mode - prompt user
                    print("Paste your ticket text below (press Ctrl+D when done):")
                    print("─" * 70)
                    lines = []
                    try:
                        while True:
                            line = input()
                            lines.append(line)
                    except EOFError:
                        pass
                    ticket_text = '\n'.join(lines)
                    print("─" * 70)

            if not ticket_text.strip():
                print("❌ Error: No ticket text provided")
                sys.exit(1)

            # Create manual ticket
            from src.manual_ticket import parse_manual_ticket
            manual_ticket = parse_manual_ticket(ticket_text, source)

            print(f"\n✅ Manual ticket created:")
            print(f"   #{manual_ticket.number}: {manual_ticket.title}")
            print()

            # Process with appropriate orchestrator
            if mode == "openai":
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key:
                    print("❌ Error: OPENAI_API_KEY not found in environment")
                    print("Please set OPENAI_API_KEY in .env file or environment")
                    sys.exit(1)

                orchestrator = OpenAIOrchestrator(github_token, openai_api_key)
                orchestrator.run_manual_ticket(project_name, manual_ticket)
            else:
                orchestrator = AgentOrchestrator(github_token)
                orchestrator.run_manual_ticket(project_name, manual_ticket)

        else:
            print(f"❌ Error: Unknown command '{command}'")
            print_usage()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
