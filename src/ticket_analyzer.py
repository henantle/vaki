"""Ticket analysis for clarity and completeness assessment."""

import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from github.Issue import Issue

from .openai_agent import OpenAIAgent
from .github_client import GitHubClient


@dataclass
class TicketAnalysis:
    """Result of ticket clarity analysis."""

    clarity_score: int  # 0-100
    is_implementable: bool
    missing_information: List[str]
    assumptions_needed: List[str]
    questions_for_author: List[str]
    acceptance_criteria: List[str]
    estimated_complexity: int  # 1-10 scale
    implementation_strategy: str
    risk_level: str  # low, medium, high


class TicketAnalyzer:
    """Analyzes tickets for clarity and completeness before implementation."""

    def __init__(self, agent: OpenAIAgent, github_client: GitHubClient):
        """
        Initialize ticket analyzer.

        Args:
            agent: OpenAI agent for analysis
            github_client: GitHub client for posting comments
        """
        self.agent = agent
        self.github_client = github_client

    def analyze_ticket(
        self,
        issue: Issue,
        context: str,
        min_clarity_threshold: int = 70
    ) -> TicketAnalysis:
        """
        Analyze ticket for clarity and completeness.

        Args:
            issue: GitHub issue to analyze
            context: Project context
            min_clarity_threshold: Minimum clarity score to proceed

        Returns:
            TicketAnalysis with assessment details
        """
        analysis_prompt = f"""Analyze this GitHub issue for implementation readiness.

# PROJECT CONTEXT
{context}

# ISSUE TO ANALYZE
**Title:** {issue.title}

**Description:**
{issue.body or 'No description provided'}

**Labels:** {', '.join([label.name for label in issue.labels])}

# YOUR TASK
Assess whether this issue is clear and complete enough to implement.

Respond with JSON:
{{
  "clarity_score": 0-100,
  "is_implementable": true/false,
  "missing_information": ["what information is missing or unclear"],
  "assumptions_needed": ["what assumptions must be made to proceed"],
  "questions_for_author": ["clarifying questions to ask issue author"],
  "acceptance_criteria": ["testable criteria to verify completion"],
  "estimated_complexity": 1-10,
  "implementation_strategy": "brief description of approach",
  "risk_level": "low/medium/high"
}}

Scoring guide:
- 90-100: Crystal clear, all details provided
- 70-89: Good, minor assumptions needed
- 50-69: Unclear, significant assumptions needed
- 0-49: Very unclear, cannot implement safely

Consider:
- Are requirements specific and measurable?
- Is the expected behavior clearly described?
- Are edge cases mentioned?
- Is there enough technical detail?
- Are there any ambiguities?
"""

        response = self.agent.send_message(analysis_prompt)
        analysis_data = self.agent.parse_json_response(response)

        if not analysis_data:
            # Fallback if parsing fails
            return TicketAnalysis(
                clarity_score=50,
                is_implementable=False,
                missing_information=["Unable to analyze ticket"],
                assumptions_needed=[],
                questions_for_author=[],
                acceptance_criteria=[],
                estimated_complexity=5,
                implementation_strategy="Unknown",
                risk_level="high"
            )

        return TicketAnalysis(
            clarity_score=analysis_data.get('clarity_score', 50),
            is_implementable=analysis_data.get('is_implementable', False),
            missing_information=analysis_data.get('missing_information', []),
            assumptions_needed=analysis_data.get('assumptions_needed', []),
            questions_for_author=analysis_data.get('questions_for_author', []),
            acceptance_criteria=analysis_data.get('acceptance_criteria', []),
            estimated_complexity=analysis_data.get('estimated_complexity', 5),
            implementation_strategy=analysis_data.get('implementation_strategy', ''),
            risk_level=analysis_data.get('risk_level', 'medium')
        )

    def request_clarification(
        self,
        issue: Issue,
        analysis: TicketAnalysis
    ) -> None:
        """
        Post clarification questions as a comment on the GitHub issue.

        Args:
            issue: GitHub issue to comment on
            analysis: Analysis containing questions
        """
        if not analysis.questions_for_author:
            return

        comment_body = f"""🤖 **Automated Analysis: Need Clarification**

I analyzed this issue and found it needs more information before implementation can begin.

**Clarity Score:** {analysis.clarity_score}/100

**Questions:**
"""
        for i, question in enumerate(analysis.questions_for_author, 1):
            comment_body += f"\n{i}. {question}"

        if analysis.missing_information:
            comment_body += "\n\n**Missing Information:**"
            for info in analysis.missing_information:
                comment_body += f"\n- {info}"

        comment_body += "\n\n*Once these details are provided, I can proceed with implementation.*"

        # Post comment
        issue.create_comment(comment_body)
        print(f"📝 Posted clarification request on issue #{issue.number}")

    def should_proceed(
        self,
        analysis: TicketAnalysis,
        min_clarity_threshold: int = 70,
        allow_assumptions: bool = True
    ) -> bool:
        """
        Determine if implementation should proceed based on analysis.

        Args:
            analysis: Ticket analysis
            min_clarity_threshold: Minimum acceptable clarity score
            allow_assumptions: Whether to proceed with documented assumptions

        Returns:
            True if should proceed, False otherwise
        """
        if analysis.clarity_score >= min_clarity_threshold:
            return True

        if allow_assumptions and analysis.clarity_score >= 50:
            # Can proceed with assumptions if they're reasonable
            if len(analysis.assumptions_needed) <= 3:
                return True

        return False

    def print_analysis_summary(self, analysis: TicketAnalysis) -> None:
        """
        Print formatted analysis summary.

        Args:
            analysis: Analysis to print
        """
        print("\n" + "=" * 70)
        print("🔍 TICKET ANALYSIS")
        print("=" * 70)
        print(f"Clarity Score: {analysis.clarity_score}/100")
        print(f"Implementable: {'✅ Yes' if analysis.is_implementable else '❌ No'}")
        print(f"Complexity: {analysis.estimated_complexity}/10")
        print(f"Risk Level: {analysis.risk_level.upper()}")

        if analysis.implementation_strategy:
            print(f"\nStrategy: {analysis.implementation_strategy}")

        if analysis.acceptance_criteria:
            print("\nAcceptance Criteria:")
            for criterion in analysis.acceptance_criteria:
                print(f"  ✓ {criterion}")

        if analysis.assumptions_needed:
            print("\n⚠️  Assumptions Required:")
            for assumption in analysis.assumptions_needed:
                print(f"  - {assumption}")

        if analysis.missing_information:
            print("\n❌ Missing Information:")
            for info in analysis.missing_information:
                print(f"  - {info}")

        if analysis.questions_for_author:
            print("\n❓ Questions for Author:")
            for question in analysis.questions_for_author:
                print(f"  - {question}")

        print("=" * 70)
