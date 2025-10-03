# GPT-5.0 Pricing Information

**Status:** Estimated pricing based on expected progression from GPT-4o

---

## Current Pricing Configuration

VÄKI is now configured to use **GPT-5.0** as the default model for all OpenAI operations.

### Estimated Pricing

```python
"gpt-5.0": {
    "input": $5.00 per 1M tokens   # Estimated
    "output": $15.00 per 1M tokens # Estimated
}
```

### Comparison with Other Models

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GPT-5.0 | $5.00 (estimated) | $15.00 (estimated) |
| GPT-4o | $2.50 | $10.00 |
| GPT-4o-mini | $0.15 | $0.60 |

---

## Important Notes

### 1. Pricing May Change

The pricing shown above for GPT-5.0 is **estimated** based on:
- Historical pricing progression from GPT-4 to GPT-4o
- Typical model improvement cost increases
- Conservative estimation for budget safety

**When official GPT-5.0 pricing is announced:**
- Update pricing in `src/resource_manager.py`
- Update this document
- Adjust project budgets if needed

### 2. Model Availability

**Check model availability:**
- Ensure your OpenAI API key has access to GPT-5.0
- If GPT-5.0 is not available, you may need to:
  - Wait for general availability
  - Request beta access
  - Or temporarily revert to GPT-4o

### 3. Budget Considerations

With estimated GPT-5.0 pricing ($5/$15), typical costs:

**Per implementation:**
- Small fix: ~50K tokens = $0.50 - $1.50
- Medium feature: ~100K tokens = $1.00 - $3.00
- Large feature: ~200K tokens = $2.00 - $6.00

**Recommended budget adjustments:**
```yaml
resources:
  daily_cost_limit: 75.00      # Increased from 50.00
  per_issue_cost_limit: 15.00  # Increased from 10.00
```

---

## Updating Pricing

When official pricing is announced, update in one place:

**File:** `src/resource_manager.py`

```python
PRICING = {
    "gpt-5.0": {
        "input": X.XX / 1_000_000,   # Update with official price
        "output": Y.YY / 1_000_000,  # Update with official price
    },
    # ...
}
```

All cost tracking, estimation, and reporting will automatically use the updated values.

---

## Reverting to GPT-4o

If you need to use GPT-4o instead:

### Option 1: Per-project (recommended)
```python
# In your code, pass model explicitly
orchestrator = OpenAIOrchestrator(github_token, api_key)
orchestrator.agent = OpenAIAgent(api_key, model="gpt-4o")
```

### Option 2: Change defaults
Edit these files:
1. `src/openai_agent.py` - Line 12: `model: str = "gpt-4o"`
2. `src/resource_manager.py` - Line 61: `model: str = "gpt-4o"`
3. `src/openai_orchestrator.py` - Line 191: `model="gpt-4o"`

### Option 3: Environment variable
```bash
export OPENAI_MODEL="gpt-4o"
# Then modify code to read from environment
```

---

## Monitoring Costs

With the higher GPT-5.0 pricing, monitoring becomes more important:

### 1. Check After Each Run
```bash
# Cost is shown at end of implementation
💰 RESOURCE USAGE
Session Usage:
  Cost: $4.50
```

### 2. Review Daily Usage
```bash
cat .vaki/usage.json
```

### 3. Set Conservative Budgets
```yaml
resources:
  per_issue_cost_limit: 10.00  # Hard stop if exceeded
```

### 4. Use Dry Run Mode (future)
```bash
# Estimate cost before running
python main.py ticket myproject --dry-run
```

---

## FAQ

**Q: Is GPT-5.0 available now?**
A: Check OpenAI's API documentation and your account access. If not available, revert to GPT-4o.

**Q: What if the actual pricing is different?**
A: Update `src/resource_manager.py` PRICING dictionary with actual values.

**Q: Will this break existing budgets?**
A: Existing budget limits will still work, but you may hit limits faster with higher pricing.

**Q: Can I mix models?**
A: Yes, you can pass different models for different projects or operations. The default is just a starting point.

**Q: How much more expensive is GPT-5.0?**
A: Based on estimates: 2x input cost, 1.5x output cost compared to GPT-4o.

---

## Summary

✅ **Default model changed to GPT-5.0**
⚠️ **Pricing is estimated** - update when official pricing announced
💡 **Monitor costs closely** with the higher pricing tier
🔄 **Easy to revert** to GPT-4o if needed

---

*Last updated: 2025-10-03*
*Update this document when official GPT-5.0 pricing is announced*
