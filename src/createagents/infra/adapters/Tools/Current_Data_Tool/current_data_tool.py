from datetime import datetime
from functools import lru_cache
from typing import Any, Dict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .....domain import BaseTool
from .....utils import TextSanitizer
from ....config import LoggingConfig


@lru_cache(maxsize=32)
def _get_zoneinfo(tz: str) -> ZoneInfo:
    return ZoneInfo(tz)


class CurrentDateTool(BaseTool):
    """Secure tool that provides the current date and/or time in any timezone.

    Safety and design:
    - No external I/O (network or filesystem access)
    - Validates timezones using `zoneinfo` and returns friendly errors
    - Simple, focused API: just action + timezone
    - All output is sanitized to remove problematic unicode characters

    Usage:
            execute(action: str, tz: str) -> str
            where action is one of: 'date', 'time', 'datetime', 'timestamp', 'date_with_weekday'
            and tz is an IANA timezone string (e.g., 'UTC', 'America/New_York')

    Returns:
    - Error message starting with "[CurrentDateTool Error]" if validation fails
    - Otherwise, a string with the requested date/time information (sanitized)
    """

    name = 'currentdate'
    description = "Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions."
    parameters: Dict[str, Any] = {
        'type': 'object',
        'properties': {
            'action': {
                'type': 'string',
                'enum': [
                    'date',
                    'time',
                    'datetime',
                    'timestamp',
                    'date_with_weekday',
                ],
                'description': "What information to return: 'date' (just the date), 'time' (just the time), 'datetime' (both), 'timestamp' (unix seconds), or 'date_with_weekday' (full date with weekday)",
            },
            'tz': {
                'type': 'string',
                'description': "IANA timezone identifier. Examples: 'UTC', 'America/New_York' (New York), 'America/Los_Angeles' (California), 'America/Chicago' (Chicago), 'America/Sao_Paulo' (Brazil), 'Europe/Lisbon', etc.",
            },
        },
        'required': ['action', 'tz'],
    }

    # Limits / security constants
    MAX_OFFSET_DAYS = 3650  # 10 years (kept for potential future use)
    MAX_FORMAT_LENGTH = 200  # kept for potential future use

    def __init__(self) -> None:
        self.__logger = LoggingConfig.get_logger(__name__)

    @staticmethod
    def __resolve_zone(tz: str) -> ZoneInfo:
        try:
            return _get_zoneinfo(tz.strip())
        except ZoneInfoNotFoundError:
            raise ValueError(f'Invalid timezone: {tz}')

    def execute(
        self,
        action: str,
        tz: str,
    ) -> str:
        """Run the tool with safety checks.

        Args:
                action: One of 'date', 'time', 'datetime', 'timestamp'
                tz: IANA timezone string (e.g., 'UTC', 'America/New_York')

        Returns:
                A string with the requested date/time, or an error message starting with
                "[CurrentDateTool Error]".
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
        except Exception:
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

        except Exception as e:
            self.__logger.error(
                'Unexpected error in CurrentDateTool: %s', e, exc_info=True
            )
            return self.__error(f'Unexpected error: {type(e).__name__}: {e}')

    def __error(self, details: str) -> str:
        msg = f'[CurrentDateTool Error] {details}'
        self.__logger.warning(msg)
        return msg
