"""Security utilities for token masking and sanitization."""

import re
from typing import Optional


class TokenSanitizer:
    """Sanitize sensitive tokens from logs and error messages."""

    def __init__(self):
        self.tokens = []

    def register_token(self, token: str):
        """
        Register a sensitive token to be masked in output.

        Args:
            token: Token to mask (e.g., GitHub token, API key)
        """
        if token and len(token) > 0:
            self.tokens.append(token)

    def sanitize(self, text: str) -> str:
        """
        Remove all registered tokens from text.

        Args:
            text: Text that may contain sensitive tokens

        Returns:
            Sanitized text with tokens masked
        """
        if not text:
            return text

        sanitized = text

        # Mask registered tokens
        for token in self.tokens:
            if token in sanitized:
                # Show first 4 chars for identification, mask the rest
                if len(token) > 8:
                    masked = f"{token[:4]}{'*' * (len(token) - 4)}"
                else:
                    masked = "***TOKEN***"
                sanitized = sanitized.replace(token, masked)

        # Mask common patterns even if not registered
        # GitHub tokens: ghp_*, gho_*, etc.
        sanitized = re.sub(r'(ghp_|gho_|ghu_|ghs_|ghr_)[a-zA-Z0-9]{36}', r'\1****', sanitized)

        # OpenAI API keys: sk-*
        sanitized = re.sub(r'sk-[a-zA-Z0-9]{48}', 'sk-****', sanitized)

        # Generic API key patterns in URLs
        sanitized = re.sub(r'(token=|api_key=|apikey=)[^&\s]+', r'\1****', sanitized)

        # Authorization headers
        sanitized = re.sub(r'(Authorization:\s*Bearer\s+)[^\s]+', r'\1****', sanitized)

        return sanitized

    def sanitize_url(self, url: str) -> str:
        """
        Sanitize URLs that may contain tokens.

        Args:
            url: URL that may contain embedded credentials

        Returns:
            Sanitized URL
        """
        if not url:
            return url

        # Replace tokens in git URLs: https://token@github.com/...
        url = re.sub(r'https://[^@]+@github\.com/', 'https://***@github.com/', url)

        # Replace tokens in query parameters
        url = re.sub(r'([?&])(token|api_key|apikey)=[^&]+', r'\1\2=****', url)

        return url

    def sanitize_command(self, command: str) -> str:
        """
        Sanitize shell commands that may contain tokens.

        Args:
            command: Command string

        Returns:
            Sanitized command
        """
        return self.sanitize(command)


# Global sanitizer instance
_sanitizer = TokenSanitizer()


def register_token(token: str):
    """Register a sensitive token globally."""
    _sanitizer.register_token(token)


def sanitize(text: str) -> str:
    """Sanitize text using global sanitizer."""
    return _sanitizer.sanitize(text)


def sanitize_url(url: str) -> str:
    """Sanitize URL using global sanitizer."""
    return _sanitizer.sanitize_url(url)


def sanitize_command(command: str) -> str:
    """Sanitize command using global sanitizer."""
    return _sanitizer.sanitize_command(command)
