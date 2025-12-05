from datetime import datetime
from enum import Enum
from functools import lru_cache
from time import perf_counter
from typing import Final, Literal, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field, field_validator

from .....domain import BaseTool
from .....domain.interfaces import LoggerInterface
from .....domain.value_objects.tools.response import ToolResponse
from .....utils import TextSanitizer
from ....config import create_logger


ActionType = Literal[
    'date', 'time', 'datetime', 'timestamp', 'date_with_weekday', 'iso_week'
]

_TOOL_NAME: Final[str] = 'currentdate'
_TOOL_VERSION: Final[str] = '2.0.0'


@lru_cache(maxsize=64)
def _get_zoneinfo(tz: str) -> ZoneInfo:
    """Cache timezone objects for performance.

    Args:
        tz: IANA timezone identifier.

    Returns:
        Cached ZoneInfo instance.
    """
    return ZoneInfo(tz.strip())


class DateAction(str, Enum):
    """Available actions for date/time retrieval."""

    DATE = 'date'
    TIME = 'time'
    DATETIME = 'datetime'
    TIMESTAMP = 'timestamp'
    DATE_WITH_WEEKDAY = 'date_with_weekday'
    ISO_WEEK = 'iso_week'


class CurrentDateInput(BaseModel):
    """Input schema for CurrentDateTool.

    Validates and documents the expected inputs with comprehensive
    descriptions for AI understanding.
    """

    action: Literal[
        'date',
        'time',
        'datetime',
        'timestamp',
        'date_with_weekday',
        'iso_week',
    ] = Field(
        default='datetime',
        description=(
            'Information to return:\n'
            "- 'date': ISO date (YYYY-MM-DD)\n"
            "- 'time': Time (HH:MM:SS)\n"
            "- 'datetime': Full ISO datetime with timezone (default)\n"
            "- 'timestamp': Unix timestamp (seconds)\n"
            "- 'date_with_weekday': Full date with weekday name\n"
            "- 'iso_week': ISO week number and year (YYYY-Www)"
        ),
    )
    tz: str = Field(
        default='UTC',
        description=(
            'IANA timezone identifier. Common examples:\n'
            "- 'UTC' (Coordinated Universal Time)\n"
            "- 'America/New_York' (US Eastern)\n"
            "- 'America/Los_Angeles' (US Pacific)\n"
            "- 'America/Sao_Paulo' (Brazil)\n"
            "- 'Europe/London', 'Europe/Paris'\n"
            "- 'Asia/Tokyo', 'Asia/Shanghai'"
        ),
    )

    @field_validator('action', mode='before')
    @classmethod
    def normalize_action(cls, v):
        """Convert common aliases to valid action values."""
        if isinstance(v, str):
            v_lower = v.lower().strip()
            aliases = {
                'now': 'datetime',
                'current': 'datetime',
                'get': 'datetime',
                'get_time': 'time',
                'get_date': 'date',
            }
            return aliases.get(v_lower, v_lower)
        return v


class CurrentDateTool(BaseTool):
    """Fast, secure tool for current date/time in any timezone.

    Features:
    - Zero external I/O (no network/filesystem)
    - Cached timezone resolution for performance
    - Multiple output formats optimized for different use cases
    - Sanitized output safe for all downstream processing
    - Structured responses for reliable AI parsing

    Performance:
    - Sub-millisecond execution
    - LRU cache for repeated timezone lookups
    - Minimal memory footprint
    """

    name: str = _TOOL_NAME
    description: str = (
        'Get current date/time in any timezone. '
        'Use for questions about current time, date, day of week, '
        'or timestamp conversions. Returns formatted, ready-to-use values.'
    )
    args_schema = CurrentDateInput

    _ALLOWED_ACTIONS: Final[frozenset] = frozenset(
        {
            'date',
            'time',
            'datetime',
            'timestamp',
            'date_with_weekday',
            'iso_week',
        }
    )

    def __init__(self, logger: Optional[LoggerInterface] = None) -> None:
        """Initialize with optional logger."""
        self._logger = logger or create_logger(__name__)

    def execute(self, action: ActionType, tz: str = 'UTC') -> str:  # type: ignore[override]
        """Execute date/time retrieval.

        Args:
            action: The type of information to retrieve.
            tz: IANA timezone identifier.

        Returns:
            Formatted date/time string or error message.
        """
        start_time = perf_counter()
        self._logger.debug(
            'CurrentDateTool executing: action=%s, tz=%s', action, tz
        )

        if action not in self._ALLOWED_ACTIONS:
            return self._error_response(
                f"Invalid action '{action}'. Valid options: {sorted(self._ALLOWED_ACTIONS)}",
                'INVALID_ACTION',
                start_time,
            )

        try:
            zone = _get_zoneinfo(tz)
        except ZoneInfoNotFoundError:
            return self._error_response(
                f"Unknown timezone '{tz}'. Use IANA format (e.g., 'America/New_York', 'UTC')",
                'INVALID_TIMEZONE',
                start_time,
            )

        try:
            now = datetime.now(zone)
            result = self._format_datetime(now, action)
            sanitized = TextSanitizer.sanitize(result)

            elapsed_ms = (perf_counter() - start_time) * 1000
            self._logger.debug(
                'CurrentDateTool completed in %.2fms: %s',
                elapsed_ms,
                sanitized,
            )

            return ToolResponse.success(
                data=sanitized,
                message=f'{action} retrieved for timezone {tz}',
                tool_name=_TOOL_NAME,
                execution_time_ms=elapsed_ms,
            ).format()

        except (ValueError, TypeError, OverflowError) as exc:
            self._logger.error(
                'DateTime processing error: %s', exc, exc_info=True
            )
            return self._error_response(
                f'DateTime error: {exc}',
                'PROCESSING_ERROR',
                start_time,
            )

    def _format_datetime(self, dt: datetime, action: ActionType) -> str:
        """Format datetime according to requested action.

        Args:
            dt: The datetime object to format.
            action: The formatting action.

        Returns:
            Formatted string.
        """
        formatters: dict[str, object] = {
            'date': lambda d: d.date().isoformat(),
            'time': lambda d: d.strftime('%H:%M:%S'),
            'datetime': lambda d: d.isoformat(),
            'timestamp': lambda d: str(int(d.timestamp())),
            'date_with_weekday': lambda d: f'{d.strftime("%A")}, {d.strftime("%d de %B de %Y")}',
            'iso_week': lambda d: f'{d.isocalendar().year}-W{d.isocalendar().week:02d}',
        }
        result: str = str(formatters[action](dt))  # type: ignore[operator]
        return result

    def _error_response(
        self, message: str, code: str, start_time: float
    ) -> str:
        """Generate formatted error response.

        Args:
            message: Error description.
            code: Error code for categorization.
            start_time: Execution start time for timing.

        Returns:
            Formatted error string.
        """
        elapsed_ms = (perf_counter() - start_time) * 1000
        self._logger.warning('CurrentDateTool error [%s]: %s', code, message)
        return ToolResponse.error(
            message=message,
            tool_name=_TOOL_NAME,
            error_code=code,
            execution_time_ms=elapsed_ms,
        ).format()


__all__ = ['CurrentDateTool']
