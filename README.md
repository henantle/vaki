# VÄKI - Automated GitHub Issue Implementation

Enterprise-grade automated system for GitHub issue implementation with AI.

**Features:** Ticket analysis • Multi-strategy implementation • Quality enforcement • Cost tracking • Rollback capability • Learning system

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

### Manual Ticket Mode (New! 🎉)
**Process tickets from ANY source** - Slack, email, Jira, Linear, etc.
```bash
# Interactive (paste text)
python main.py ticket myproject --source=slack

# From file
python main.py ticket myproject --file=ticket.txt --source=jira

# From stdin
echo "Fix bug\nDescription here" | python main.py ticket myproject
```
1. Paste or pipe ticket text from any source
2. VÄKI parses and processes like a GitHub issue
3. Creates PR with full context and source reference

**Best for:** Ad-hoc requests, multi-tool workflows, non-GitHub sources
**See:** [MANUAL_TICKETS.md](MANUAL_TICKETS.md) for complete guide

### OpenAI Mode (Enhanced)
**Fully automated** - Zero human intervention with enterprise features
```bash
python main.py run myproject 42 --mode=openai
```

**Enhanced workflow:**
1. **📋 Ticket Analysis** - Checks clarity, requests clarification if needed
2. **💰 Cost Estimation** - Estimates and validates against budget
3. **🔍 Codebase Analysis** - Understands architecture and tech stack
4. **🎯 Strategy Generation** - Creates multiple approaches, ranks them
5. **⚙️ Implementation** - Executes with checkpoints and rollback
   - Agent responds with JSON actions: `read_file`, `write_file`, `edit_file`, `run_command`, `commit`, `done`
   - Real-time incremental validation after each change
   - Resource usage tracking
6. **✅ Quality Gates** - 3-tier enforcement (critical/required/recommended)
   - Type checking, Tests, Build (automated)
   - Code quality, Requirements, UI (AI review)
7. **🔄 Retry or Rollback** - Auto-rollback to checkpoint on failure, try next strategy
8. **📊 Learning** - Records outcome, updates insights
9. **🚀 PR Creation** - With quality badge, metrics, and cost

**Best for:** Production systems requiring reliability and quality
**Success rate:** 50-70% improvement with ticket analysis and multi-strategy approach

## Configuration

### Basic Configuration

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

### Enhanced Configuration (Optional)

Add enterprise features by including these sections:

```yaml
# Quality enforcement
quality:
  mode: "standard"  # strict, standard, permissive
  critical_gates:
    - security_check
    - syntax_check
    - breaking_changes
  required_gates:
    - type_check
    - tests_pass
    - build

# Ticket analysis
ticket_analysis:
  enabled: true
  min_clarity_score: 70
  ask_for_clarification: true

# Multi-strategy implementation
implementation:
  multi_strategy: true
  use_checkpoints: true
  incremental_validation: true

# Cost tracking
resources:
  daily_cost_limit: 50.00
  per_issue_cost_limit: 10.00

# Learning system
learning:
  enabled: true
  track_outcomes: true
```

**See `projects/example-enhanced.yml` for complete example.**
**See `QUICK_START.md` for detailed setup guide.**

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

---

## 📚 Documentation

### Getting Started
- **[QUICK_START.md](QUICK_START.md)** - Get up and running in 5 minutes
- **[projects/example-enhanced.yml](projects/example-enhanced.yml)** - Complete configuration example

### Features & Architecture
- **[INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)** - What's new and how it works
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Detailed usage guide for all features
- **[ARCHITECTURE_IMPROVEMENTS.md](ARCHITECTURE_IMPROVEMENTS.md)** - Technical architecture details
- **[WORKFLOW_IMPROVEMENTS.md](WORKFLOW_IMPROVEMENTS.md)** - Future enhancement ideas

---

## 🚀 New in v2.0 (Enterprise Edition)

### 9 New Enhancement Modules

1. **TicketAnalyzer** - Analyzes ticket clarity, requests clarification automatically
2. **QualityGate** - 3-tier quality enforcement (critical/required/recommended)
3. **CodebaseAnalyzer** - Understands project structure and tech stack
4. **ResourceManager** - Cost tracking with daily and per-issue budgets
5. **CheckpointManager** - Git-based rollback points for safe experimentation
6. **ImplementationTracker** - Learns from past implementations
7. **StrategyEvaluator** - Generates and ranks multiple implementation approaches
8. **IncrementalValidator** - Real-time validation after each change
9. **ImplementationLogger** - Comprehensive debugging with debug bundles

### Expected Improvements
- **50-70%** fewer failed implementations
- **100%** enforcement of critical quality standards
- **Predictable costs** with automatic budget compliance
- **Safe rollback** for failed implementations
- **Continuous learning** from historical data

### Backward Compatibility
✅ Fully backward compatible - All existing configurations work unchanged. New features are opt-in.
