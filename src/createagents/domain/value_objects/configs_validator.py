from typing import Dict, Optional, Set, Union

from ..exceptions import InvalidAgentConfigException


class SupportedConfigs:
    """
    Manages and validates supported configurations for AI agents.

    Responsibilities:
    - Define the supported configurations.
    - Validate the values of specific configurations.
    - Provide an interface for automatic validation.
    """

    __AVAILABLE_CONFIGS: Set[str] = {
        "temperature",
        "max_tokens",
        "top_p",
        "think",
        "top_k",
    }

    @classmethod
    def get_available_configs(cls) -> Set[str]:
        """
        Returns the set of supported configurations.

        Returns:
            A set containing the names of available configurations.
        """
        return cls.__AVAILABLE_CONFIGS.copy()

    @staticmethod
    def validate_temperature(value: Optional[float]) -> None:
        """
        Validates the 'temperature' parameter.

        Args:
            value: The temperature value, which must be between 0.0 and 2.0.

        Raises:
            InvalidAgentConfigException: If the value is outside the allowed range or of the wrong type.
        """
        if value is not None:
            if not isinstance(value, (float, int)) or not (0.0 <= float(value) <= 2.0):
                raise InvalidAgentConfigException(
                    "temperature", "must be a float between 0.0 and 2.0"
                )

    @staticmethod
    def validate_max_tokens(value: Optional[int]) -> None:
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
    def validate_top_p(value: Optional[float]) -> None:
        """
        Validates the 'top_p' parameter.

        Args:
            value: The top_p value, which must be between 0.0 and 1.0.

        Raises:
            InvalidAgentConfigException: If the value is outside the allowed range or of the wrong type.
        """
        if value is not None:
            if not isinstance(value, (float, int)) or not (0.0 <= float(value) <= 1.0):
                raise InvalidAgentConfigException(
                    "top_p", "must be a float between 0.0 and 1.0"
                )

    @staticmethod
    def validate_think(value: Optional[Union[bool, Dict[str, str]]]) -> None:
        """
        Validates the 'think' parameter.

        The `think` option can be provided in two shapes depending on the provider:
        - Ollama provider: a boolean (True/False)
        - OpenAI provider: a dict with string keys and string values

        Args:
            value: The think value to validate (or None).

        Raises:
            InvalidAgentConfigException: If the value does not match the allowed shapes.
        """
        if value is None:
            return

        # boolean is allowed
        if isinstance(value, bool):
            return

        if isinstance(value, dict):
            if not all(
                isinstance(k, str) and isinstance(v, str) for k, v in value.items()
            ):
                raise InvalidAgentConfigException(
                    "think",
                    "must be a boolean (for Ollama Provider) or a dict[str, str] (for OpenAI Provider)",
                )
            return

        raise InvalidAgentConfigException(
            "think",
            "must be a boolean (for Ollama Provider) or a dict[str, str] (for OpenAI Provider)",
        )

    @staticmethod
    def validate_top_k(value: Optional[int]) -> None:
        """
        Validates the 'top_k' parameter.

        Args:
            value: The top_k value, which must be an integer greater than zero.

        Raises:
            InvalidAgentConfigException: If the value is invalid.
        """
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise InvalidAgentConfigException(
                "top_k", "must be an integer greater than zero"
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
            "think": cls.validate_think,
            "temperature": cls.validate_temperature,
            "max_tokens": cls.validate_max_tokens,
            "top_p": cls.validate_top_p,
            "top_k": cls.validate_top_k,
        }
        validator = validators.get(key)
        if validator:
            validator(value)
