# VÄKI Features Guide

**Understanding what VÄKI can do for you**

This guide explains each feature in plain English - what it does, why it's useful, and how to use it.

---

## 🎯 Ticket Analysis

### What It Does
Before implementing, VÄKI reads your issue and checks if it's clear enough. If not, it asks questions.

### Why It's Useful
**Problem:** Vague tickets like "Fix the thing" or "Make it faster" lead to wrong implementations.

**Solution:** VÄKI catches unclear tickets early and asks for clarification.

### Example

**Bad ticket:**
```
Title: Add feature
Description: Users want this
```

**VÄKI's response:**
```
❌ Clarity Score: 35/100

Missing information:
- What feature should be added?
- Where in the app?
- What should it do?

I've posted questions on your GitHub issue. Please clarify before I implement.
```

### How to Enable
```yaml
# projects/myproject.yml
ticket_analysis:
  enabled: true
  min_clarity_score: 70  # Require 70/100 score
  ask_for_clarification: true  # Auto-post questions
```

### Result
- **50-70% fewer failed implementations**
- **Better communication** with issue authors
- **Less time wasted** on unclear requirements

---

## 🛡️ Quality Gates

### What It Does
Runs multiple quality checks before creating a PR. Won't create PRs with critical problems.

### Why It's Useful
**Problem:** Auto-generated PRs might break tests, have syntax errors, or introduce bugs.

**Solution:** VÄKI checks everything before bothering you with a PR.

### Three Levels

**🔴 Critical (Must Pass)**
- Security vulnerabilities
- Syntax errors
- Breaking changes
- **Result:** No PR created if these fail

**🟡 Required (Should Pass)**
- Tests failing
- Type errors
- Build broken
- **Result:** PR created with warnings

**🟢 Recommended (Nice to Have)**
- Lint warnings
- Documentation missing
- **Result:** PR created with notes

### Example

```bash
Running quality checks...

✅ Security - No vulnerabilities
✅ Syntax - All files valid
✅ Tests - 47 passing
✅ Build - Success
⚠️  Lint - 2 warnings (non-blocking)

📊 Overall: ✅ PASSED

Creating pull request...
```

### How to Configure

```yaml
# Strict mode - everything must pass
quality:
  mode: "strict"
  critical_gates:
    - security_check
    - syntax_check
    - breaking_changes
  required_gates:
    - type_check
    - tests_pass
    - build
```

```yaml
# Permissive mode - only critical must pass
quality:
  mode: "permissive"
  critical_gates:
    - security_check
    - syntax_check
```

### Result
- **100% enforcement** of your quality standards
- **No broken PRs** to review
- **Clear reports** on what passed/failed

---

## 💰 Cost Tracking & Budgets

### What It Does
Tracks how much each implementation costs and stops if you exceed budget.

### Why It's Useful
**Problem:** AI API calls cost money. Without limits, a bug in VÄKI could cost hundreds of dollars overnight.

**Solution:** Set daily and per-issue budget limits. VÄKI stops automatically.

### Example

```bash
💰 Cost Estimate: $2.50 (125,000 tokens)

✅ Within budget:
   Daily: $12.50 / $50.00 (25%)
   Per-issue: $2.50 / $10.00 (25%)

Starting implementation...

... implementation happens ...

💰 RESOURCE USAGE
Session Usage:
  Cost: $2.38 (95% of estimate)
  Tokens: 118,432

Daily Budget:
  Used: $14.88 / $50.00 (30%)
  Remaining: $35.12

✅ All budgets within limits
```

### How to Configure

```yaml
resources:
  daily_cost_limit: 50.00      # Max $50 per day
  per_issue_cost_limit: 10.00  # Max $10 per issue
  per_issue_token_limit: 200000  # Max 200K tokens per issue
```

### What Happens When Budget Exceeded

```bash
💰 Cost Estimate: $12.00

❌ Implementation would exceed budget:
   Daily budget: $48 used / $50 limit
   This issue: $12 estimated
   Total would be: $60 (over limit by $10)

Implementation cancelled. Try again tomorrow or increase limit.
```

### Result
- **Predictable costs** - no surprises
- **Automatic protection** - stops before overspending
- **Visibility** - see exactly where money goes

---

## 🎯 Multi-Strategy Implementation

### What It Does
Generates 3-5 different ways to implement the feature, ranks them, and tries the best one first.

### Why It's Useful
**Problem:** There's usually more than one way to implement something. The first idea isn't always the best.

**Solution:** VÄKI explores multiple approaches and picks the safest/best one.

### Example

**Issue:** "Add dark mode toggle"

**VÄKI generates:**

```
Strategy 1: Context API Implementation
  Pros: Clean, React-idiomatic, scalable
  Cons: More files to change
  Risk: Low
  Score: 8.5/10

Strategy 2: CSS Variables Approach
  Pros: Simple, fast, no state management
  Cons: Less flexible, harder to extend
  Risk: Low
  Score: 7.8/10

Strategy 3: Third-party Library (next-themes)
  Pros: Battle-tested, feature-rich
  Cons: External dependency, learning curve
  Risk: Medium
  Score: 6.2/10

Trying Strategy 1: Context API Implementation
```

### If Strategy Fails

```
❌ Strategy 1 failed: Type errors in ThemeContext

Rolling back to checkpoint...

Trying Strategy 2: CSS Variables Approach

✅ Strategy 2 succeeded!
```

### How to Enable

```yaml
implementation:
  multi_strategy: true
  max_strategies: 3  # Generate up to 3 strategies
```

### Result
- **Better solutions** through exploration
- **Automatic fallback** if first approach fails
- **Learn best practices** from strategy comparisons

---

## 🔄 Checkpoints & Rollback

### What It Does
Creates save points before trying each approach. If something fails, rolls back to the save point.

### Why It's Useful
**Problem:** A failed implementation might leave your repo in a broken state.

**Solution:** VÄKI creates checkpoints (git commits) and can rollback cleanly.

### Example

```bash
Strategy 1: Database Migration Approach
📍 Checkpoint created: a3b2c1d4

Implementing...
  ✅ Create migration file
  ✅ Update models
  ❌ Tests failing: migration syntax error

🔄 Rolling back to checkpoint a3b2c1d4

Strategy 2: Incremental Update Approach
📍 Checkpoint created: b4c5d2e3

Implementing...
  ✅ All changes successful
  ✅ Tests passing

✅ Strategy 2 succeeded!
```

### How It Works

```
Before:        Checkpoint         After Strategy 1 Fails:
main ─┐        main ─┬─ checkpoint1     main ─┬─ checkpoint1 (rollback here)
      │              │                        │
    (clean)       (clean)                  (clean again)
```

### How to Enable

```yaml
implementation:
  use_checkpoints: true
```

### Result
- **Safe experimentation** - try risky approaches safely
- **Clean rollback** - no broken states
- **Multiple attempts** - keep trying until something works

---

## 📊 Learning System

### What It Does
Records every implementation (success/failure) and learns patterns over time.

### Why It's Useful
**Problem:** VÄKI might repeat the same mistakes.

**Solution:** Learns from history and suggests improvements.

### Example

**After 10 implementations:**

```bash
📊 Historical Insights:
   Success Rate: 85% (17/20 attempts)
   Average Cost: $3.20
   Average Time: 4.5 minutes

Common Success Patterns:
   ✅ React component changes: 95% success
   ✅ CSS modifications: 100% success
   ⚠️  Database changes: 60% success (risky)

💡 Suggestions for this issue:
   • Similar issues succeeded with Strategy A approach
   • Database-related issues need extra validation
   • Allocate more budget (avg $4.50 for this type)
```

### What It Learns

- Which types of issues succeed most
- Which strategies work best
- Common failure patterns
- Cost and time estimates
- Project-specific best practices

### How to Enable

```yaml
learning:
  enabled: true
  track_outcomes: true
  use_insights: true
```

### Result
- **Improves over time** - gets smarter with each issue
- **Project-specific knowledge** - learns your codebase
- **Better cost estimates** - predicts based on history

---

## 🔍 Real-Time Validation

### What It Does
Checks code quality after each file change, not just at the end.

### Why It's Useful
**Problem:** If VÄKI makes 10 changes and the 2nd one has a syntax error, it wastes time on the remaining 8.

**Solution:** Validate after each change and give immediate feedback.

### Example

**Without real-time validation:**
```bash
Change 1: Update component ✅
Change 2: Add helper (syntax error) ❌
Change 3: Update styles ✅
Change 4: Add tests ✅
...
Change 10: Done

Running validation... ❌ Failed!
(Wasted time on changes 3-10)
```

**With real-time validation:**
```bash
Change 1: Update component ✅
Change 2: Add helper
  ⚠️  Syntax error detected:
  Line 42: Missing closing brace

  Fixing syntax error...
  ✅ Fixed

Change 3: Update styles ✅
...
(All changes validated in real-time)
```

### How to Enable

```yaml
implementation:
  incremental_validation: true
```

### Result
- **Faster feedback** - catch errors immediately
- **Less wasted time** - don't continue with broken code
- **Better quality** - errors fixed as they occur

---

## 📝 Comprehensive Logging

### What It Does
Records everything VÄKI does for debugging and analysis.

### Why It's Useful
**Problem:** When something goes wrong, you need to know what happened.

**Solution:** Complete logs of every action, decision, and outcome.

### What Gets Logged

```
.vaki/logs/myproject/issue-42/
├── implementation.log          # Human-readable log
├── agent_interactions.jsonl    # All AI conversations
├── actions.jsonl              # Every action taken
├── metrics.json               # Cost, time, success
└── debug_bundle/              # Complete debug package
    ├── git_history.txt
    ├── git_diff.txt
    └── summary.txt
```

### Example Log

```
[14:23:45] ℹ️  [initialization] Phase start: initialization
[14:23:46] ℹ️  [ticket_analysis] Ticket analyzed
   Data: {"clarity_score": 85, "complexity": 6}
[14:23:50] ℹ️  [implementation] Starting implementation
[14:24:15] ⚠️  [implementation] Incremental validation failed
   Data: {"errors": ["Syntax error in Helper.tsx"]}
[14:24:20] ℹ️  [implementation] Error fixed
[14:25:30] ℹ️  [quality_verification] All quality gates passed
[14:25:45] ℹ️  [pr_creation] PR created
```

### Debug Bundle

When something fails, VÄKI creates a debug bundle with everything:

```bash
📦 Debug bundle created: .vaki/logs/myproject/issue-42/debug_bundle

Contains:
  - Complete logs
  - All AI interactions
  - Git history
  - Diff of changes
  - Metrics and timing
```

### How It's Used

Automatically enabled. No configuration needed!

### Result
- **Easy debugging** - see exactly what happened
- **Replay failures** - understand why something failed
- **Learn patterns** - analyze what works

---

## 🧠 Codebase Understanding

### What It Does
Analyzes your project before implementing to understand structure, patterns, and tech stack.

### Why It's Useful
**Problem:** VÄKI needs context. What framework? What patterns? Where are components?

**Solution:** Automatically detects tech stack and finds relevant files.

### Example

```bash
🔍 CODEBASE ANALYSIS

**Tech Stack:** React 18, TypeScript, Next.js 14, Tailwind CSS
**Framework:** Next.js with App Router
**Pattern:** Component-based architecture

**Structure:**
  ├── src/app/          (Next.js pages)
  ├── src/components/   (React components)
  ├── src/lib/          (Utilities)
  └── src/styles/       (Tailwind styles)

**Relevant files for this issue:**
  • src/components/Settings.tsx (settings page)
  • src/components/ThemeToggle.tsx (similar pattern)
  • src/lib/theme.ts (theme utilities)

Ready to implement with full context!
```

### What It Detects

- Programming languages (JavaScript, TypeScript, Python)
- Frameworks (React, Next.js, Express, Django)
- Build tools (Webpack, Vite, npm)
- Testing frameworks (Jest, pytest)
- Code patterns (MVC, component-based, etc.)

### How It's Used

Automatically happens before every implementation!

### Result
- **Smarter implementations** - understands your project
- **Follows patterns** - uses your existing style
- **Finds right files** - knows where to make changes

---

## 🎛️ Modes Comparison

Quick reference for which mode to use:

| Feature | OpenAI Mode | Claude Mode | Manual Ticket |
|---------|-------------|-------------|---------------|
| **Automation** | Full | Semi | Full |
| **Control** | AI decides | You decide | AI decides |
| **Speed** | 3-10 min | 15-60 min | 3-10 min |
| **Best For** | Routine tasks | Complex work | Any source |
| **Cost** | $1-15 | Your time | $1-15 |
| **Quality Features** | ✅ All | ❌ Manual | ✅ All |
| **Ticket Source** | GitHub | GitHub | Anywhere |

### When to Use Each

**OpenAI Mode:**
- Bug fixes
- Small features
- Repetitive tasks
- You trust VÄKI

**Claude Mode:**
- Complex features
- Architecture changes
- Learning how VÄKI works
- You want control

**Manual Ticket Mode:**
- Slack messages
- Email requests
- Jira tickets
- Ad-hoc requests

---

## 💡 Tips & Best Practices

### Start Simple
Don't enable all features on day 1. Start with:
```yaml
# Just the basics
name: myproject
github: {...}
filters: {...}
```

After a few successful runs, add:
```yaml
# Add quality gates
quality:
  mode: "standard"

# Add budget limits
resources:
  daily_cost_limit: 50.00
```

### Set Realistic Budgets
Base on your usage:
- **Testing:** $10/day, $3/issue
- **Small team:** $50/day, $10/issue
- **Production:** $100/day, $20/issue

### Review Every PR
VÄKI is smart but not perfect:
- ✅ Always review code before merging
- ✅ Check tests pass
- ✅ Verify it does what you wanted
- ✅ Learn from its approaches

### Use Clear Tickets
Help VÄKI help you:
- ✅ Clear titles: "Add dark mode toggle to settings"
- ❌ Vague titles: "Improve UI"
- ✅ Specific descriptions with requirements
- ❌ One-line descriptions without context

### Monitor Costs
Check regularly:
```bash
# View daily usage
cat .vaki/usage.json

# Check logs for cost per issue
cat .vaki/logs/myproject/issue-42/metrics.json
```

### Learn From History
Review successful implementations:
```bash
# View past outcomes
.vaki/implementations.jsonl

# Learn what works for your project
```

---

## 🎓 Learning Path

**Week 1: Basics**
1. Setup with basic configuration
2. Run 3-5 simple issues in OpenAI mode
3. Review PRs and learn VÄKI's style

**Week 2: Quality**
1. Add quality gates
2. Enable ticket analysis
3. Try manual ticket mode

**Week 3: Advanced**
1. Enable multi-strategy
2. Turn on checkpoints
3. Enable learning system

**Week 4: Production**
1. Set budget limits
2. Configure for all projects
3. Train team on usage

---

## ❓ FAQ

**Q: Which features should I enable first?**

A: Start with quality gates and budget limits. These protect you.

**Q: How do I know if a feature is working?**

A: Check the output - VÄKI prints what it's doing:
```bash
📋 PHASE 0: TICKET ANALYSIS
✅ Ticket Analysis Complete
   Clarity Score: 85/100
```

**Q: Can I disable features temporarily?**

A: Yes, just comment them out:
```yaml
# ticket_analysis:  # Disabled temporarily
#   enabled: true
```

**Q: What if I don't understand a feature?**

A: Try it on a simple issue and watch what happens. VÄKI is safe - you review everything before merging.

---

## 📞 Need Help?

- **Quick questions:** Check this guide
- **Setup help:** See [QUICK_START.md](QUICK_START.md)
- **Technical details:** See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Bugs:** Open a GitHub issue with logs

---

**Ready to use these features? Return to [README.md](README.md)** 🚀
