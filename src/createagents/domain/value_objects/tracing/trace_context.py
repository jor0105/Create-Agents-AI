from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid


class RunType(str, Enum):
    """Types of runs/spans in the trace hierarchy.

    Based on LangSmith run types for compatibility.
    """

    CHAT = 'chat'
    LLM = 'llm'
    TOOL = 'tool'
    CHAIN = 'chain'
    RETRIEVER = 'retriever'
    EMBEDDING = 'embedding'
    AGENT = 'agent'
    PARSER = 'parser'


@dataclass(frozen=True)
class TraceContext:
    """Immutable value object representing a trace context.

    This class follows Clean Architecture principles as a pure domain
    value object with no external dependencies.

    Attributes:
        trace_id: Unique identifier for the entire trace/conversation.
        run_id: Unique identifier for this specific operation/span.
        parent_run_id: ID of the parent operation (None for root).
        run_type: Type of operation (chat, tool, llm, etc.).
        operation: Human-readable operation name.
        session_id: Optional session ID for grouping related traces.
        agent_name: Name of the agent executing the operation.
        model: Model being used (if applicable).
        metadata: Additional context metadata.
        start_time: When this run started.
    """

    trace_id: str
    run_id: str
    run_type: RunType
    operation: str
    parent_run_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_name: Optional[str] = None
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def create_root(
        cls,
        run_type: RunType,
        operation: str = 'root',
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> 'TraceContext':
        """Create a root trace context (no parent).

        Args:
            run_type: Type of the root operation.
            operation: Human-readable operation name.
            session_id: Optional session ID for grouping traces.
            agent_name: Name of the agent.
            model: Model being used.
            metadata: Additional metadata.
            trace_id: Optional custom trace ID (auto-generated if None).

        Returns:
            A new root TraceContext.
        """
        generated_trace_id = trace_id or f'trace-{uuid.uuid4().hex[:12]}'
        return cls(
            trace_id=generated_trace_id,
            run_id=f'run-{uuid.uuid4().hex[:12]}',
            parent_run_id=None,
            run_type=run_type,
            operation=operation,
            session_id=session_id,
            agent_name=agent_name,
            model=model,
            metadata=metadata or {},
        )

    def create_child(
        self,
        run_type: RunType,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> 'TraceContext':
        """Create a child trace context with this context as parent.

        Args:
            run_type: Type of the child operation.
            operation: Human-readable operation name.
            metadata: Additional metadata for the child.

        Returns:
            A new TraceContext with this context as parent.
        """
        child_metadata = {**self.metadata, **(metadata or {})}
        return TraceContext(
            trace_id=self.trace_id,
            run_id=f'run-{uuid.uuid4().hex[:12]}',
            parent_run_id=self.run_id,
            run_type=run_type,
            operation=operation,
            session_id=self.session_id,
            agent_name=self.agent_name,
            model=self.model,
            metadata=child_metadata,
        )

    def with_metadata(self, **kwargs: Any) -> 'TraceContext':
        """Create a new context with additional metadata.

        Since TraceContext is frozen, this returns a new instance.

        Args:
            **kwargs: Metadata key-value pairs to add.

        Returns:
            A new TraceContext with merged metadata.
        """
        new_metadata = {**self.metadata, **kwargs}
        return TraceContext(
            trace_id=self.trace_id,
            run_id=self.run_id,
            parent_run_id=self.parent_run_id,
            run_type=self.run_type,
            operation=self.operation,
            session_id=self.session_id,
            agent_name=self.agent_name,
            model=self.model,
            metadata=new_metadata,
            start_time=self.start_time,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization.

        Returns:
            Dictionary representation of the trace context.
        """
        return {
            'trace_id': self.trace_id,
            'run_id': self.run_id,
            'parent_run_id': self.parent_run_id,
            'run_type': self.run_type.value,
            'operation': self.operation,
            'session_id': self.session_id,
            'agent_name': self.agent_name,
            'model': self.model,
            'metadata': self.metadata,
            'start_time': self.start_time.isoformat(),
        }

    def to_log_extra(self) -> Dict[str, Any]:
        """Convert to extra dict for Python logging.

        Returns:
            Dictionary suitable for logging extra parameter.
        """
        return {
            'trace_id': self.trace_id,
            'run_id': self.run_id,
            'parent_run_id': self.parent_run_id,
            'run_type': self.run_type.value,
            'operation': self.operation,
            'session_id': self.session_id,
            'agent_name': self.agent_name,
            'model': self.model,
        }

    @property
    def elapsed_ms(self) -> float:
        """Calculate elapsed time since start in milliseconds.

        Returns:
            Elapsed time in milliseconds.
        """
        now = datetime.now(timezone.utc)
        delta = now - self.start_time
        return delta.total_seconds() * 1000

    @property
    def is_root(self) -> bool:
        """Check if this is a root context (no parent)."""
        return self.parent_run_id is None

    def __str__(self) -> str:
        """Human-readable string representation."""
        parent_info = (
            f' (parent: {self.parent_run_id})' if self.parent_run_id else ''
        )
        return f'[{self.run_type.value}:{self.run_id}] {self.operation}{parent_info}'
