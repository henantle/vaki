# Quick Start: Enhanced VÄKI System

Get started with the enterprise-grade automated implementation system in 5 minutes.

---

## Prerequisites

- Python 3.8+
- GitHub account with repo access
- OpenAI API key
- Git configured locally

---

## Step 1: Basic Setup (2 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export GITHUB_TOKEN="your-github-token"
export OPENAI_API_KEY="your-openai-key"
```

---

## Step 2: Create Project Configuration (2 minutes)

```bash
# Copy example configuration
cp projects/example-enhanced.yml projects/my-project.yml
```

Edit `projects/my-project.yml`:

```yaml
name: "My Project"
description: "Your project description"

github:
  repo: "your-org/your-repo"      # Change this
  base_branch: "main"
  username: "your-github-username" # Change this
  email: "your-email@example.com"  # Change this

filters:
  assignee: "your-github-username" # Change this
  labels: ["enhancement", "bug"]
  state: "open"

workspace:
  temp_dir: "/tmp/vaki-workspaces"

context: "contexts/your-context.md"           # Optional
prompt_template: "templates/your-template.md" # Optional

# ============= ENHANCED FEATURES =============

# Quality enforcement (recommended)
quality:
  mode: "standard"  # Options: strict, standard, permissive
  critical_gates:
    - security_check
    - syntax_check
  required_gates:
    - type_check
    - tests_pass

# Ticket analysis (highly recommended)
ticket_analysis:
  enabled: true
  min_clarity_score: 70
  ask_for_clarification: true

# Resource limits (recommended)
resources:
  daily_cost_limit: 50.00
  per_issue_cost_limit: 10.00

# Multi-strategy (optional but recommended)
implementation:
  multi_strategy: true
  use_checkpoints: true
  incremental_validation: true

# Learning (recommended)
learning:
  enabled: true
  track_outcomes: true
```

---

## Step 3: Run Your First Enhanced Implementation (1 minute)

```bash
# Process all assigned issues
python main.py my-project

# Or process a specific issue
python main.py my-project --issue 123
```

---

## What Happens Now?

The enhanced system will:

1. **📋 Analyze Ticket** (if enabled)
   - Check clarity score
   - Identify missing information
   - Request clarification if needed

2. **💰 Check Budget**
   - Estimate cost
   - Ensure within limits

3. **🔍 Analyze Codebase**
   - Detect tech stack
   - Understand architecture

4. **🎯 Generate Strategies** (if enabled)
   - Create 3 implementation approaches
   - Rank by safety/quality/speed

5. **⚙️ Implement with Safety**
   - Create checkpoint
   - Execute with validation
   - Auto-rollback if fails

6. **✅ Enforce Quality**
   - Run critical checks
   - Run required checks
   - Report any issues

7. **🚀 Create PR**
   - With quality badge
   - Cost metrics
   - Strategy used

8. **📊 Learn**
   - Record outcome
   - Update insights
   - Improve over time

---

## Example Output

```
======================================================================
🤖 AUTO-PROCESSING ISSUE #42
======================================================================
Title: Add dark mode toggle
URL: https://github.com/org/repo/issues/42

======================================================================
📋 PHASE 0: TICKET ANALYSIS
======================================================================
✅ Ticket Analysis Complete
   Clarity Score: 85/100 ✅
   Implementable: Yes
   Estimated Complexity: 6/10
   Risk Level: medium

💰 Cost Estimate: $2.50 (125,000 tokens)

======================================================================
🔍 CODEBASE ANALYSIS
======================================================================
**Tech Stack:** React, TypeScript, Tailwind CSS
**Framework:** Next.js 14
**Pattern:** Component-based architecture

======================================================================
🎯 STRATEGY GENERATION
======================================================================
Generated 3 strategies:
1. Context API Implementation (Score: 8.5)
2. CSS Variables Approach (Score: 7.8)
3. Third-party Theme Library (Score: 6.2)

✅ Generated 3 strategies (ranked by criteria)

📊 Historical Insights: 87.5% success rate over 8 attempts
💡 Suggestions based on history:
   • Similar UI features succeeded with Context API approach
   • Testing is critical for this project - ensure coverage

======================================================================
🎯 STRATEGY 1/3: Context API Implementation
======================================================================
Approach: Create React Context for theme state...
Risk: medium | Complexity: 6/10

📍 Checkpoint created: a3b2c1d4

──────────────────────────────────────────────────────────────────────
🔄 ATTEMPT 1/3 for Context API Implementation
──────────────────────────────────────────────────────────────────────

⚙️  PHASE 1: IMPLEMENTATION

✅ Read file: src/components/Layout.tsx
✅ Wrote file: src/contexts/ThemeContext.tsx
✅ Edited file: src/components/Layout.tsx
✅ Committed: feat: add theme context and dark mode toggle

✅ Implementation phase complete

🔄 Resetting conversation for verification (fresh perspective)

======================================================================
🔍 PHASE 2: QUALITY VERIFICATION
======================================================================

📋 Running automated quality checks...
   ✅ Type Check
   ✅ Tests
   ✅ Build

🤖 AI reviewing code quality, requirements, and UI...
   ✅ Code Quality
   ✅ Requirements Met
   ✅ UI Functional

📊 Overall: ✅ PASSED

✅ Strategy succeeded!

======================================================================
🚀 CREATING PULL REQUEST
======================================================================

✅ Pull Request created: https://github.com/org/repo/pull/123

======================================================================
💰 RESOURCE USAGE
======================================================================
Session Usage:
  Tokens: 118,432 (94.7% of estimate)
  Cost: $2.38 (95.2% of estimate)

Daily Budget:
  Used: $2.38 / $50.00 (4.8%)
  Remaining: $47.62

Issue Budget:
  Used: $2.38 / $10.00 (23.8%)
  Remaining: $7.62

✅ All budgets within limits
```

---

## Configuration Presets

### Conservative (Safest)
```yaml
quality:
  mode: "strict"
ticket_analysis:
  enabled: true
  min_clarity_score: 80
implementation:
  multi_strategy: true
  max_strategies: 3
resources:
  daily_cost_limit: 30.00
  per_issue_cost_limit: 5.00
```

### Balanced (Recommended)
```yaml
quality:
  mode: "standard"
ticket_analysis:
  enabled: true
  min_clarity_score: 70
implementation:
  multi_strategy: true
resources:
  daily_cost_limit: 50.00
  per_issue_cost_limit: 10.00
```

### Aggressive (Fastest)
```yaml
quality:
  mode: "permissive"
ticket_analysis:
  enabled: false
implementation:
  multi_strategy: false
resources:
  daily_cost_limit: 100.00
  per_issue_cost_limit: 20.00
```

---

## Common Tasks

### Enable Only Ticket Analysis
```yaml
ticket_analysis:
  enabled: true
# Don't include other enhancement configs
```

### Add Budget Limits Only
```yaml
resources:
  daily_cost_limit: 50.00
  per_issue_cost_limit: 10.00
# Don't include other enhancement configs
```

### Full Enterprise Mode
```yaml
# Include all enhancement sections
quality: {...}
ticket_analysis: {...}
implementation: {...}
resources: {...}
learning: {...}
```

### Legacy Mode (No Enhancements)
```yaml
# Just include the basic required fields
name: "..."
github: {...}
filters: {...}
# No enhancement configs
```

---

## Troubleshooting

### Issue: "Budget exceeded"
**Solution:** Increase limits in `resources` config or wait until next day.

### Issue: "Ticket clarity too low"
**Solution:**
- Answer clarification questions posted to GitHub issue
- Or lower `min_clarity_score`
- Or disable `ask_for_clarification`

### Issue: "Critical quality gates failed"
**Solution:**
- Check error messages in output
- Fix issues manually
- Or change `quality.mode` to "standard"

### Issue: "All strategies failed"
**Solution:**
- Check `.vaki/logs/` for debug bundle
- Review implementation_logger output
- Consider simplifying the issue
- Try with `multi_strategy: false`

---

## Best Practices

1. **Start Conservative**
   - Use "standard" quality mode
   - Enable ticket analysis
   - Set reasonable budget limits

2. **Monitor First Run**
   - Watch the output carefully
   - Check generated PR quality
   - Adjust configuration based on results

3. **Iterate Configuration**
   - Start with basic enhancements
   - Add features gradually
   - Tune thresholds based on experience

4. **Review Historical Data**
   - Check `.vaki/implementations.jsonl`
   - Look for patterns in failures
   - Adjust strategy based on insights

5. **Set Appropriate Budgets**
   - Small fixes: $2-5 per issue
   - Medium features: $5-10 per issue
   - Large refactors: $10-20 per issue

---

## Getting Help

- **Detailed Docs:** `IMPLEMENTATION_SUMMARY.md`
- **Architecture:** `ARCHITECTURE_IMPROVEMENTS.md`
- **Configuration:** `projects/example-enhanced.yml`
- **Status:** `INTEGRATION_COMPLETE.md`

---

## Success Checklist

Before running in production:

- [ ] Created project configuration
- [ ] Set GitHub token and OpenAI key
- [ ] Configured filters (assignee, labels)
- [ ] Enabled ticket analysis (recommended)
- [ ] Set budget limits (recommended)
- [ ] Tested with 1-2 simple issues first
- [ ] Reviewed generated PRs
- [ ] Tuned configuration based on results

---

**You're ready to go! 🚀**

Run `python main.py my-project` and watch the magic happen.
