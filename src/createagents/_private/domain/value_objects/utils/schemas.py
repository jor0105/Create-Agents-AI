from __future__ import annotations

import inspect
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import docstring_parser
from pydantic import BaseModel, Field, create_model

from ..tools.injected import is_injected_arg


def _get_base_type(annotation: Any) -> Any:
    """Extract the base type from an Annotated type.

    Args:
        annotation: A type annotation, possibly Annotated.

    Returns:
        The base type without Annotated wrapper.
    """
    origin = get_origin(annotation)
    if origin is Annotated:
        args = get_args(annotation)
        return args[0] if args else Any
    return annotation


def _parse_google_docstring(func: Callable) -> Dict[str, str]:
    """Parse a Google-style docstring to extract parameter descriptions.

    Args:
        func: The function whose docstring should be parsed.

    Returns:
        A dictionary mapping parameter names to their descriptions.

    Example:
        ```python
        def example(name: str, age: int) -> str:
            '''Do something with name and age.'''
            pass

        descriptions = _parse_google_docstring(example)
        # Returns: {'name': ..., 'age': ...}
        ```
    """
    descriptions: Dict[str, str] = {}

    if not func.__doc__:
        return descriptions

    try:
        parsed = docstring_parser.parse(func.__doc__)
        for param in parsed.params:
            if param.arg_name and param.description:
                descriptions[param.arg_name] = param.description
    except Exception:
        # If parsing fails, return empty dict (expected for malformed docstrings)
        return descriptions

    return descriptions


def _get_short_description(func: Callable) -> str:
    """Extract the short description from a function's docstring.

    Args:
        func: The function whose docstring should be parsed.

    Returns:
        The short description (first line) from the docstring,
        or an empty string if no docstring exists.
    """
    if not func.__doc__:
        return ''

    try:
        parsed = docstring_parser.parse(func.__doc__)
        desc = parsed.short_description or ''
        return desc.strip()
    except Exception:
        # Fallback: get first non-empty line
        lines = func.__doc__.strip().split('\n')
        return lines[0].strip() if lines else ''


def _filter_injected_args(
    type_hints: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Separate regular arguments from injected arguments.

    Args:
        type_hints: Dictionary of parameter names to type hints.

    Returns:
        A tuple of (regular_args, injected_args) dictionaries.
    """
    regular_args: Dict[str, Any] = {}
    injected_args: Dict[str, Any] = {}

    for name, hint in type_hints.items():
        if name == 'return':
            continue
        if is_injected_arg(hint):
            injected_args[name] = hint
        else:
            regular_args[name] = hint

    return regular_args, injected_args


def _python_type_to_json_type(python_type: Any) -> str:
    """Convert a Python type to a JSON Schema type string.

    Args:
        python_type: A Python type annotation.

    Returns:
        The corresponding JSON Schema type string.
    """
    origin = get_origin(python_type)

    # Handle Union types (including Optional)
    if origin is Union:
        args = get_args(python_type)
        # Filter out NoneType for Optional
        non_none_args = [a for a in args if a is not type(None)]
        if non_none_args:
            return _python_type_to_json_type(non_none_args[0])
        return 'string'

    # Handle Literal types
    if origin is not None and str(origin).startswith('typing.Literal'):
        return 'string'

    # Handle list/array types
    if origin in (list, tuple, set, frozenset):
        return 'array'

    # Handle dict types
    if origin is dict:
        return 'object'

    # Direct type mappings
    type_mapping = {
        str: 'string',
        int: 'integer',
        float: 'number',
        bool: 'boolean',
        list: 'array',
        tuple: 'array',
        set: 'array',
        frozenset: 'array',
        dict: 'object',
        type(None): 'null',
    }

    return type_mapping.get(python_type, 'string')


def create_schema_from_function(
    func: Callable,
    model_name: str | None = None,
    *,
    parse_docstring: bool = True,
    filter_injected: bool = True,
) -> Type[BaseModel]:
    """Create a Pydantic model from a function's signature.

    This function analyzes a callable's signature and docstring to
    automatically generate a Pydantic BaseModel that can validate
    the function's input arguments.

    Args:
        func: The function to analyze.
        model_name: Optional name for the generated model. Defaults to
            `{function_name}Input`.
        parse_docstring: Whether to parse the docstring for parameter
            descriptions. Uses Google-style docstring format.
        filter_injected: Whether to filter out parameters marked with
            InjectedToolArg annotations.

    Returns:
        A dynamically created Pydantic BaseModel class.

    Example:
        ```python
        def search(query: str, max_results: int = 10) -> str:
            '''Search for information.'''
            pass

        SearchInput = create_schema_from_function(search)
        # SearchInput is now a Pydantic model with:
        # - query: str (required)
        # - max_results: int = 10 (optional with default)
        ```
    """
    if model_name is None:
        model_name = f'{func.__name__.title().replace("_", "")}Input'

    # Get type hints
    try:
        hints = get_type_hints(func, include_extras=True)
    except Exception:
        hints = {}

    # Get function signature for default values
    sig = inspect.signature(func)

    # Filter out injected args if requested
    if filter_injected:
        regular_hints, _ = _filter_injected_args(hints)
    else:
        regular_hints = {k: v for k, v in hints.items() if k != 'return'}

    # Parse docstring for descriptions
    descriptions: Dict[str, str] = {}
    if parse_docstring:
        descriptions = _parse_google_docstring(func)

    # Build field definitions for create_model
    field_definitions: Dict[str, Any] = {}

    for param_name, param in sig.parameters.items():
        # Skip *args, **kwargs, and self/cls
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if param_name in ('self', 'cls'):
            continue

        # Skip injected args
        if param_name not in regular_hints and param_name in hints:
            continue
        if param_name not in regular_hints and param_name not in hints:
            # Parameter without type hint - use Any
            type_hint = Any
        else:
            type_hint = regular_hints.get(param_name, Any)

        # Get base type (strip Annotated wrapper if present)
        base_type = _get_base_type(type_hint)

        # Get description from docstring
        description = descriptions.get(param_name, '')

        # Check if parameter has default
        if param.default is inspect.Parameter.empty:
            # Required field
            field_definitions[param_name] = (
                base_type,
                Field(description=description) if description else ...,
            )
        else:
            # Optional field with default
            field_definitions[param_name] = (
                base_type,
                Field(default=param.default, description=description),
            )

    # Create the model dynamically
    return create_model(model_name, **field_definitions)  # type: ignore[no-any-return]


def get_json_schema_from_function(
    func: Callable,
    *,
    parse_docstring: bool = True,
    filter_injected: bool = True,
) -> Dict[str, Any]:
    """Generate a JSON Schema from a function's signature.

    This is a convenience function that creates a Pydantic model and
    immediately converts it to a JSON Schema dictionary.

    Args:
        func: The function to analyze.
        parse_docstring: Whether to parse docstring for descriptions.
        filter_injected: Whether to filter InjectedToolArg parameters.

    Returns:
        A JSON Schema dictionary describing the function's parameters.
    """
    model = create_schema_from_function(
        func,
        parse_docstring=parse_docstring,
        filter_injected=filter_injected,
    )
    return model.model_json_schema()  # type: ignore[no-any-return]


__all__ = [
    'create_schema_from_function',
    'get_json_schema_from_function',
]
