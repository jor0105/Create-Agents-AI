from datetime import datetime, timezone
from typing import Any

from ....domain.interfaces import LoggerInterface
from ....domain.value_objects.tracing.context_var import (
    get_current_trace_context,
    get_current_trace_store,
)


class ContextAwareLogger(LoggerInterface):
    """Logger that automatically enriches logs with trace context.

    This class wraps a base logger and adds trace context information
    to logs when a trace is active. If no trace is active, it behaves
    exactly like the base logger.

    Attributes:
        _name: Logger name for trace entries.
        _base: The underlying logger to delegate to.
    """

    __slots__ = ('_name', '_base')

    def __init__(self, name: str, base_logger: LoggerInterface):
        """Initialize with a name and base logger.

        Args:
            name: Logger name (usually __name__).
            base_logger: The underlying LoggerInterface to delegate to.
        """
        self._name = name
        self._base = base_logger

    def _enrich_and_log(
        self,
        level: str,
        message: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Enrich log with context and delegate to base logger.

        Args:
            level: Log level name ('debug', 'info', etc.).
            message: Log message (may contain % formatting).
            *args: Arguments for % formatting.
            **kwargs: Additional kwargs including 'extra'.
        """
        ctx = get_current_trace_context()
        store = get_current_trace_store()
        extra = kwargs.pop('extra', {}) or {}

        if ctx:
            extra.update(
                {
                    'trace_id': ctx.trace_id,
                    'run_id': ctx.run_id,
                    'logger_name': self._name,
                }
            )

        kwargs['extra'] = extra

        log_method = getattr(self._base, level)
        log_method(message, *args, **kwargs)

        if ctx and store:
            try:
                formatted_msg = message % args if args else message
            except (TypeError, ValueError):
                formatted_msg = str(message)

            store.save(
                {
                    'event': 'tool.log',
                    'trace_id': ctx.trace_id,
                    'run_id': ctx.run_id,
                    'parent_run_id': ctx.parent_run_id,
                    'level': level.upper(),
                    'message': formatted_msg,
                    'logger_name': self._name,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'operation': ctx.operation,
                    'run_type': ctx.run_type.value,
                }
            )

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self._enrich_and_log('debug', message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self._enrich_and_log('info', message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self._enrich_and_log('warning', message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._enrich_and_log('error', message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._enrich_and_log('critical', message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error with exception info."""
        kwargs.setdefault('exc_info', True)
        self._enrich_and_log('error', message, *args, **kwargs)
