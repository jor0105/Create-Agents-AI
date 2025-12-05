from typing import Any, Optional, Set


class AgentException(Exception):
    """Base exception for agent-related errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class InvalidAgentConfigException(AgentException):
    """Exception raised when the agent configuration is invalid."""

    def __init__(self, field: str, reason: str):
        message = f"Invalid configuration in field '{field}': {reason}"
        super().__init__(message)


class InvalidModelException(AgentException):
    """Exception raised when the specified AI model is not supported."""

    def __init__(self, model: str):
        message = f"Unsupported AI model: '{model}'"
        super().__init__(message)


class ChatException(Exception):
    """Base exception for errors during communication with AI."""

    def __init__(
        self, message: str, original_error: Optional[Exception] = None
    ):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class RateLimitError(ChatException):
    """Exception raised when API rate limit is exceeded (HTTP 429).

    This exception captures the retry_after value from the API response,
    allowing intelligent retry strategies.

    Attributes:
        retry_after: Seconds to wait before retrying (from Retry-After header).
        provider: The API provider that returned the rate limit error.
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.retry_after = retry_after
        self.provider = provider


class APITimeoutError(ChatException):
    """Exception raised when API request times out.

    Attributes:
        timeout_seconds: The timeout value that was exceeded.
        provider: The API provider that timed out.
    """

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.timeout_seconds = timeout_seconds
        self.provider = provider


class AdapterNotFoundException(ChatException):
    """Exception raised when the chat adapter is not found."""

    def __init__(self, adapter_name: str):
        message = f"Adapter not found: '{adapter_name}'"
        super().__init__(message)


class InvalidProviderException(AgentException):
    """Exception raised when the provider is not supported."""

    def __init__(self, provider: str, available_providers: Set[str]):
        providers = ', '.join(sorted(available_providers))
        message = f"Provider '{provider}' is not available. Available providers: {providers}"
        super().__init__(message)


class UnsupportedConfigException(AgentException):
    """Exception raised when a configuration is not supported."""

    def __init__(self, config_key: str, available_configs: Set[str]):
        configs = ', '.join(sorted(available_configs))
        message = f"Configuration '{config_key}' is not supported. Valid options: {configs}"
        super().__init__(message)


class InvalidConfigTypeException(AgentException):
    """Exception raised when the configuration type is invalid."""

    def __init__(self, config_key: str, value_type: type):
        message = f"Configuration '{config_key}' has invalid type: {value_type.__name__}"
        super().__init__(message)


class InvalidBaseToolException(AgentException):
    """Exception raised when a provided tool does not match the BaseTool interface."""

    def __init__(self, tool: Any):
        message = (
            f"Tool '{tool}' is invalid. It must inherit from BaseTool and "
            "implement the attributes 'name' (string type), 'description' "
            "(string type), and the 'execute' method."
        )
        super().__init__(message)


class FileReadException(AgentException):
    """Exception raised when file reading operation fails."""

    def __init__(self, file_path: str, reason: str):
        message = f"Failed to read file '{file_path}': {reason}"
        super().__init__(message)
