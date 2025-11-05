from typing import List, Optional

from src.domain import BaseTool


class FormatInstructionsUseCase:
    """Use case for formatting agent instructions with tool descriptions.

    This use case applies different formatting strategies based on the provider:
    - OpenAI: Uses native function calling, so tool descriptions are NOT added to prompt
    - Ollama: Doesn't have native function calling, so tool descriptions ARE added to prompt

    This follows the Open/Closed Principle by being open for extension (new providers)
    but closed for modification (existing logic is preserved).
    """

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
        if not tools and not instructions:
            return None

        # OpenAI has native function calling, so we don't add tools to prompt
        # The tools are passed separately via the API
        if provider and provider.lower() == "openai":
            return instructions

        # For Ollama and other providers without native function calling,
        # we add tool descriptions to the system prompt
        prompt_part = ""
        if tools:
            prompt_part = "Você pode usar as seguintes ferramentas:\n\n"
            for tool in tools:
                schema = tool.get_schema_for_llm()
                prompt_part += "<tool>\n"
                prompt_part += f"  <name>{schema['name']}</name>\n"
                prompt_part += f"  <description>{schema['description']}</description>\n"
                prompt_part += "</tool>\n\n"

        if not instructions:
            return prompt_part if prompt_part else None

        if prompt_part:
            return instructions + "\n\n" + prompt_part

        return instructions
