# VÄKI - Automated GitHub Issue Implementation

Fetch GitHub issues, create branches, implement with AI, and create PRs automatically.

## Quick Start

```bash
# Install
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup .env
GITHUB_TOKEN=ghp_xxx
OPENAI_API_KEY=sk-xxx  # Optional, for --mode=openai

# Run (always activate venv first!)
source venv/bin/activate
python main.py list                              # List projects
python main.py run myproject 42                  # Semi-auto (Claude Code CLI)
python main.py run myproject 42 --mode=openai    # Fully auto (OpenAI)
```

## Modes

### Claude Mode (default)
**Semi-automated** - Human guides implementation
```bash
python main.py run myproject 42
```
1. Fetches issue, creates branch
2. Generates TASK.md with context
3. Launches Claude Code CLI
4. **You implement** with Claude's help
5. Creates PR when done

**Best for:** Complex features, architectural decisions

### OpenAI Mode
**Fully automated** - Zero human intervention
```bash
python main.py run myproject 42 --mode=openai
```

**How it works:**
1. Sends issue + context to OpenAI (gpt-4o)
2. Agent responds with JSON actions: `read_file`, `write_file`, `edit_file`, `run_command`, `commit`, `done`
3. Executes actions, sends results back to agent
4. Repeats until agent says `done` (max 20 iterations)
5. **Single combined verification** (1 API call):
   - ✅ Type checking, Tests, Build (automated)
   - 🤖 AI reviews code quality, requirements, and UI (single prompt)
6. **If verification fails:** Agent gets feedback and retries (max 3 attempts)
7. Creates PR (with quality warning if checks failed)

**Best for:** Simple bugs, repetitive tasks
**Token optimized:** Single verification pass = ~10-15k tokens (vs 40k+ with separate checks)

## Configuration

**1. Create project config** `projects/myproject.yml`:
```yaml
name: myproject
description: My awesome project
github:
  repo: owner/repo
  base_branch: main
filters:
  assignee: your-username
  state: open
context: contexts/myproject.md
prompt_template: prompts/templates/react-typescript.md
```

**2. Create context** `contexts/myproject.md`:
```markdown
# Tech Stack
- React + TypeScript
- Node.js + Express

# Coding Standards
- TypeScript strict mode
- Write tests for all features
```

**3. Create template** `prompts/templates/react-typescript.md`:
```markdown
# Guidelines
- Use functional components
- Prefer TypeScript interfaces
- Write unit tests
```

## Project Structure
```
vaki/
├── main.py              # Entry point
├── src/
│   ├── orchestrator.py           # Claude Code workflow
│   ├── openai_orchestrator.py    # OpenAI workflow
│   ├── openai_agent.py           # OpenAI agent
│   └── ...
├── projects/            # Project configs
├── contexts/            # Project contexts
└── prompts/templates/   # Coding standards
```

## Requirements

- Python 3.8+
- Git
- GitHub token (always required)
- Claude Code CLI (for Claude mode)
- OpenAI API key (for OpenAI mode)
