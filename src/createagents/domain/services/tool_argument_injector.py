from typing import (
    Any,
    Dict,
    Optional,
    Annotated,
    get_args,
    get_origin,
    get_type_hints,
)
from ..interfaces import LoggerInterface
from ..value_objects import BaseTool
from ..value_objects.injected_args import (
    InjectedState,
    InjectedToolArg,
    InjectedToolCallId,
)


class ToolArgumentInjector:
    """Service responsible for injecting special arguments into tool calls.

    This service handles the logic of inspecting tool signatures and injecting
    values for parameters annotated with InjectedToolArg, InjectedToolCallId,
    and InjectedState.
    """

    def __init__(self, logger: LoggerInterface):
        """Initialize the injector with a logger.

        Args:
            logger: Logger instance for logging injection details.
        """
        self.__logger = logger

    def inject_args(
        self,
        tool: BaseTool,
        kwargs: Dict[str, Any],
        tool_call_id: Optional[str],
        agent_state: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Inject InjectedToolArg parameters into kwargs.

        This method inspects the tool's function signature (if available)
        and injects values for parameters annotated with InjectedToolArg
        markers.

        Args:
            tool: The tool being executed.
            kwargs: The original keyword arguments from the LLM.
            tool_call_id: Optional tool call ID to inject.
            agent_state: Optional agent state to inject.

        Returns:
            A new dict with injected arguments added.
        """
        result = kwargs.copy()

        # Get the function to inspect (for StructuredTool or class-based)
        func = None
        if hasattr(tool, 'func') and tool.func is not None:
            func = tool.func
        elif hasattr(tool, 'coroutine') and tool.coroutine is not None:
            func = tool.coroutine
        elif hasattr(tool, '_run'):
            func = tool._run
        elif hasattr(tool, 'execute'):
            func = tool.execute

        if func is None:
            return result

        try:
            hints = get_type_hints(func, include_extras=True)
        except Exception:
            # Can't get type hints, return original kwargs
            return result

        for param_name, hint in hints.items():
            if param_name == 'return':
                continue

            # Check if this is an Annotated type with InjectedToolArg
            if get_origin(hint) is Annotated:
                args = get_args(hint)
                for arg in args[1:]:  # Skip the base type
                    if isinstance(arg, InjectedToolCallId):
                        if tool_call_id is not None:
                            result[param_name] = tool_call_id
                            self.__logger.debug(
                                "Injected tool_call_id into '%s'", param_name
                            )
                        break
                    elif isinstance(arg, InjectedState):
                        if agent_state is not None:
                            result[param_name] = agent_state
                            self.__logger.debug(
                                "Injected agent_state into '%s'", param_name
                            )
                        break
                    elif isinstance(arg, InjectedToolArg):
                        # Generic injected arg - skip for now
                        self.__logger.debug(
                            "Found InjectedToolArg for '%s' but no value",
                            param_name,
                        )
                        break

        return result
