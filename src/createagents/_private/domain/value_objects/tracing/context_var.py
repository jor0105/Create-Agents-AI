from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from .trace_context import TraceContext
    from ...interfaces.tracing import ITraceStore

# Context variables for trace propagation
# These variables hold the current trace context and trace store
# for the current execution flow (e.g. inside a tool execution)
_current_trace_context: ContextVar[Optional['TraceContext']] = ContextVar(
    'current_trace_context', default=None
)
_current_trace_store: ContextVar[Optional['ITraceStore']] = ContextVar(
    'current_trace_store', default=None
)

# Type alias for the token tuple
TokenPair = Tuple[
    Token[Optional['TraceContext']],
    Token[Optional['ITraceStore']],
]


def set_trace_context(
    ctx: 'TraceContext', store: Optional['ITraceStore'] = None
) -> TokenPair:
    """Set current trace context (called by framework).

    Args:
        ctx: The trace context to set.
        store: The trace store to set (optional).

    Returns:
        A tuple of tokens to be used with reset_trace_context.
    """
    token_ctx = _current_trace_context.set(ctx)
    token_store = _current_trace_store.set(store)
    return (token_ctx, token_store)


def reset_trace_context(tokens: TokenPair) -> None:
    """Reset trace context (called by framework).

    Args:
        tokens: The tokens returned by set_trace_context.
    """
    token_ctx, token_store = tokens
    _current_trace_context.reset(token_ctx)
    _current_trace_store.reset(token_store)


def get_current_trace_context() -> Optional['TraceContext']:
    """Get current trace context (public API).

    Returns:
        The current TraceContext or None if not set.
    """
    return _current_trace_context.get()


def get_current_trace_store() -> Optional['ITraceStore']:
    """Get current trace store (public API).

    Returns:
        The current ITraceStore or None if not set.
    """
    return _current_trace_store.get()
