"""Interface for trace persistence.

This module defines the contract for storing and retrieving
trace data. Implementations can store traces in memory, files,
databases, or external services.

The data classes TraceEntry and TraceSummary are imported from
domain/value_objects/tracing for proper Clean Architecture layering.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

# Import value objects from proper domain location
from ..value_objects.tracing import TraceEntry, TraceSummary

# Re-export for backward compatibility
__all__ = [
    'ITraceStore',
    'TraceEntry',
    'TraceSummary',
]


class ITraceStore(ABC):
    """Interface for trace persistence.

    This abstract class defines the contract for storing and retrieving
    trace data. Implementations can store traces in memory, files,
    databases, or external services.

    Follows Clean Architecture principles:
    - Defined in domain layer as an interface
    - Concrete implementations in infra layer
    """

    @abstractmethod
    def save_entry(self, entry: TraceEntry) -> None:
        """Save a single trace entry.

        Args:
            entry: The trace entry to persist.
        """

    @abstractmethod
    def get_trace(self, trace_id: str) -> Optional[TraceSummary]:
        """Get all entries for a trace.

        Args:
            trace_id: The trace identifier.

        Returns:
            TraceSummary with all entries, or None if not found.
        """

    @abstractmethod
    def list_traces(
        self,
        limit: int = 20,
        session_id: Optional[str] = None,
        since: Optional[datetime] = None,
        agent_name: Optional[str] = None,
    ) -> List[TraceSummary]:
        """List traces with optional filters.

        Args:
            limit: Maximum number of traces to return.
            session_id: Filter by session ID.
            since: Only include traces after this time.
            agent_name: Filter by agent name.

        Returns:
            List of trace summaries.
        """

    @abstractmethod
    def export_traces(
        self,
        trace_ids: Optional[List[str]] = None,
        format: str = 'jsonl',
    ) -> str:
        """Export traces to string format.

        Args:
            trace_ids: Specific trace IDs to export (None = all).
            format: Export format ('json' or 'jsonl').

        Returns:
            Exported trace data as string.
        """

    @abstractmethod
    def clear_traces(
        self,
        older_than: Optional[datetime] = None,
        trace_ids: Optional[List[str]] = None,
    ) -> int:
        """Clear/delete traces.

        Args:
            older_than: Delete traces older than this time.
            trace_ids: Specific trace IDs to delete.

        Returns:
            Number of traces deleted.
        """

    @abstractmethod
    def get_trace_count(self) -> int:
        """Get total number of stored traces.

        Returns:
            Count of unique trace IDs.
        """
