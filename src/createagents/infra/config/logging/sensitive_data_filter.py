import re
from functools import lru_cache
from typing import Dict, Pattern


class SensitiveDataFilter:
    """
    A filter to remove sensitive data from logs.

    This filter protects against the leakage of:
    - Credentials (API keys, tokens, passwords)
    - Personal data (emails, CPF, phone numbers)
    - Financial data (credit cards)
    - Secrets and keys

    IMPORTANT: The order of the patterns is significant.
    More specific patterns should be placed first to prevent
    generic patterns from capturing data incorrectly.

    Current order:
    1. Cloud/AI Provider keys (OpenAI, AWS, Google, Anthropic, HF, GitHub)
    2. Private Keys (PEM headers)
    3. JWT tokens (most specific)
    4. API keys (generic label-based)
    5. Bearer tokens
    6. Secrets
    7. Auth headers
    8. URIs with passwords (DBs, URLs)
    9. Passwords (most generic)
    9. Personal data (LGPD/GDPR)
    10. Financial data
    11. Private IPs
    """

    DEFAULT_CACHE_SIZE = 1000
    DEFAULT_VISIBLE_CHARS = 4

    _PATTERNS: Dict[str, Pattern] = {
        # Specific Provider Keys (High Priority)
        'openai_key': re.compile(r'\bsk-(?:proj-)?[a-zA-Z0-9\-_]{20,}\b'),
        'anthropic_key': re.compile(r'\bsk-ant-[a-zA-Z0-9\-_]{20,}\b'),
        'google_key': re.compile(r'\bAIza[0-9A-Za-z\-_]{35}\b'),
        'aws_access_key': re.compile(r'\b(AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\b'),
        'github_token': re.compile(
            r'\b(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36}\b'
        ),
        'huggingface_token': re.compile(r'\bhf_[a-zA-Z0-9]{34}\b'),
        'private_key': re.compile(r'-----BEGIN[ A-Z0-9_-]+PRIVATE KEY-----'),
        # Generic Patterns
        'jwt_token': re.compile(
            r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'
        ),
        'api_key': re.compile(
            r'(api[_-]?key[\s:="\']*)[\w\-]{6,}', re.IGNORECASE
        ),
        'bearer_token': re.compile(r'(bearer[\s]+)[\w\-._]+', re.IGNORECASE),
        'secret': re.compile(
            r'(secret|secret_key)[\s:="\']*([\w\-]{8,})', re.IGNORECASE
        ),
        'auth_header': re.compile(
            r'(authorization[\s:]+)(basic|bearer)[\s]+[\w\-._=]+',
            re.IGNORECASE,
        ),
        'url_with_password': re.compile(
            r'([a-zA-Z][a-zA-Z0-9+.-]*://[^:@\s]+):([^@\s]+)@', re.IGNORECASE
        ),
        'password': re.compile(
            r'(password|senha|pwd|pass)[\s:="\'\[]*([^\s,\]"\'}@]{3,})',
            re.IGNORECASE,
        ),
        'email': re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ),
        'cnpj': re.compile(r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b'),
        'cpf': re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'),
        'rg': re.compile(r'\b\d{1,2}\.?\d{3}\.?\d{3}-?[0-9Xx]\b'),
        'phone_br': re.compile(
            r'\b(?:\+55[\s]?)?\(?[1-9]{2}\)?[\s]?9[\s]?\d{4}-?\d{4}\b'
        ),
        'credit_card': re.compile(
            r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
        ),
        'cvv': re.compile(
            r'\b(cvv|cvc|security[\s]?code)[\s:="\']*([\d]{3,4})\b',
            re.IGNORECASE,
        ),
        'ipv4': re.compile(
            r'\b(?:10|127|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b'
        ),
    }

    @classmethod
    @lru_cache(maxsize=DEFAULT_CACHE_SIZE)
    def _filter_cached(cls, text: str) -> str:
        """
        Removes or masks sensitive data from text (cached version).
        Uses an LRU cache for improved performance and automatic management.

        Args:
            text: The text to be filtered.

        Returns:
            The text with sensitive data replaced by placeholders.
        """
        filtered_text = text

        for pattern_name, pattern in cls._PATTERNS.items():
            if pattern_name == 'password':
                filtered_text = pattern.sub(
                    r'\1[PASSWORD_REDACTED]', filtered_text
                )
            elif pattern_name == 'secret':
                filtered_text = pattern.sub(
                    r'\1[SECRET_REDACTED]', filtered_text
                )
            elif pattern_name == 'cvv':
                filtered_text = pattern.sub(r'\1[CVV_REDACTED]', filtered_text)
            elif pattern_name == 'url_with_password':
                filtered_text = pattern.sub(
                    r'\1:[CREDENTIALS_REDACTED]@', filtered_text
                )
            elif pattern_name == 'auth_header':
                filtered_text = pattern.sub(
                    r'\1\2 [TOKEN_REDACTED]', filtered_text
                )
            else:
                filtered_text = pattern.sub(
                    f'[{pattern_name.upper()}_REDACTED]', filtered_text
                )

        return filtered_text

    @classmethod
    def filter(cls, text: str) -> str:
        """
        Removes or masks sensitive data from a given text.

        Args:
            text: The text to be filtered.

        Returns:
            The text with sensitive data replaced by placeholders.

        Example:
            >>> text = "API Key: abc123xyz, email: user@example.com"
            >>> SensitiveDataFilter.filter(text)
            'API Key: [API_KEY_REDACTED], email: [EMAIL_REDACTED]'
        """
        if not text:
            return text

        return cls._filter_cached(text)

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the LRU cache of replacements."""
        cls._filter_cached.cache_clear()
