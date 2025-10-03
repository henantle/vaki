# Quick Start Guide

**Get VÄKI running in 2-5 minutes**

Choose your path:
- 🏃 **[Fast Track](#fast-track-2-minutes)** - Run your first issue NOW (minimal setup)
- 🎯 **[Full Setup](#full-setup-5-minutes)** - All features enabled (recommended)

---

## Prerequisites

You need:
- Python 3.8+
- Git
- GitHub account + token ([create here](https://github.com/settings/tokens))
- OpenAI API key ([get here](https://platform.openai.com/api-keys))

**First time?** Get your tokens first, then come back!

---

# Fast Track (2 minutes)

**Goal:** Run VÄKI on one issue RIGHT NOW

## Step 1: Install (30 seconds)

```bash
pip install -r requirements.txt
export GITHUB_TOKEN="ghp_your_token_here"
export OPENAI_API_KEY="sk_your_key_here"
```

---

## Step 2: Minimal Config (1 minute)

Create `projects/myproject.yml` with just 3 things changed:

```yaml
name: myproject

github:
  repo: "your-org/your-repo"        # ← CHANGE THIS
  base_branch: "main"
  username: "your-github-username"  # ← CHANGE THIS
  email: "your-email@example.com"   # ← CHANGE THIS

filters:
  assignee: "your-github-username"  # ← CHANGE THIS
  state: "open"
```

**That's it!** This is enough to get started.

---

## Step 3: Run It! (30 seconds)

```bash
# Process a specific issue (recommended for first try)
python main.py run myproject 42 --mode=openai

# Or process all assigned issues
python main.py run myproject --mode=openai
```

**That's it!** VÄKI will implement the issue and create a PR.

---

## What Just Happened?

VÄKI just:
1. 📋 Read your GitHub issue
2. 🔍 Analyzed your codebase
3. ⚙️ Implemented the changes
4. ✅ Ran basic checks
5. 🚀 Created a pull request

**Next:** Review the PR and merge if it looks good!

---

# Full Setup (5 minutes)

**Want all the enterprise features?** Add these to your config.

## Enhanced Configuration

Start with your minimal config and add these features:

### 1. Quality Gates (Highly Recommended)

**What:** Won't create PRs with critical issues
**Why:** Ensures high code quality automatically

```yaml
quality:
  mode: "standard"  # strict, standard, or permissive
  critical_gates:
    - security_check
    - syntax_check
  required_gates:
    - type_check
    - tests_pass
```

### 2. Budget Limits (Highly Recommended)

**What:** Stops before overspending on API calls
**Why:** Predictable costs, no surprises

```yaml
resources:
  daily_cost_limit: 50.00      # Max $50 per day
  per_issue_cost_limit: 10.00  # Max $10 per issue
```

### 3. Ticket Analysis (Recommended)

**What:** Checks if issue is clear before implementing
**Why:** 50-70% fewer failed implementations

```yaml
ticket_analysis:
  enabled: true
  min_clarity_score: 70
  ask_for_clarification: true
```

### 4. Multi-Strategy (Optional)

**What:** Tries multiple approaches, picks best one
**Why:** Better solutions, automatic fallback if first fails

```yaml
implementation:
  multi_strategy: true
  use_checkpoints: true
  incremental_validation: true
```

### 5. Learning System (Optional)

**What:** Learns from past implementations
**Why:** Gets smarter over time

```yaml
learning:
  enabled: true
  track_outcomes: true
```

**See all features explained:** [FEATURES.md](FEATURES.md)

---

## Example Output (With All Features Enabled)

Here's what you'll see when running with full features:

```
🤖 AUTO-PROCESSING ISSUE #42: Add dark mode toggle

📋 TICKET ANALYSIS
   Clarity Score: 85/100 ✅
   💰 Cost Estimate: $2.50

🔍 CODEBASE ANALYSIS
   Tech Stack: React + TypeScript + Next.js 14

🎯 MULTI-STRATEGY
   Generated 3 strategies, trying best first:
   1. Context API Implementation (Score: 8.5) ← Trying this

📍 Checkpoint created

⚙️  IMPLEMENTATION
   ✅ Created: src/contexts/ThemeContext.tsx
   ✅ Updated: src/components/Layout.tsx
   ✅ Committed changes

✅ QUALITY CHECKS
   ✅ Type Check
   ✅ Tests Pass
   ✅ Build Success

🚀 Pull Request created!
   https://github.com/org/repo/pull/123

💰 RESOURCE USAGE
   Cost: $2.38 (within budget)
   Daily: $2.38 / $50.00 (5%)
```

**With minimal config:** Same process, just skips ticket analysis and multi-strategy.

---

## Quick Config Templates

Copy one of these based on your needs:

### 🛡️ Conservative (Maximum Safety)
```yaml
# Best for: Production environments, critical projects
quality:
  mode: "strict"          # Strictest quality checks
ticket_analysis:
  min_clarity_score: 80   # Only clear tickets
resources:
  per_issue_cost_limit: 5.00  # Low budget per issue
```

### ⚖️ Balanced (Recommended Start)
```yaml
# Best for: Most teams, testing VÄKI
quality:
  mode: "standard"
ticket_analysis:
  min_clarity_score: 70
resources:
  per_issue_cost_limit: 10.00
```

### ⚡ Fast (Speed Priority)
```yaml
# Best for: Quick fixes, low-risk projects
quality:
  mode: "permissive"      # Fewer checks
ticket_analysis:
  enabled: false          # Skip analysis
resources:
  per_issue_cost_limit: 20.00
```

---

## Common Scenarios

### "I just want to try it"
Use the Fast Track minimal config. Run on one simple issue.

### "I need strict quality for production"
Add quality gates with `mode: "strict"` and set low cost limits.

### "I want to enable features gradually"
Start minimal, then add one feature at a time:
1. First run: basic config
2. Add budget limits
3. Add quality gates
4. Add ticket analysis
5. Add multi-strategy

### "I have Slack/email requests, not GitHub issues"
Use the manual ticket mode:
```bash
python main.py ticket myproject --source=slack
# Paste text, press Ctrl+D
```

See: [MANUAL_TICKETS.md](MANUAL_TICKETS.md)

---

## Troubleshooting

**Problem:** "Budget exceeded"
**Fix:** Increase `per_issue_cost_limit` or wait until tomorrow

**Problem:** "Ticket clarity too low"
**Fix:** Make your issue more detailed or lower `min_clarity_score`

**Problem:** "Quality gates failed"
**Fix:** Check the error messages, fix manually, or use `mode: "permissive"`

**Problem:** "Command not found"
**Fix:** Make sure you're in the vaki directory and ran `pip install -r requirements.txt`

**Problem:** "GitHub token invalid"
**Fix:** Create a new token at https://github.com/settings/tokens with repo permissions

---

## Tips for Success

### 1. Start Small
Run on 1-2 simple issues first. Learn how VÄKI works before automating everything.

### 2. Always Review PRs
VÄKI is smart, but you're the boss. Review code before merging, always.

### 3. Set Budget Limits
Typical costs:
- Bug fix: $1-3
- Small feature: $3-6
- Large feature: $8-15

Start with `per_issue_cost_limit: 10.00` and adjust.

### 4. Write Clear Issues
Help VÄKI help you:
- ✅ "Add dark mode toggle to settings page"
- ❌ "Make UI better"

### 5. Enable Features Gradually
Don't turn everything on day 1. Add features as you need them.

### 6. Check the Logs
When something fails, check `.vaki/logs/` for debug info.

---

## Next Steps

**Just Getting Started?**
1. Run the Fast Track (2 minutes)
2. Try 2-3 simple issues
3. Read [FEATURES.md](FEATURES.md) to understand what's possible

**Ready for Production?**
1. Add quality gates
2. Set budget limits
3. Enable ticket analysis
4. Review [best practices](README.md#common-questions)

**Want to Learn More?**
- 📘 [Features Guide](FEATURES.md) - What each feature does
- 📗 [Manual Tickets](MANUAL_TICKETS.md) - Process tickets from Slack/email
- 📕 [Technical Details](IMPLEMENTATION_SUMMARY.md) - For developers

---

## Quick Checklist

Before your first run:

- [ ] Installed dependencies (`pip install -r requirements.txt`)
- [ ] Set `GITHUB_TOKEN` and `OPENAI_API_KEY`
- [ ] Created `projects/myproject.yml`
- [ ] Updated repo, username, email in config
- [ ] Have an issue to test with

**Ready?** Run:
```bash
python main.py run myproject 42 --mode=openai
```

---

**You're all set! VÄKI is ready to save you hours of work.** 🚀

Questions? Check [README.md](README.md) or [FEATURES.md](FEATURES.md)
