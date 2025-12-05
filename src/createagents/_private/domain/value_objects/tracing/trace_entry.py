"""Trace entry value object for representing logged events."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class TraceEntry:
    """Represents a single trace entry/span.

    This is the unit of persistence for the trace store.
    Each entry corresponds to a logged event in a trace.

    Designed for compatibility with:
    - OpenTelemetry (trace_id, run_id as span_id, parent_run_id)
    - LangSmith (run_type, inputs, outputs, tokens)
    - Datadog APM (operation, duration_ms, error fields)
    """

    # Required fields
    timestamp: datetime
    trace_id: str
    run_id: str
    run_type: str
    operation: str
    event: str

    # Hierarchy
    parent_run_id: Optional[str] = None
    session_id: Optional[str] = None

    # Context
    agent_name: Optional[str] = None
    model: Optional[str] = None

    # Status
    status: Optional[str] = None

    # Data payloads
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None

    # Timing
    duration_ms: Optional[float] = None

    # Error tracking (for OpenTelemetry/Datadog compatibility)
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    error_stack: Optional[str] = None

    # Token/Cost tracking (for LangSmith/LLM observability)
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None

    # Extensible metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for serialization."""
        result: Dict[str, Any] = {
            'timestamp': self.timestamp.isoformat(),
            'trace_id': self.trace_id,
            'run_id': self.run_id,
            'run_type': self.run_type,
            'operation': self.operation,
            'event': self.event,
        }

        # Optional fields - only include if set
        if self.parent_run_id:
            result['parent_run_id'] = self.parent_run_id
        if self.session_id:
            result['session_id'] = self.session_id
        if self.agent_name:
            result['agent_name'] = self.agent_name
        if self.model:
            result['model'] = self.model
        if self.status:
            result['status'] = self.status
        if self.inputs:
            result['inputs'] = self.inputs
        if self.outputs:
            result['outputs'] = self.outputs
        if self.data:
            result['data'] = self.data
        if self.duration_ms is not None:
            result['duration_ms'] = self.duration_ms

        # Error tracking
        if self.error_message:
            result['error_message'] = self.error_message
        if self.error_type:
            result['error_type'] = self.error_type
        if self.error_stack:
            result['error_stack'] = self.error_stack

        # Token/Cost tracking
        if self.input_tokens is not None:
            result['input_tokens'] = self.input_tokens
        if self.output_tokens is not None:
            result['output_tokens'] = self.output_tokens
        if self.total_tokens is not None:
            result['total_tokens'] = self.total_tokens
        if self.cost_usd is not None:
            result['cost_usd'] = self.cost_usd

        if self.metadata:
            result['metadata'] = self.metadata

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraceEntry':
        """Create entry from dictionary."""
        timestamp_value = data.get('timestamp')
        if isinstance(timestamp_value, str):
            parsed_timestamp = datetime.fromisoformat(timestamp_value)
        elif isinstance(timestamp_value, datetime):
            parsed_timestamp = timestamp_value
        else:
            parsed_timestamp = datetime.now(timezone.utc)

        return cls(
            timestamp=parsed_timestamp,
            trace_id=data['trace_id'],
            run_id=data['run_id'],
            run_type=data['run_type'],
            operation=data['operation'],
            event=data['event'],
            parent_run_id=data.get('parent_run_id'),
            session_id=data.get('session_id'),
            agent_name=data.get('agent_name'),
            model=data.get('model'),
            status=data.get('status'),
            inputs=data.get('inputs'),
            outputs=data.get('outputs'),
            data=data.get('data'),
            duration_ms=data.get('duration_ms'),
            error_message=data.get('error_message'),
            error_type=data.get('error_type'),
            error_stack=data.get('error_stack'),
            input_tokens=data.get('input_tokens'),
            output_tokens=data.get('output_tokens'),
            total_tokens=data.get('total_tokens'),
            cost_usd=data.get('cost_usd'),
            metadata=data.get('metadata', {}),
        )


@dataclass
class TraceSummary:
    """Summary of a complete trace.

    Provides aggregated metrics including token usage and costs.
    """

    trace_id: str
    session_id: Optional[str]
    agent_name: Optional[str]
    model: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    status: str
    run_count: int
    tool_calls_count: int

    # Token/Cost aggregates
    total_tokens: Optional[int] = None
    total_cost_usd: Optional[float] = None

    # Error tracking
    error_count: int = 0

    entries: List[TraceEntry] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Check if trace has been completed."""
        return self.end_time is not None


__all__ = ['TraceEntry', 'TraceSummary']
