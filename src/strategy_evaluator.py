"""Strategy evaluation for multi-approach implementation."""

from typing import List, Dict
from dataclasses import dataclass
from github.Issue import Issue

from .openai_agent import OpenAIAgent
from .ticket_analyzer import TicketAnalysis


@dataclass
class ImplementationStrategy:
    """Represents one approach to solving an issue."""

    name: str
    approach: str
    pros: List[str]
    cons: List[str]
    estimated_complexity: int  # 1-10
    risk_level: str  # low, medium, high
    estimated_time: str  # e.g., "1-2 hours"


class StrategyEvaluator:
    """Evaluates and ranks implementation strategies."""

    def __init__(self, agent: OpenAIAgent):
        """
        Initialize strategy evaluator.

        Args:
            agent: OpenAI agent for strategy generation
        """
        self.agent = agent

    def generate_strategies(
        self,
        issue: Issue,
        context: str,
        analysis: TicketAnalysis,
        max_strategies: int = 3
    ) -> List[ImplementationStrategy]:
        """
        Generate multiple implementation strategies.

        Args:
            issue: GitHub issue
            context: Project context
            analysis: Ticket analysis
            max_strategies: Maximum number of strategies to generate

        Returns:
            List of implementation strategies
        """
        strategy_prompt = f"""Generate {max_strategies} different approaches to implement this GitHub issue.

# ISSUE
**Title:** {issue.title}
**Description:** {issue.body or 'No description'}

# ANALYSIS
**Complexity:** {analysis.estimated_complexity}/10
**Risk Level:** {analysis.risk_level}
**Strategy Suggested:** {analysis.implementation_strategy}

# YOUR TASK
Generate {max_strategies} distinct implementation strategies, from safest/simplest to most ambitious.

Respond with JSON array:
[
  {{
    "name": "Strategy name",
    "approach": "Brief description of approach",
    "pros": ["advantage 1", "advantage 2"],
    "cons": ["limitation 1", "limitation 2"],
    "estimated_complexity": 1-10,
    "risk_level": "low/medium/high",
    "estimated_time": "time estimate"
  }}
]

Consider different approaches like:
- Minimal change (safest, quickest)
- Standard implementation (balanced)
- Refactor + implement (cleanest, but more work)
- New abstraction (most flexible, highest complexity)
"""

        response = self.agent.send_message(strategy_prompt)
        strategies_data = self.agent.parse_json_response(response)

        if not strategies_data or not isinstance(strategies_data, list):
            # Fallback to default strategy
            return [ImplementationStrategy(
                name="Standard Implementation",
                approach=analysis.implementation_strategy,
                pros=["Follows analysis recommendation"],
                cons=["Only one approach considered"],
                estimated_complexity=analysis.estimated_complexity,
                risk_level=analysis.risk_level,
                estimated_time="Unknown"
            )]

        strategies = []
        for data in strategies_data[:max_strategies]:
            strategies.append(ImplementationStrategy(
                name=data.get("name", "Unknown"),
                approach=data.get("approach", ""),
                pros=data.get("pros", []),
                cons=data.get("cons", []),
                estimated_complexity=data.get("estimated_complexity", 5),
                risk_level=data.get("risk_level", "medium"),
                estimated_time=data.get("estimated_time", "Unknown")
            ))

        return strategies

    def rank_strategies(
        self,
        strategies: List[ImplementationStrategy],
        criteria: Dict[str, float]
    ) -> List[ImplementationStrategy]:
        """
        Rank strategies by weighted criteria.

        Args:
            strategies: List of strategies to rank
            criteria: Dict of criterion -> weight (must sum to 1.0)
                     e.g., {"safety": 0.4, "quality": 0.3, "speed": 0.3}

        Returns:
            Sorted list of strategies (best first)
        """
        scored_strategies = []

        for strategy in strategies:
            score = 0.0

            # Safety (inverse of risk)
            if "safety" in criteria:
                risk_scores = {"low": 1.0, "medium": 0.6, "high": 0.3}
                score += risk_scores.get(strategy.risk_level, 0.5) * criteria["safety"]

            # Quality (inverse of complexity, assuming simpler is better tested)
            if "quality" in criteria:
                quality_score = max(0, 1.0 - (strategy.estimated_complexity / 15))
                score += quality_score * criteria["quality"]

            # Speed (inverse of complexity and time)
            if "speed" in criteria:
                speed_score = max(0, 1.0 - (strategy.estimated_complexity / 12))
                score += speed_score * criteria["speed"]

            # Simplicity
            if "simplicity" in criteria:
                simplicity_score = max(0, 1.0 - (strategy.estimated_complexity / 10))
                score += simplicity_score * criteria["simplicity"]

            scored_strategies.append((score, strategy))

        # Sort by score descending
        scored_strategies.sort(key=lambda x: x[0], reverse=True)

        return [strategy for score, strategy in scored_strategies]

    def print_strategies(self, strategies: List[ImplementationStrategy]) -> None:
        """
        Print formatted strategies.

        Args:
            strategies: Strategies to print
        """
        print("\n" + "=" * 70)
        print("🎯 IMPLEMENTATION STRATEGIES")
        print("=" * 70)

        for i, strategy in enumerate(strategies, 1):
            print(f"\n{i}. {strategy.name}")
            print(f"   Approach: {strategy.approach}")
            print(f"   Complexity: {strategy.estimated_complexity}/10")
            print(f"   Risk: {strategy.risk_level.upper()}")
            print(f"   Time: {strategy.estimated_time}")

            if strategy.pros:
                print("   ✅ Pros:")
                for pro in strategy.pros:
                    print(f"      • {pro}")

            if strategy.cons:
                print("   ❌ Cons:")
                for con in strategy.cons:
                    print(f"      • {con}")

        print("=" * 70)
