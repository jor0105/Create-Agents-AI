from typing import Dict, Optional

from ...domain import BaseTool


class AvailableTools:
    """Registry of available tools for the AI Agent.

    This class maintains a catalog of tool instances that can be used
    by agents. Tools are registered with string keys for easy lookup.

    Tools are separated into two categories:
    - System Tools: Built-in tools provided by the AI Agent framework
    - Agent Tools: Tools added to specific agents by users

    Heavy tools (like ReadLocalFileTool) are loaded lazily to improve
    import performance and avoid loading unnecessary dependencies.
    """

    # System tools: built-in tools provided by the framework
    __SYSTEM_TOOLS: Dict[str, BaseTool] = {}

    # Agent tools: tools added by users to specific agents
    __AGENT_TOOLS: Dict[str, BaseTool] = {}

    # Cache for lazily loaded system tools
    __LAZY_SYSTEM_TOOLS: Dict[str, Optional[BaseTool]] = {}

    @classmethod
    def _ensure_system_tools_loaded(cls):
        """Ensure system tools are loaded lazily to avoid circular imports."""
        if not cls.__SYSTEM_TOOLS:
            from ..adapters import CurrentDateTool  # pylint: disable=import-outside-toplevel

            cls.__SYSTEM_TOOLS['currentdate'] = CurrentDateTool()

    @classmethod
    def get_system_tools(cls) -> Dict[str, str]:
        """Return a dict of system tool descriptions.

        System tools are built-in tools provided by the framework.

        Returns:
            Dict[str, str]: A dictionary mapping system tool names to descriptions.
        """
        cls._ensure_system_tools_loaded()

        # Try to load lazy system tools on first access
        if 'readlocalfile' not in cls.__LAZY_SYSTEM_TOOLS:
            cls.__try_load_read_local_file_tool()

        # Get all system tool instances
        all_system_tool_instances = cls.__get_all_system_tool_instances()

        # Convert to name: description mapping
        return {
            tool_name: tool.description
            for tool_name, tool in all_system_tool_instances.items()
        }

    @classmethod
    def get_system_tool_names(cls) -> set:
        """Return a set of system tool names (registry keys).

        This returns the keys used to register system tools, which may differ
        from the tool's internal 'name' attribute.

        Returns:
            set: A set of system tool names as registered in the system.
        """
        cls._ensure_system_tools_loaded()

        # Try to load lazy system tools on first access
        if 'readlocalfile' not in cls.__LAZY_SYSTEM_TOOLS:
            cls.__try_load_read_local_file_tool()

        # Get all system tool names (keys in the dictionaries)
        system_tool_names = set(cls.__SYSTEM_TOOLS.keys())
        system_tool_names.update(
            k for k, v in cls.__LAZY_SYSTEM_TOOLS.items() if v is not None
        )

        return system_tool_names

    @classmethod
    def get_agent_tools(cls) -> Dict[str, str]:
        """Return a dict of agent tool descriptions.

        Agent tools are tools added by users to specific agents.

        Returns:
            Dict[str, str]: A dictionary mapping agent tool names to descriptions.
        """
        # Convert to name: description mapping
        return {
            tool_name: tool.description
            for tool_name, tool in cls.__AGENT_TOOLS.items()
        }

    @classmethod
    def add_agent_tool(cls, tool_name: str, tool: BaseTool) -> None:
        """Add a new agent tool to the registry.

        This method allows dynamic registration of agent tools at runtime.
        Useful for adding custom tools created by users.

        Args:
            tool_name: The unique identifier for the tool (case-insensitive).
            tool: The BaseTool instance to register.

        Raises:
            ValueError: If a tool with the same name already exists.
        """
        tool_key = tool_name.lower()

        # Check if tool already exists (in both system and agent tools)
        if tool_key in cls.__AGENT_TOOLS:
            raise ValueError(
                f"Agent tool '{tool_name}' is already registered. "
                f'Use a different name or remove the existing tool first.'
            )

        # Also check system tools to avoid conflicts
        cls._ensure_system_tools_loaded()
        all_system_tools = cls.__get_all_system_tool_instances()
        if tool_key in all_system_tools:
            raise ValueError(
                f"'{tool_name}' conflicts with a system tool. "
                f'Please use a different name for your custom agent tool.'
            )

        cls.__AGENT_TOOLS[tool_key] = tool

    @classmethod
    def clear_agent_tools(cls) -> None:
        """Clear all agent tools from the registry.

        This is useful for testing or resetting the agent tools state.
        System tools are not affected by this operation.
        """
        cls.__AGENT_TOOLS.clear()

    @classmethod
    def get_all_available_tools(cls) -> Dict[str, str]:
        """Return a dict of ALL available tool descriptions (system + agent).

        This method returns a user-friendly dictionary mapping tool names
        to their descriptions. This includes both system tools and agent tools.

        Returns:
            Dict[str, str]: A dictionary mapping tool names to descriptions.
        """
        all_tools = {}
        all_tools.update(cls.get_system_tools())
        all_tools.update(cls.get_agent_tools())
        return all_tools

    @classmethod
    def __get_all_system_tool_instances(cls) -> Dict[str, BaseTool]:
        """Return a dict of all available system tool instances (internal method).

        This internal method returns the actual system tool objects, which are needed
        for execution by the domain layer.

        Returns:
            A dict of supported system tool instances.
        """
        cls._ensure_system_tools_loaded()

        # Try to load lazy system tools on first access
        if 'readlocalfile' not in cls.__LAZY_SYSTEM_TOOLS:
            cls.__try_load_read_local_file_tool()

        # Combine eager and lazy system tools
        all_system_tools = cls.__SYSTEM_TOOLS.copy()
        all_system_tools.update(
            {k: v for k, v in cls.__LAZY_SYSTEM_TOOLS.items() if v is not None}
        )

        return all_system_tools

    @classmethod
    def __get_all_tool_instances(cls) -> Dict[str, BaseTool]:
        """Return a dict of all available tool instances (internal method).

        This internal method returns the actual tool objects, which are needed
        for execution by the domain layer. Includes both system and agent tools.

        Returns:
            A dict of supported tool instances.
        """
        cls._ensure_system_tools_loaded()

        # Try to load lazy tools on first access
        if 'readlocalfile' not in cls.__LAZY_SYSTEM_TOOLS:
            cls.__try_load_read_local_file_tool()

        # Combine eager and lazy tools (both system and agent)
        all_tools = cls.__SYSTEM_TOOLS.copy()
        all_tools.update(
            {k: v for k, v in cls.__LAZY_SYSTEM_TOOLS.items() if v is not None}
        )
        all_tools.update(cls.__AGENT_TOOLS)

        return all_tools

    @classmethod
    def get_tool_instance(cls, tool_name: str) -> Optional[BaseTool]:
        """Get a specific tool instance by name.

        This method is used internally to retrieve actual tool objects
        for execution. It's needed by the application layer when validating
        and using tools.

        Args:
            tool_name: The name of the tool to retrieve (case-insensitive).

        Returns:
            The BaseTool instance if found, None otherwise.
        """
        all_tools = cls.__get_all_tool_instances()
        return all_tools.get(tool_name.lower())

    @classmethod
    def get_all_tool_instances(cls) -> Dict[str, BaseTool]:
        """Get all available tool instances.

        This method returns the actual tool objects for use by the domain layer.
        It's primarily used internally for tool execution.

        Returns:
            A dict of all available tool instances.
        """
        return cls.__get_all_tool_instances()

    @classmethod
    def __try_load_read_local_file_tool(cls) -> None:
        """Attempt to load ReadLocalFileTool with its heavy dependencies.

        If the optional dependencies are not installed, logs a warning
        and marks the tool as unavailable.
        """
        # Only load once - check if already loaded
        if 'readlocalfile' in cls.__LAZY_SYSTEM_TOOLS:
            return

        try:
            from ..adapters import ReadLocalFileTool  # pylint: disable=import-outside-toplevel
            from .logging_config import create_logger  # pylint: disable=import-outside-toplevel

            logger = create_logger(__name__)
            cls.__LAZY_SYSTEM_TOOLS['readlocalfile'] = ReadLocalFileTool()
            logger.debug('ReadLocalFileTool loaded successfully')
        except ImportError as e:
            from .logging_config import create_logger  # pylint: disable=import-outside-toplevel

            logger = create_logger(__name__)
            logger.warning(
                'ReadLocalFileTool not available - optional dependencies missing. '
                'Install with: pip install ai-agent[file-tools]\n'
                'Error: %s',
                e,
            )
            cls.__LAZY_SYSTEM_TOOLS['readlocalfile'] = None
        except RuntimeError as e:
            from .logging_config import create_logger  # pylint: disable=import-outside-toplevel

            logger = create_logger(__name__)
            logger.warning('ReadLocalFileTool not available: %s', e)
            cls.__LAZY_SYSTEM_TOOLS['readlocalfile'] = None
        except Exception as e:
            from .logging_config import create_logger  # pylint: disable=import-outside-toplevel

            logger = create_logger(__name__)
            logger.error('Failed to load ReadLocalFileTool: %s', e)
            cls.__LAZY_SYSTEM_TOOLS['readlocalfile'] = None
