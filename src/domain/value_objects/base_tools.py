from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Base class for all tools that the agent can use.

    This class defines the contract that all tools must follow.
    Tools are capabilities that the AI agent can invoke to perform
    specific tasks (e.g., web search, calculations, API calls).

    Attributes:
        name (str): Unique identifier for the tool (e.g., 'web_search').
        description (str): Clear description of what the tool does and when to use it.
                          This description is used by the LLM to decide when to invoke the tool.

    Subclasses must:
        1. Set class attributes `name` and `description`
        2. Implement the `execute` method with the tool's logic

    Example:
        ```python
        class CalculatorTool(BaseTool):
            name = "calculator"
            description = "Performs mathematical calculations"

            def execute(self, expression: str) -> str:
                return str(eval(expression))
        ```
    """

    name: str = "base_tool"
    description: str = "Base tool description (should be overridden)"

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the tool's main functionality.

        This method must be implemented by all subclasses.

        Args:
            *args: Positional arguments specific to the tool.
            **kwargs: Keyword arguments specific to the tool.

        Returns:
            The result of the tool execution (typically a string).
        """
        pass

    def get_schema_for_llm(self) -> dict:
        """Return a schema describing the tool for LLM prompts.

        The default implementation returns the tool name and description.
        Subclasses can extend this with a `parameters` key if needed to
        describe expected inputs.

        Returns:
            A dictionary with 'name' and 'description' keys.
        """
        return {
            "name": self.name,
            "description": self.description,
        }
