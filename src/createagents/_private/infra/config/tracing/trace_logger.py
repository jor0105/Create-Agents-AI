import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING

from ....domain.interfaces import ITraceLogger, LoggerInterface
from ....domain.value_objects import TraceContext

if TYPE_CHECKING:
    from ....domain.interfaces.tracing import ITraceStore


class TraceLogger(ITraceLogger):
    """Concrete implementation of trace-aware logging.

    This class wraps a standard LoggerInterface and adds trace context
    to all log entries, enabling structured observability.

    The output format is designed to be:
    - Human-readable in console
    - Machine-parseable (JSON in 'extra' fields)
    - Compatible with log aggregation systems
    """

    # Preview length for truncated content
    PREVIEW_LENGTH = 500
    # Maximum length for full content in DEBUG level
    MAX_CONTENT_LENGTH = 10000

    def __init__(
        self,
        logger: LoggerInterface,
        json_output: bool = False,
        trace_store: Optional['ITraceStore'] = None,
    ):
        """Initialize the trace logger.

        Args:
            logger: Underlying logger implementation.
            json_output: If True, output fully structured JSON logs.
            trace_store: Optional trace store for persistence.
        """
        self._logger = logger
        self._json_output = json_output
        self._trace_store = trace_store

    def start_trace(
        self,
        trace_context: TraceContext,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log the start of a trace/operation."""
        # Merge data and inputs (inputs takes precedence)
        merged_data = {**(data or {}), **(inputs or {})}

        extra = self._build_extra(
            trace_context=trace_context,
            event='trace.start',
            status='started',
            data=merged_data if merged_data else None,
        )

        log_message = message or f'Starting {trace_context.operation}'

        if self._json_output:
            self._logger.info(self._to_json(log_message, extra))
        else:
            self._logger.info(
                '▶️ [%s] %s | trace_id=%s run_id=%s',
                trace_context.run_type.value.upper(),
                log_message,
                trace_context.trace_id,
                trace_context.run_id,
                extra=extra,
            )

        # Log input data at DEBUG level
        if merged_data:
            self._logger.debug(
                '[%s] Input data: %s',
                trace_context.run_id,
                self._truncate(json.dumps(merged_data, default=str)),
                extra=extra,
            )

        self._persist_entry(
            trace_context=trace_context,
            event='trace.start',
            status='started',
            inputs=merged_data if merged_data else None,
        )

    def end_trace(
        self,
        trace_context: TraceContext,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        status: str = 'success',
    ) -> None:
        """Log the end of a trace/operation."""
        # Merge data and outputs (outputs takes precedence)
        merged_data = {**(data or {}), **(outputs or {})}

        duration_ms = trace_context.elapsed_ms

        extra = self._build_extra(
            trace_context=trace_context,
            event='trace.end',
            status=status,
            data=merged_data if merged_data else None,
            duration_ms=duration_ms,
        )

        log_method = (
            self._logger.info if status == 'success' else self._logger.error
        )
        status_emoji = '✅' if status == 'success' else '❌'
        log_message = message or f'Completed {trace_context.operation}'

        if self._json_output:
            log_method(self._to_json(log_message, extra))
        else:
            log_method(
                '%s [%s] %s | trace_id=%s run_id=%s duration=%.2fms status=%s',
                status_emoji,
                trace_context.run_type.value.upper(),
                log_message,
                trace_context.trace_id,
                trace_context.run_id,
                duration_ms,
                status,
                extra=extra,
            )

        # Log output data at DEBUG level
        if merged_data:
            self._logger.debug(
                '[%s] Output data: %s',
                trace_context.run_id,
                self._truncate(json.dumps(merged_data, default=str)),
                extra=extra,
            )

        self._persist_entry(
            trace_context=trace_context,
            event='trace.end',
            status=status,
            outputs=merged_data if merged_data else None,
            duration_ms=duration_ms,
        )

    def log_event(
        self,
        trace_context: TraceContext,
        event: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        level: str = 'info',
    ) -> None:
        """Log an event within a trace."""
        extra = self._build_extra(
            trace_context=trace_context,
            event=event,
            data=data,
        )

        log_method = getattr(self._logger, level, self._logger.info)

        if self._json_output:
            log_method(self._to_json(message, extra))
        else:
            log_method(
                '[%s] %s | trace_id=%s event=%s',
                trace_context.run_id,
                message,
                trace_context.trace_id,
                event,
                extra=extra,
            )

        self._persist_entry(
            trace_context=trace_context,
            event=event,
            data=data,
        )

    def log_tool_call(
        self,
        trace_context: TraceContext,
        tool_name: str,
        tool_call_id: str,
        inputs: Dict[str, Any],
    ) -> None:
        """Log a tool call with inputs."""
        extra = self._build_extra(
            trace_context=trace_context,
            event='tool.call',
            data={
                'tool_name': tool_name,
                'tool_call_id': tool_call_id,
                'inputs': inputs,
            },
        )

        if self._json_output:
            self._logger.info(
                self._to_json(f"Calling tool '{tool_name}'", extra)
            )
        else:
            self._logger.info(
                '[%s] 🔧 Calling tool: %s | tool_call_id=%s',
                trace_context.run_id,
                tool_name,
                tool_call_id,
                extra=extra,
            )

        # Log full inputs at DEBUG level
        self._logger.debug(
            '[%s] Tool inputs for %s: %s',
            trace_context.run_id,
            tool_name,
            json.dumps(inputs, default=str),
            extra=extra,
        )

        self._persist_entry(
            trace_context=trace_context,
            event='tool.call',
            inputs=inputs,
            data={
                'tool_name': tool_name,
                'tool_call_id': tool_call_id,
            },
        )

    def log_tool_result(
        self,
        trace_context: TraceContext,
        tool_name: str,
        tool_call_id: str,
        result: Any,
        duration_ms: float,
        success: bool = True,
    ) -> None:
        """Log a tool execution result."""
        result_str = str(result)
        result_preview = self._truncate(result_str, 200)

        extra = self._build_extra(
            trace_context=trace_context,
            event='tool.result',
            status='success' if success else 'error',
            data={
                'tool_name': tool_name,
                'tool_call_id': tool_call_id,
                'result_preview': result_preview,
                'result_length': len(result_str),
            },
            duration_ms=duration_ms,
        )

        status_icon = '✅' if success else '❌'
        status_text = 'success' if success else 'error'

        log_method = self._logger.info if success else self._logger.error

        if self._json_output:
            log_method(
                self._to_json(
                    f"Tool '{tool_name}' completed ({status_text})", extra
                )
            )
        else:
            log_method(
                '[%s] %s Tool %s completed [%s] | duration=%.2fms result=%s',
                trace_context.run_id,
                status_icon,
                tool_name,
                status_text,
                duration_ms,
                result_preview,
                extra=extra,
            )

        # Log full result at DEBUG level
        self._logger.debug(
            '[%s] Tool %s full result: %s',
            trace_context.run_id,
            tool_name,
            self._truncate(result_str, self.MAX_CONTENT_LENGTH),
            extra=extra,
        )

        self._persist_entry(
            trace_context=trace_context,
            event='tool.result',
            status=status_text,
            outputs={'result': result_str},
            duration_ms=duration_ms,
            data={
                'tool_name': tool_name,
                'tool_call_id': tool_call_id,
            },
        )

    def log_llm_request(
        self,
        trace_context: TraceContext,
        model: str,
        messages_count: int,
        tools_available: Optional[int] = None,
    ) -> None:
        """Log an LLM API request."""
        extra = self._build_extra(
            trace_context=trace_context,
            event='llm.request',
            data={
                'model': model,
                'messages_count': messages_count,
                'tools_available': tools_available,
            },
        )

        tools_info = f' tools={tools_available}' if tools_available else ''

        if self._json_output:
            self._logger.info(self._to_json(f'LLM request to {model}', extra))
        else:
            self._logger.info(
                '[%s] 🤖 LLM request | model=%s messages=%d%s',
                trace_context.run_id,
                model,
                messages_count,
                tools_info,
                extra=extra,
            )

        self._persist_entry(
            trace_context=trace_context,
            event='llm.request',
            inputs={
                'messages_count': messages_count,
                'tools_available': tools_available,
            },
            data={'model': model},
        )

    def log_llm_response(
        self,
        trace_context: TraceContext,
        model: str,
        response_preview: str,
        has_tool_calls: bool,
        tool_calls_count: int = 0,
        tokens_used: Optional[int] = None,
        duration_ms: Optional[float] = None,
    ) -> None:
        """Log an LLM API response."""
        extra = self._build_extra(
            trace_context=trace_context,
            event='llm.response',
            data={
                'model': model,
                'response_preview': self._truncate(response_preview, 200),
                'has_tool_calls': has_tool_calls,
                'tool_calls_count': tool_calls_count,
                'tokens_used': tokens_used,
            },
            duration_ms=duration_ms,
        )

        tool_info = (
            f' tool_calls={tool_calls_count}'
            if has_tool_calls
            else ' (text response)'
        )
        tokens_info = f' tokens={tokens_used}' if tokens_used else ''
        duration_info = f' duration={duration_ms:.2f}ms' if duration_ms else ''

        if self._json_output:
            self._logger.info(
                self._to_json(f'LLM response from {model}', extra)
            )
        else:
            self._logger.info(
                '[%s] 🤖 LLM response | model=%s%s%s%s',
                trace_context.run_id,
                model,
                tool_info,
                tokens_info,
                duration_info,
                extra=extra,
            )

        # Log response preview at DEBUG level
        self._logger.debug(
            '[%s] LLM response content: %s',
            trace_context.run_id,
            self._truncate(response_preview, self.PREVIEW_LENGTH),
            extra=extra,
        )

        self._persist_entry(
            trace_context=trace_context,
            event='llm.response',
            outputs={
                'response_preview': response_preview,
                'has_tool_calls': has_tool_calls,
                'tool_calls_count': tool_calls_count,
            },
            duration_ms=duration_ms,
            data={
                'model': model,
                'tokens_used': tokens_used,
            },
        )

    def _build_extra(
        self,
        trace_context: TraceContext,
        event: str,
        status: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Build the extra dict for logging."""
        extra = {
            **trace_context.to_log_extra(),
            'event': event,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        if status:
            extra['status'] = status
        if duration_ms is not None:
            extra['duration_ms'] = round(duration_ms, 2)
        if data:
            extra['data'] = data

        return extra

    def _to_json(self, message: str, extra: Dict[str, Any]) -> str:
        """Convert log entry to JSON string."""
        log_entry = {
            'message': message,
            **extra,
        }
        return json.dumps(log_entry, default=str, ensure_ascii=False)

    def _truncate(self, text: str, max_length: Optional[int] = None) -> str:
        """Truncate text to max length with ellipsis."""
        length = max_length or self.PREVIEW_LENGTH
        if len(text) <= length:
            return text
        return text[:length] + '...'

    def _persist_entry(
        self,
        trace_context: TraceContext,
        event: str,
        status: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
    ) -> None:
        """Persist a trace entry to the store if configured."""
        if not self._trace_store:
            return

        from ....domain.value_objects.tracing import TraceEntry  # pylint: disable=import-outside-toplevel

        entry = TraceEntry(
            timestamp=datetime.now(timezone.utc),
            trace_id=trace_context.trace_id,
            run_id=trace_context.run_id,
            parent_run_id=trace_context.parent_run_id,
            run_type=trace_context.run_type.value,
            operation=trace_context.operation,
            event=event,
            status=status,
            session_id=trace_context.session_id,
            agent_name=trace_context.agent_name,
            model=trace_context.model,
            inputs=inputs,
            outputs=outputs,
            data=data,
            duration_ms=duration_ms,
            metadata=trace_context.metadata,
        )
        self._trace_store.save_entry(entry)

    @property
    def trace_store(self) -> Optional['ITraceStore']:
        """Get the trace store instance."""
        return self._trace_store

    @trace_store.setter
    def trace_store(self, store: Optional['ITraceStore']) -> None:
        """Set the trace store instance."""
        self._trace_store = store


def create_trace_logger(
    name: str,
    json_output: bool = False,
    trace_store: Optional['ITraceStore'] = None,
) -> TraceLogger:
    """Factory function to create a TraceLogger.

    Args:
        name: Logger name (usually __name__).
        json_output: If True, output structured JSON logs.
        trace_store: Optional trace store for persistence.
                    Pass any ITraceStore implementation (FileTraceStore,
                    InMemoryTraceStore, or custom).

    Returns:
        A configured TraceLogger instance.

    Example:
        >>> from createagents import FileTraceStore
        >>> trace_logger = create_trace_logger(__name__, trace_store=FileTraceStore())
        >>> ctx = TraceContext.create_root(RunType.CHAT, "chat")
        >>> trace_logger.start_trace(ctx, "Starting chat")
    """
    from ..logging.logging_config import create_logger

    base_logger = create_logger(name)

    return TraceLogger(
        logger=base_logger, json_output=json_output, trace_store=trace_store
    )
