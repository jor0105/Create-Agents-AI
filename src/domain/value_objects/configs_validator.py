from typing import Set

from src.domain.exceptions.domain_exceptions import InvalidAgentConfigException


class SupportedConfigs:
    """
    Manages and validates supported configurations for AI agents.

    Responsibilities:
    - Define the supported configurations.
    - Validate the values of specific configurations.
    - Provide an interface for automatic validation.
    """

    __AVAILABLE_CONFIGS: Set[str] = {"temperature", "max_tokens", "top_p"}

    @classmethod
    def get_available_configs(cls) -> Set[str]:
        """
        Returns the set of supported configurations.

        Returns:
            A set containing the names of available configurations.
        """
        return cls.__AVAILABLE_CONFIGS.copy()

    @staticmethod
    def validate_temperature(value: float) -> None:
        """
        Validates the 'temperature' parameter.

        Args:
            value: The temperature value, which must be between 0.0 and 2.0.

        Raises:
            InvalidAgentConfigException: If the value is outside the allowed range.
        """
        if value is not None and not (0.0 <= value <= 2.0):
            raise InvalidAgentConfigException(
                "temperature", "must be a float between 0.0 and 2.0"
            )

    @staticmethod
    def validate_max_tokens(value: int) -> None:
        """
        Validates the 'max_tokens' parameter.

        Args:
            value: The max_tokens value, which must be an integer greater than zero.

        Raises:
            InvalidAgentConfigException: If the value is invalid.
        """
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise InvalidAgentConfigException(
                "max_tokens", "must be an integer greater than zero"
            )

    @staticmethod
    def validate_top_p(value: float) -> None:
        """
        Validates the 'top_p' parameter.

        Args:
            value: The top_p value, which must be between 0.0 and 1.0.

        Raises:
            InvalidAgentConfigException: If the value is outside the allowed range.
        """
        if value is not None and not (0.0 <= value <= 1.0):
            raise InvalidAgentConfigException(
                "top_p", "must be a float between 0.0 and 1.0"
            )

    @classmethod
    def validate_config(cls, key: str, value) -> None:
        """
        Validates a specific configuration based on its key.

        Args:
            key: The name of the configuration.
            value: The value of the configuration.

        Raises:
            InvalidAgentConfigException: If the validation fails.
        """
        validators = {
            "temperature": cls.validate_temperature,
            "max_tokens": cls.validate_max_tokens,
            "top_p": cls.validate_top_p,
        }
        validator = validators.get(key)
        if validator:
            validator(value)
