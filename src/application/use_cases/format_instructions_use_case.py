from typing import List, Optional

from src.domain import BaseTool
from src.infra.config.logging_config import LoggingConfig


class FormatInstructionsUseCase:
    """Use case for formatting agent instructions with tool descriptions.

    This use case applies different formatting strategies based on the provider:
    - OpenAI: Uses native function calling, so tool descriptions are NOT added to prompt
    - Ollama: Doesn't have native function calling, so tool descriptions ARE added to prompt

    This follows the Open/Closed Principle by being open for extension (new providers)
    but closed for modification (existing logic is preserved).
    """

    def __init__(self):
        """Initialize the FormatInstructionsUseCase with logging."""
        self.__logger = LoggingConfig.get_logger(__name__)

    def execute(
        self,
        instructions: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None,
        provider: Optional[str] = None,
    ) -> Optional[str]:
        """Format instructions based on provider capabilities.

        Args:
            instructions: The base instructions for the agent.
            tools: Optional list of tools available to the agent.
            provider: The AI provider (e.g., "openai", "ollama").
                     If None, defaults to adding tool descriptions.

        Returns:
            Formatted instructions, or None if no instructions or tools provided.
        """
        self.__logger.debug(
            f"Formatting instructions - Provider: {provider}, "
            f"Tools: {len(tools) if tools else 0}, "
            f"Instructions length: {len(instructions) if instructions else 0}"
        )

        if not tools and not instructions:
            self.__logger.debug("No tools or instructions provided, returning None")
            return None

        # OpenAI has native function calling, so we don't add tools to prompt
        # The tools are passed separately via the API
        if provider and provider.lower() == "openai":
            self.__logger.debug(
                "Provider is OpenAI - tools will be passed via API, not in prompt"
            )
            return instructions

        # For Ollama and other providers without native function calling,
        # we add tool descriptions to the system prompt
        self.__logger.debug(
            "Provider requires tools in prompt - formatting tool descriptions"
        )

        prompt_part = ""
        if tools:
            prompt_part = "Você pode usar as seguintes ferramentas:\n\n"
            for tool in tools:
                schema = tool.get_schema()
                prompt_part += "<tool>\n"
                prompt_part += f"  <name>{schema['name']}</name>\n"
                prompt_part += f"  <description>{schema['description']}</description>\n"
                prompt_part += "</tool>\n\n"

            self.__logger.debug(f"Added {len(tools)} tool description(s) to prompt")

        if not instructions:
            self.__logger.debug(
                "No base instructions, returning only tool descriptions"
            )
            return prompt_part if prompt_part else None

        if prompt_part:
            formatted = instructions + "\n\n" + prompt_part
            self.__logger.debug(
                f"Combined instructions and tool descriptions - Total length: {len(formatted)} chars"
            )
            return formatted

        self.__logger.debug("Returning original instructions (no tools to add)")
        return instructions
