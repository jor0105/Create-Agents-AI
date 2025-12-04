from datetime import datetime
from enum import Enum
from functools import lru_cache
from typing import Literal, Optional

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field

from .....domain import BaseTool
from .....domain.interfaces import LoggerInterface
from .....utils import TextSanitizer
from ....config import create_logger

# Type alias for better type checking
ActionType = Literal[
    'date', 'time', 'datetime', 'timestamp', 'date_with_weekday'
]


@lru_cache(maxsize=32)
def _get_zoneinfo(tz: str) -> ZoneInfo:
    """Get a ZoneInfo object for the given timezone string.

    Args:
        tz: The timezone string.

    Returns:
        ZoneInfo: The ZoneInfo object.
    """
    return ZoneInfo(tz.strip())


class DateAction(str, Enum):
    """Available actions for the CurrentDateTool."""

    DATE = 'date'
    TIME = 'time'
    DATETIME = 'datetime'
    TIMESTAMP = 'timestamp'
    DATE_WITH_WEEKDAY = 'date_with_weekday'


class CurrentDateInput(BaseModel):
    """Input schema for CurrentDateTool using Pydantic validation.

    This schema validates and documents the inputs expected by the tool.
    """

    action: Literal[
        'date', 'time', 'datetime', 'timestamp', 'date_with_weekday'
    ] = Field(
        ...,
        description=(
            "What information to return: 'date' (just the date), "
            "'time' (just the time), 'datetime' (both), "
            "'timestamp' (unix seconds), or 'date_with_weekday' "
            '(full date with weekday)'
        ),
    )
    tz: str = Field(
        ...,
        description=(
            "IANA timezone identifier. Examples: 'UTC', "
            "'America/New_York' (New York), 'America/Los_Angeles' "
            "(California), 'America/Chicago' (Chicago), "
            "'America/Sao_Paulo' (Brazil), 'Europe/Lisbon', etc."
        ),
    )


class CurrentDateTool(BaseTool):
    """Secure tool that provides the current date and/or time in any timezone.

    Safety and design:
    - No external I/O (network or filesystem access)
    - Validates timezones using `zoneinfo` and returns friendly errors
    - Simple, focused API: just action + timezone
    - All output is sanitized to remove problematic unicode characters

    Usage:
            execute(action: str, tz: str) -> str
            where action is one of: 'date', 'time', 'datetime',
            'timestamp', 'date_with_weekday'
            and tz is an IANA timezone string (e.g., 'UTC', 'America/New_York')

    Returns:
    - Error message starting with "[CurrentDateTool Error]" if validation fails
    - Otherwise, a string with the requested date/time information (sanitized)
    """

    name = 'currentdate'
    description = (
        'Get the current date and/or time in a specific timezone. '
        "Essential for answering 'What time is it?' or 'What day is it?' questions."
    )
    args_schema = CurrentDateInput

    def __init__(self, logger: Optional[LoggerInterface] = None) -> None:
        """Initialize the CurrentDateTool.

        Args:
            logger: Optional logger instance. If None, creates from config.
        """
        self.__logger = logger or create_logger(__name__)

    @staticmethod
    def __resolve_zone(tz: str) -> ZoneInfo:
        """Resolve the timezone string to a ZoneInfo object.

        Args:
            tz: The timezone string.

        Returns:
            ZoneInfo: The resolved ZoneInfo object.

        Raises:
            ValueError: If the timezone is invalid.
        """
        try:
            return _get_zoneinfo(tz.strip())
        except ZoneInfoNotFoundError as e:
            raise ValueError(f'Invalid timezone: {tz}') from e

    def execute(  # type: ignore[override]
        self,
        action: ActionType,
        tz: str,
    ) -> str:
        """Execute the tool with safety checks.

        Args:
            action: One of 'date', 'time', 'datetime', 'timestamp', 'date_with_weekday'
            tz: IANA timezone string (e.g., 'UTC', 'America/New_York')

        Returns:
            A string with the requested date/time, or an error message
            starting with "[CurrentDateTool Error]".
        """
        self.__logger.info(
            'CurrentDateTool.execute called: action=%s, tz=%s',
            action,
            tz,
        )

        # Validate action
        allowed = {
            'date',
            'time',
            'datetime',
            'timestamp',
            'date_with_weekday',
        }
        if action not in allowed:
            return self.__error(
                f"Invalid action '{action}'. Allowed: {sorted(allowed)}"
            )

        try:
            zone = self.__resolve_zone(tz)
        except ValueError:
            return self.__error(f"Invalid timezone '{tz}'")

        try:
            now = datetime.now(zone)

            if action == 'date':
                out = now.date().isoformat()

            elif action == 'time':
                out = now.time().strftime('%H:%M:%S')

            elif action == 'datetime':
                out = now.isoformat()

            elif action == 'timestamp':
                out = str(int(now.timestamp()))

            elif action == 'date_with_weekday':
                weekday = now.strftime('%A')
                date_str = now.strftime('%d de %B de %Y')
                out = f'{weekday}, {date_str}'

            else:
                return self.__error('Unsupported action')

            sanitized_response: str = TextSanitizer.sanitize(out)

            return sanitized_response

        except (ValueError, TypeError) as e:
            self.__logger.error(
                'Value/Type error in CurrentDateTool: %s', e, exc_info=True
            )
            return self.__error(f'Processing error: {type(e).__name__}: {e}')

        except Exception as e:
            self.__logger.error(
                'Unexpected error in CurrentDateTool: %s', e, exc_info=True
            )
            return self.__error(f'Unexpected error: {type(e).__name__}: {e}')

    def __error(self, details: str) -> str:
        """Format an error message.

        Args:
            details: The error details.

        Returns:
            str: The formatted error message.
        """
        msg = f'[CurrentDateTool Error] {details}'
        self.__logger.warning(msg)
        return msg
