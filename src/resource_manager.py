"""Resource and cost management for API usage tracking."""

import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class CostEstimate:
    """Estimated cost for an operation."""

    tokens: int
    cost: float
    confidence: float  # 0-1


@dataclass
class Usage:
    """Resource usage tracking."""

    tokens: int = 0
    cost: float = 0.0
    api_calls: int = 0


@dataclass
class BudgetConfig:
    """Budget configuration."""

    daily_token_limit: int = 1_000_000
    daily_cost_limit: float = 50.00
    per_issue_token_limit: int = 200_000
    per_issue_cost_limit: float = 10.00


class ResourceManager:
    """Manages API costs and resource usage with quota enforcement."""

    # Pricing (as of 2024 - update as needed)
    PRICING = {
        "gpt-4o": {
            "input": 2.50 / 1_000_000,   # $2.50 per 1M input tokens
            "output": 10.00 / 1_000_000,  # $10.00 per 1M output tokens
        },
        "gpt-4o-mini": {
            "input": 0.150 / 1_000_000,   # $0.15 per 1M input tokens
            "output": 0.600 / 1_000_000,  # $0.60 per 1M output tokens
        }
    }

    def __init__(
        self,
        budget: BudgetConfig,
        storage_path: Optional[Path] = None,
        model: str = "gpt-4o"
    ):
        """
        Initialize resource manager.

        Args:
            budget: Budget configuration
            storage_path: Path to store usage data
            model: Model being used for pricing
        """
        self.budget = budget
        self.model = model
        self.storage_path = storage_path or Path(".vaki/usage.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or initialize usage data
        self.usage_data = self._load_usage()

        # Current session tracking
        self.session_usage = Usage()
        self.current_issue_usage = Usage()

    def check_quota(self, operation: str, estimated_tokens: int = 0) -> bool:
        """
        Check if operation is within quota.

        Args:
            operation: Name of operation
            estimated_tokens: Estimated token usage

        Returns:
            True if within quota, False otherwise
        """
        today = str(date.today())
        today_usage = self.usage_data.get(today, Usage())

        # Check daily limits
        if today_usage.tokens + estimated_tokens > self.budget.daily_token_limit:
            print(f"⚠️  Daily token limit exceeded ({today_usage.tokens}/{self.budget.daily_token_limit})")
            return False

        estimated_cost = self._estimate_cost(estimated_tokens)
        if today_usage.cost + estimated_cost > self.budget.daily_cost_limit:
            print(f"⚠️  Daily cost limit exceeded (${today_usage.cost:.2f}/${self.budget.daily_cost_limit:.2f})")
            return False

        # Check per-issue limits if tracking an issue
        if self.current_issue_usage.tokens > 0:
            if self.current_issue_usage.tokens + estimated_tokens > self.budget.per_issue_token_limit:
                print(f"⚠️  Per-issue token limit exceeded ({self.current_issue_usage.tokens}/{self.budget.per_issue_token_limit})")
                return False

            if self.current_issue_usage.cost + estimated_cost > self.budget.per_issue_cost_limit:
                print(f"⚠️  Per-issue cost limit exceeded (${self.current_issue_usage.cost:.2f}/${self.budget.per_issue_cost_limit:.2f})")
                return False

        return True

    def record_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        operation: Optional[str] = None
    ) -> None:
        """
        Record API usage.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            operation: Optional operation name for logging
        """
        total_tokens = input_tokens + output_tokens
        cost = self._calculate_cost(input_tokens, output_tokens)

        # Update session usage
        self.session_usage.tokens += total_tokens
        self.session_usage.cost += cost
        self.session_usage.api_calls += 1

        # Update current issue usage
        self.current_issue_usage.tokens += total_tokens
        self.current_issue_usage.cost += cost
        self.current_issue_usage.api_calls += 1

        # Update daily usage
        today = str(date.today())
        if today not in self.usage_data:
            self.usage_data[today] = Usage()

        self.usage_data[today].tokens += total_tokens
        self.usage_data[today].cost += cost
        self.usage_data[today].api_calls += 1

        # Save to file
        self._save_usage()

        # Alert if approaching limits
        self._check_alerts()

        # Log
        if operation:
            print(f"💰 {operation}: {total_tokens:,} tokens (${cost:.3f}) | "
                  f"Issue total: ${self.current_issue_usage.cost:.2f}")

    def start_issue_tracking(self) -> None:
        """Start tracking usage for a new issue."""
        self.current_issue_usage = Usage()

    def get_issue_usage(self) -> Usage:
        """
        Get usage for current issue.

        Returns:
            Usage data for current issue
        """
        return self.current_issue_usage

    def get_today_usage(self) -> Usage:
        """
        Get usage for today.

        Returns:
            Usage data for today
        """
        today = str(date.today())
        return self.usage_data.get(today, Usage())

    def get_cost_estimate(
        self,
        context_size: int,
        issue_complexity: int = 5
    ) -> CostEstimate:
        """
        Estimate cost for implementing an issue.

        Args:
            context_size: Size of project context in characters
            issue_complexity: Complexity rating 1-10

        Returns:
            CostEstimate
        """
        # Rough estimation model
        # Context sent once, multiple iterations
        context_tokens = context_size // 4  # Rough approximation

        # Estimated interactions based on complexity
        iterations = min(3 + issue_complexity, 15)

        # Estimated tokens per iteration
        input_per_iteration = 1000 + (context_tokens if iterations == 1 else 0)
        output_per_iteration = 2000

        total_input = context_tokens + (iterations * input_per_iteration)
        total_output = iterations * output_per_iteration
        total_tokens = total_input + total_output

        cost = self._calculate_cost(total_input, total_output)

        # Confidence decreases with complexity
        confidence = max(0.3, 1.0 - (issue_complexity / 15))

        return CostEstimate(
            tokens=total_tokens,
            cost=cost,
            confidence=confidence
        )

    def print_usage_summary(self) -> None:
        """Print usage summary."""
        today_usage = self.get_today_usage()

        print("\n" + "=" * 70)
        print("💰 RESOURCE USAGE SUMMARY")
        print("=" * 70)

        # Today's usage
        print(f"\n📅 Today:")
        print(f"   Tokens: {today_usage.tokens:,} / {self.budget.daily_token_limit:,}")
        print(f"   Cost: ${today_usage.cost:.2f} / ${self.budget.daily_cost_limit:.2f}")
        print(f"   API Calls: {today_usage.api_calls}")

        # Current issue usage
        if self.current_issue_usage.tokens > 0:
            print(f"\n🎯 Current Issue:")
            print(f"   Tokens: {self.current_issue_usage.tokens:,} / {self.budget.per_issue_token_limit:,}")
            print(f"   Cost: ${self.current_issue_usage.cost:.2f} / ${self.budget.per_issue_cost_limit:.2f}")
            print(f"   API Calls: {self.current_issue_usage.api_calls}")

        # Session usage
        if self.session_usage.tokens > 0:
            print(f"\n🔄 Session:")
            print(f"   Tokens: {self.session_usage.tokens:,}")
            print(f"   Cost: ${self.session_usage.cost:.2f}")
            print(f"   API Calls: {self.session_usage.api_calls}")

        print("=" * 70)

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in dollars
        """
        pricing = self.PRICING.get(self.model, self.PRICING["gpt-4o"])
        return (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])

    def _estimate_cost(self, tokens: int, ratio: float = 0.4) -> float:
        """
        Estimate cost assuming input/output ratio.

        Args:
            tokens: Total estimated tokens
            ratio: Input to total ratio (default 0.4 = 40% input, 60% output)

        Returns:
            Estimated cost
        """
        input_tokens = int(tokens * ratio)
        output_tokens = tokens - input_tokens
        return self._calculate_cost(input_tokens, output_tokens)

    def _check_alerts(self) -> None:
        """Check and alert if approaching limits."""
        today_usage = self.get_today_usage()

        # Daily alerts at 80% and 90%
        token_pct = (today_usage.tokens / self.budget.daily_token_limit) * 100
        cost_pct = (today_usage.cost / self.budget.daily_cost_limit) * 100

        if token_pct >= 90:
            print(f"🚨 WARNING: Daily token usage at {token_pct:.0f}%")
        elif token_pct >= 80:
            print(f"⚠️  NOTICE: Daily token usage at {token_pct:.0f}%")

        if cost_pct >= 90:
            print(f"🚨 WARNING: Daily cost at {cost_pct:.0f}%")
        elif cost_pct >= 80:
            print(f"⚠️  NOTICE: Daily cost at {cost_pct:.0f}%")

    def _load_usage(self) -> Dict[str, Usage]:
        """
        Load usage data from file.

        Returns:
            Usage data dictionary
        """
        if not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            # Convert to Usage objects
            usage_dict = {}
            for date_str, usage_data in data.items():
                usage_dict[date_str] = Usage(**usage_data)

            return usage_dict

        except (json.JSONDecodeError, IOError):
            return {}

    def _save_usage(self) -> None:
        """Save usage data to file."""
        try:
            # Convert Usage objects to dicts
            data = {
                date_str: asdict(usage)
                for date_str, usage in self.usage_data.items()
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

        except IOError as e:
            print(f"⚠️  Could not save usage data: {e}")

    def get_usage_report(self, days: int = 7) -> Dict[str, Usage]:
        """
        Get usage report for last N days.

        Args:
            days: Number of days to include

        Returns:
            Dictionary of date -> Usage
        """
        from datetime import timedelta

        report = {}
        today = date.today()

        for i in range(days):
            date_str = str(today - timedelta(days=i))
            if date_str in self.usage_data:
                report[date_str] = self.usage_data[date_str]

        return report
