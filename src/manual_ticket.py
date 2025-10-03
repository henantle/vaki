"""Manual ticket support for non-GitHub issue sources."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ManualTicket:
    """Represents a manual ticket from external sources (Slack, email, Jira, etc.)."""

    number: int  # Auto-generated sequential number
    title: str
    body: str
    source: str  # e.g., "slack", "email", "jira", "manual"
    created_at: datetime
    raw_text: str  # Original pasted text

    @property
    def labels(self):
        """Mock labels property for compatibility with GitHub Issue."""
        return []

    @property
    def html_url(self):
        """Mock URL for display."""
        return f"manual-ticket-{self.number}"

    @classmethod
    def from_text(cls, raw_text: str, source: str = "manual") -> "ManualTicket":
        """
        Create a ManualTicket from raw text.

        Attempts to parse:
        - Title (first line or line starting with #, Title:, Subject:)
        - Body (remaining text)

        Args:
            raw_text: The pasted ticket text
            source: Source of the ticket (slack, email, jira, manual)

        Returns:
            ManualTicket instance
        """
        lines = raw_text.strip().split('\n')

        # Try to extract title
        title = ""
        body_lines = []

        # Look for title patterns
        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Check for common title patterns
            if not title and line_stripped:
                # Pattern: "Title: something"
                if line_stripped.lower().startswith(('title:', 'subject:', '# ')):
                    title = line_stripped.split(':', 1)[-1].strip().lstrip('#').strip()
                    body_lines = lines[i+1:]
                    break
                # Pattern: First non-empty line as title
                elif i == 0 or (i < 3 and not body_lines):
                    title = line_stripped
                    body_lines = lines[i+1:]
                    break

        # Fallback: use first line as title, rest as body
        if not title:
            title = lines[0].strip() if lines else "Manual Ticket"
            body_lines = lines[1:] if len(lines) > 1 else []

        # Construct body
        body = '\n'.join(body_lines).strip()

        # Generate sequential number (timestamp-based)
        ticket_number = int(datetime.now().timestamp() * 1000) % 100000

        return cls(
            number=ticket_number,
            title=title[:200],  # Limit title length
            body=body,
            source=source,
            created_at=datetime.now(),
            raw_text=raw_text
        )

    def to_pr_reference(self) -> str:
        """
        Generate PR body reference text.

        Returns:
            Formatted text for PR body
        """
        return f"""📋 **Manual Ticket #{self.number}** (from {self.source})

**Original Request:**
```
{self.raw_text[:500]}{'...' if len(self.raw_text) > 500 else ''}
```
"""


def parse_manual_ticket(text: str, source: str = "manual") -> ManualTicket:
    """
    Parse manual ticket text into a ManualTicket object.

    Args:
        text: Raw ticket text (pasted from any source)
        source: Source identifier (slack, email, jira, manual)

    Returns:
        ManualTicket instance

    Examples:
        >>> text = "Add dark mode\\nUsers want dark mode for the app"
        >>> ticket = parse_manual_ticket(text)
        >>> ticket.title
        'Add dark mode'
        >>> ticket.body
        'Users want dark mode for the app'

        >>> text = "Title: Fix login bug\\nDescription: Users can't login"
        >>> ticket = parse_manual_ticket(text, source="slack")
        >>> ticket.source
        'slack'
    """
    return ManualTicket.from_text(text, source)
