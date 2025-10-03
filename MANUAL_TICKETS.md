# Manual Ticket Processing

Process tickets from **any source** (Slack, email, Jira, Linear, etc.) and create PRs on GitHub automatically.

---

## Overview

The manual ticket feature allows you to process implementation requests from sources that don't have API integration with VÄKI. Simply paste your ticket text, and VÄKI will:

1. Parse the ticket (title, description)
2. Implement the changes with AI
3. Create a pull request on GitHub

**Perfect for:**
- Slack messages
- Email requests
- Jira/Linear tickets (without API setup)
- Internal tool tickets
- Ad-hoc requests
- Copy-pasted requirements

---

## Quick Start

### Interactive Mode (Paste Text)

```bash
python main.py ticket myproject

# System prompts:
# > Paste your ticket text below (press Ctrl+D when done):
# [Paste your text]
# [Press Ctrl+D]
```

### Pipe from Stdin

```bash
echo "Add dark mode
Users want dark mode for the app" | python main.py ticket myproject
```

### From File

```bash
python main.py ticket myproject --file=ticket.txt
```

### With Source Tag

```bash
python main.py ticket myproject --source=slack
python main.py ticket myproject --source=jira --file=jira-ticket.txt
```

---

## Command Options

```bash
python main.py ticket <project> [options]
```

### Options

- `--source=<name>` - Source identifier (slack, email, jira, linear, manual)
  - Default: `manual`
  - Appears in PR title: `[VÄKI] Feature (from slack)`

- `--file=<path>` - Read ticket from file
  - If not specified, reads from stdin (interactive or piped)

- `--mode=<mode>` - Processing mode (openai, claude)
  - Default: `openai` (recommended for manual tickets)
  - Claude mode requires human interaction

---

## Usage Examples

### Example 1: Slack Message

```bash
# Copy message from Slack, run command, paste, Ctrl+D
python main.py ticket myproject --source=slack
```

### Example 2: Email Request

```bash
# Save email to file
cat > email-request.txt << 'EOF'
Subject: Add export feature

Hi team,

We need an export to CSV feature for the user list.
Should include all visible columns.

Thanks!
EOF

# Process it
python main.py ticket myproject --source=email --file=email-request.txt
```

### Example 3: Jira Ticket

```bash
# Copy from Jira, pipe to VÄKI
pbpaste | python main.py ticket myproject --source=jira
```

### Example 4: Quick Fix

```bash
python main.py ticket myproject << 'EOF'
Fix login button alignment

The login button is misaligned on mobile devices.
Should be centered below the form.
EOF
```

---

## Ticket Text Format

VÄKI automatically parses your ticket text to extract:
- **Title** (first line or line with `Title:`, `Subject:`, `#`)
- **Body** (remaining text)

### Recommended Format

```
Title of the ticket

Detailed description of what needs to be done.
Can include multiple paragraphs.

Requirements:
- Requirement 1
- Requirement 2

Acceptance Criteria:
- [ ] Criteria 1
- [ ] Criteria 2
```

### Minimal Format

```
Fix the thing
It's broken
```

### Patterns VÄKI Recognizes

- `Title: Something` → Extracts "Something" as title
- `Subject: Something` → Extracts "Something" as title
- `# Something` → Extracts "Something" as title
- First line → Used as title if no pattern found

---

## What Happens

### 1. Ticket Parsing

VÄKI creates a `ManualTicket` object:
```
Manual Ticket #12345
Title: "Add dark mode toggle"
Source: slack
Body: "Users want dark mode..."
```

### 2. Implementation

Same enterprise workflow as GitHub issues:
- ✅ Ticket analysis (if enabled)
- ✅ Cost estimation
- ✅ Codebase analysis
- ✅ Multi-strategy implementation
- ✅ Quality gates
- ✅ Checkpoints & rollback
- ✅ All enhanced features

### 3. Pull Request Creation

PR is created on GitHub with:
- Title: `[VÄKI] Add dark mode toggle (from slack)`
- Body includes:
  - Implementation metrics
  - Original ticket reference
  - Source information
  - Quality status

**Example PR body:**

```markdown
🤖 Automated implementation by VÄKI AI

**Strategy Used:** Context API Implementation
**Quality Status:** ✅ All checks passed
**Files Changed:** 3
**Implementation Time:** 4.2m

---

📋 **Manual Ticket #12345** (from slack)

**Original Request:**
```
Add dark mode toggle to settings page

Users have requested a dark mode option...
```

**Description:**
Users have requested a dark mode option. The toggle should be in
the settings page and persist across sessions.
```

---

## Configuration

Manual tickets use your existing project configuration:

```yaml
# projects/myproject.yml

name: "My Project"
github:
  repo: "org/repo"
  base_branch: "main"

# All enhancement features work!
quality:
  mode: "standard"
ticket_analysis:
  enabled: true
implementation:
  multi_strategy: true
resources:
  per_issue_cost_limit: 10.00
```

No special configuration needed!

---

## Workflow Comparison

### GitHub Issues (Standard)
```
GitHub Issue #42 → VÄKI → PR (Closes #42)
```

### Manual Tickets (New)
```
Any Source → VÄKI → PR (from source)
```

**Both workflows:**
- Use same quality gates
- Use same strategy system
- Create PRs on GitHub
- Track costs and metrics

**Difference:**
- Manual tickets don't auto-close a GitHub issue
- PR title includes source: `(from slack)`
- PR body shows original ticket text

---

## Best Practices

### 1. Include Context

Good:
```
Add export feature to user list

Users need to export their user list to CSV.
Should include: name, email, role, created date.
```

Better:
```
Add CSV export to user list page

Requirements:
- Export button next to "Add User"
- CSV includes: name, email, role, created_at
- Filename: users-YYYY-MM-DD.csv
- Only exports filtered/visible users

Technical Notes:
- User list is in src/components/UserList.tsx
- Use existing CSV library (csv-stringify)
```

### 2. Use Descriptive Titles

- ❌ "Bug"
- ❌ "Fix it"
- ✅ "Fix login button alignment on mobile"
- ✅ "Add CSV export to user list"

### 3. Tag the Source

```bash
# Helps track where requests come from
python main.py ticket myproject --source=slack
python main.py ticket myproject --source=customer-email
python main.py ticket myproject --source=pm-request
```

### 4. Save Complex Tickets

```bash
# For tickets with lots of detail
vim ticket.txt  # Edit ticket
python main.py ticket myproject --file=ticket.txt
```

### 5. Use Git-Style Messages

```
Add dark mode toggle

Users want to switch between light and dark themes.

- Add toggle in settings
- Save to localStorage
- Apply theme globally
```

---

## Integration Examples

### From Slack Bot

```python
# Slack bot endpoint
@app.message({"type": "message", "text": re.compile("^@väki implement")})
def handle_implement_request(message, say):
    ticket_text = message["text"].replace("@väki implement", "").strip()

    # Save to temp file
    with open(f"/tmp/ticket-{message['ts']}.txt", "w") as f:
        f.write(ticket_text)

    # Call VÄKI
    subprocess.run([
        "python", "main.py", "ticket", "myproject",
        "--source=slack",
        f"--file=/tmp/ticket-{message['ts']}.txt"
    ])

    say("✅ Implementation started! I'll create a PR when done.")
```

### From Email Parser

```python
# Email handler
def handle_implementation_email(email):
    subject = email.subject
    body = email.body

    ticket_text = f"{subject}\n\n{body}"

    # Pipe to VÄKI
    process = subprocess.Popen(
        ["python", "main.py", "ticket", "myproject", "--source=email"],
        stdin=subprocess.PIPE
    )
    process.communicate(ticket_text.encode())
```

### From Jira Webhook

```python
# Jira webhook handler
@app.post("/jira/webhook")
def jira_webhook(request):
    issue = request.json["issue"]

    if "väki-auto-implement" in issue["fields"]["labels"]:
        ticket_text = f"{issue['fields']['summary']}\n\n{issue['fields']['description']}"

        subprocess.run(
            ["python", "main.py", "ticket", "myproject", "--source=jira"],
            input=ticket_text,
            text=True
        )
```

---

## Troubleshooting

### Issue: "No ticket text provided"

**Solution:** Make sure you're providing input
```bash
# Interactive: paste text and press Ctrl+D
python main.py ticket myproject

# Piped: provide content
echo "ticket text" | python main.py ticket myproject

# File: check file exists and has content
python main.py ticket myproject --file=ticket.txt
```

### Issue: Title not parsed correctly

**Solution:** Use explicit title format
```
Title: My Ticket Title

Rest of the description...
```

### Issue: Want to process with Claude Code

**Solution:** Add `--mode=claude`
```bash
python main.py ticket myproject --mode=claude
```

(Note: OpenAI mode is recommended for manual tickets)

### Issue: PR doesn't reference original issue

**Expected:** Manual tickets don't close GitHub issues. They create new PRs from external sources.

If you want to link to a GitHub issue:
- Use standard mode: `python main.py run myproject 42`
- Or mention issue in ticket text: "Fixes #42"

---

## Comparison with GitHub Issues

| Feature | GitHub Issues | Manual Tickets |
|---------|--------------|----------------|
| **Source** | GitHub | Any (Slack, email, Jira, etc.) |
| **API Required** | Yes | No |
| **PR Closes Issue** | Yes (`Closes #42`) | No (external source) |
| **Quality Gates** | ✅ | ✅ |
| **Multi-Strategy** | ✅ | ✅ |
| **Cost Tracking** | ✅ | ✅ |
| **Checkpoints** | ✅ | ✅ |
| **Learning** | ✅ | ✅ |
| **Branch Name** | `openai/issue-42` | `openai/manual-12345` |
| **PR Title** | `[VÄKI] Title` | `[VÄKI] Title (from slack)` |

---

## Tips

1. **Use for Ad-Hoc Requests**
   - Quick fixes from Slack
   - Customer requests via email
   - PM requirements from documents

2. **Track Sources**
   - Always use `--source=` to know where requests come from
   - Helps identify which sources generate most work

3. **Combine with GitHub**
   - Use GitHub issues for planned work
   - Use manual tickets for urgent/ad-hoc requests

4. **Create Templates**
   - Save common ticket formats in files
   - Use as starting point for similar requests

5. **Integrate with Tools**
   - Slack bot: auto-process @mentions
   - Email: auto-process tagged emails
   - Webhooks: auto-process from Jira/Linear

---

## Example Session

```bash
$ python main.py ticket vaki --source=slack

╦  ╦╔═╗╦╔═╦
╚╗╔╝╠═╣╠╩╗║
 ╚╝ ╩ ╩╩ ╩╩

Agentic Workflow System
Automated GitHub Issue Implementation

📋 Processing manual ticket for project: vaki
   Source: slack

Paste your ticket text below (press Ctrl+D when done):
──────────────────────────────────────────────────────────────────────
Add CSV export to dashboard

Users want to export their dashboard data to CSV.
Button should be in top right, next to filters.
Include all visible columns.
──────────────────────────────────────────────────────────────────────

✅ Manual ticket created:
   #38274: Add CSV export to dashboard

======================================================================
📦 PROJECT: VÄKI System (OpenAI Automated Mode)
📝 Enterprise-grade automated implementation system
======================================================================

📋 Processing manual ticket:
   Source: slack
   #38274: Add CSV export to dashboard

======================================================================
📋 PHASE 0: TICKET ANALYSIS
======================================================================
✅ Ticket Analysis Complete
   Clarity Score: 75/100 ✅
   Implementable: Yes
   Estimated Complexity: 5/10

💰 Cost Estimate: $3.20 (160,000 tokens)

======================================================================
🔍 CODEBASE ANALYSIS
======================================================================
**Tech Stack:** React, TypeScript, Material-UI
**Framework:** Next.js 14

[... implementation continues ...]

✅ Pull Request created: https://github.com/org/vaki/pull/123
```

---

## FAQ

**Q: Do I need a GitHub issue first?**
A: No! That's the point. Manual tickets work without GitHub issues.

**Q: Will the PR close a GitHub issue?**
A: No. Manual tickets are independent. If you want to reference an issue, mention it in the ticket text.

**Q: Can I use this with GitHub issues too?**
A: Yes! Use `python main.py run` for GitHub issues and `python main.py ticket` for manual tickets.

**Q: What if the ticket text is malformed?**
A: VÄKI does its best to parse it. First non-empty line becomes the title.

**Q: Can I customize the parsing?**
A: Currently no, but the parsing is flexible. Use `Title:` prefix for explicit control.

**Q: Does this work with all VÄKI features?**
A: Yes! Ticket analysis, quality gates, multi-strategy, cost tracking, etc. all work.

---

## Summary

**Manual tickets enable VÄKI to process implementation requests from ANY source:**

```bash
# Quick wins
python main.py ticket myproject                    # Interactive
echo "ticket" | python main.py ticket myproject    # Piped
python main.py ticket myproject --file=ticket.txt  # From file

# With metadata
python main.py ticket myproject --source=slack
python main.py ticket myproject --source=jira

# Still get all benefits
- ✅ Ticket analysis
- ✅ Quality gates
- ✅ Multi-strategy
- ✅ Cost tracking
- ✅ Checkpoints
- ✅ Learning
```

**Perfect for teams that:**
- Use multiple tools (Slack + GitHub + Jira)
- Want quick implementation without GitHub setup
- Get requests via email, chat, or documents
- Need flexibility in ticket sources

---

*Feature added in v2.1*
*Works with all v2.0 enterprise features*
