import time

from pydantic import ValidationError
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from createagents.infra import CurrentDateTool
from createagents.infra.adapters.Tools.Current_Data_Tool.current_data_tool import (
    _get_zoneinfo,
)


@pytest.mark.unit
class TestCurrentDateTool:
    def setup_method(self):
        _get_zoneinfo.cache_clear()

    def test_tool_has_correct_name(self):
        tool = CurrentDateTool()
        assert tool.name == 'currentdate'

    def test_tool_has_description(self):
        tool = CurrentDateTool()
        assert tool.description
        assert 'date' in tool.description.lower()
        assert 'time' in tool.description.lower()

    def test_tool_has_parameters_schema(self):
        tool = CurrentDateTool()
        schema = tool.get_schema()
        assert schema['parameters']['type'] == 'object'
        assert 'properties' in schema['parameters']
        assert 'action' in schema['parameters']['properties']
        assert 'tz' in schema['parameters']['properties']
        assert 'required' in schema['parameters']
        assert 'action' in schema['parameters']['required']
        assert 'tz' in schema['parameters']['required']

    def test_action_parameter_has_valid_options(self):
        tool = CurrentDateTool()
        schema = tool.get_schema()
        action_prop = schema['parameters']['properties']['action']
        # Pydantic uses 'enum' for Literal types
        assert (
            'enum' in action_prop
            or 'anyOf' in action_prop
            or 'const' in action_prop
        )

    def test_run_date_action_utc(self):
        tool = CurrentDateTool()
        result = tool.run(action='date', tz='UTC')

        assert not result.startswith('[CurrentDateTool Error]')
        assert len(result) == 10
        assert result.count('-') == 2

    def test_run_time_action_utc(self):
        tool = CurrentDateTool()
        result = tool.run(action='time', tz='UTC')

        assert not result.startswith('[CurrentDateTool Error]')
        assert len(result) == 8
        assert result.count(':') == 2

    def test_run_datetime_action_utc(self):
        tool = CurrentDateTool()
        result = tool.run(action='datetime', tz='UTC')

        assert not result.startswith('[CurrentDateTool Error]')
        assert 'T' in result
        assert '-' in result
        assert ':' in result

    def test_run_timestamp_action_utc(self):
        tool = CurrentDateTool()
        result = tool.run(action='timestamp', tz='UTC')

        assert not result.startswith('[CurrentDateTool Error]')
        assert result.isdigit()
        assert int(result) > 1577836800

    def test_run_date_with_weekday_action_utc(self):
        tool = CurrentDateTool()
        result = tool.run(action='date_with_weekday', tz='UTC')

        assert not result.startswith('[CurrentDateTool Error]')
        weekdays = [
            'Monday',
            'Tuesday',
            'Wednesday',
            'Thursday',
            'Friday',
            'Saturday',
            'Sunday',
        ]
        assert any(day in result for day in weekdays)
        assert 'de' in result

    def test_run_with_different_timezones(self):
        tool = CurrentDateTool()
        timezones = [
            'UTC',
            'America/New_York',
            'America/Los_Angeles',
            'America/Sao_Paulo',
            'Europe/London',
            'Asia/Tokyo',
        ]

        for tz in timezones:
            result = tool.run(action='date', tz=tz)
            assert not result.startswith('[CurrentDateTool Error]'), (
                f'Failed for timezone: {tz}'
            )

    def test_run_with_invalid_action(self):
        """Tool should raise ValidationError for invalid action."""
        tool = CurrentDateTool()

        with pytest.raises(ValidationError) as exc_info:
            tool.run(action='invalid_action', tz='UTC')

        assert 'action' in str(exc_info.value)

    def test_run_with_invalid_timezone(self):
        tool = CurrentDateTool()
        result = tool.run(action='date', tz='Invalid/Timezone')

        assert result.startswith('[CurrentDateTool Error]')
        assert 'Invalid timezone' in result

    def test_run_with_empty_timezone(self):
        tool = CurrentDateTool()
        result = tool.run(action='date', tz='')

        assert result.startswith('[CurrentDateTool Error]')

    def test_run_strips_whitespace_from_timezone(self):
        tool = CurrentDateTool()
        result = tool.run(action='date', tz='  UTC  ')

        assert not result.startswith('[CurrentDateTool Error]')

    def test_zoneinfo_cache_functionality(self):
        _get_zoneinfo.cache_clear()

        zone1 = _get_zoneinfo('UTC')
        cache_info = _get_zoneinfo.cache_info()
        assert cache_info.misses == 1
        assert cache_info.hits == 0

        zone2 = _get_zoneinfo('UTC')
        cache_info = _get_zoneinfo.cache_info()
        assert cache_info.hits == 1

        assert zone1 is zone2

    def test_zoneinfo_cache_different_timezones(self):
        _get_zoneinfo.cache_clear()

        zones = ['UTC', 'America/New_York', 'Europe/London']
        for tz in zones:
            _get_zoneinfo(tz)

        cache_info = _get_zoneinfo.cache_info()
        assert cache_info.currsize == 3

    def test_run_with_various_actions(self):
        tool = CurrentDateTool()
        actions = [
            'date',
            'time',
            'datetime',
            'timestamp',
            'date_with_weekday',
        ]

        for action in actions:
            result = tool.run(action=action, tz='UTC')
            assert not result.startswith('[CurrentDateTool Error]'), (
                f'Failed for action: {action}'
            )

    def test_output_is_sanitized(self):
        tool = CurrentDateTool()
        with patch(
            'createagents.infra.adapters.Tools.Current_Data_Tool.current_data_tool.TextSanitizer.sanitize'
        ) as mock_sanitize:
            mock_sanitize.return_value = 'sanitized_output'

            result = tool.run(action='date', tz='UTC')

            assert mock_sanitize.called
            assert result == 'sanitized_output'

    def test_logging_on_run(self):
        tool = CurrentDateTool()
        with patch.object(tool._CurrentDateTool__logger, 'info') as mock_info:
            tool.run(action='date', tz='UTC')

            assert mock_info.called

    def test_logging_on_error(self):
        """Tool should log warnings on errors (like invalid timezone)."""
        tool = CurrentDateTool()
        with patch.object(
            tool._CurrentDateTool__logger, 'warning'
        ) as mock_warning:
            tool.run(action='date', tz='Invalid/Timezone')

            assert mock_warning.called

    def test_unexpected_exception_handling(self):
        tool = CurrentDateTool()

        with patch(
            'createagents.infra.adapters.Tools.Current_Data_Tool.current_data_tool.datetime'
        ) as mock_datetime:
            mock_datetime.now.side_effect = RuntimeError('Unexpected error')

            result = tool.run(action='date', tz='UTC')

            assert result.startswith('[CurrentDateTool Error]')
            assert 'Unexpected error' in result

    def test_run_date_returns_iso_format(self):
        tool = CurrentDateTool()
        result = tool.run(action='date', tz='UTC')

        try:
            datetime.fromisoformat(result)
            assert True
        except ValueError:
            pytest.fail('Date is not in ISO format')

    def test_run_datetime_returns_iso_format(self):
        tool = CurrentDateTool()
        result = tool.run(action='datetime', tz='UTC')

        try:
            datetime.fromisoformat(result.replace('+00:00', ''))
            assert True
        except ValueError:
            pytest.fail('Datetime is not in ISO format')

    def test_run_timestamp_is_numeric(self):
        tool = CurrentDateTool()
        result = tool.run(action='timestamp', tz='UTC')

        timestamp = int(result)
        assert 1577836800 < timestamp < 2524608000

    def test_run_with_sao_paulo_timezone(self):
        tool = CurrentDateTool()
        result = tool.run(action='datetime', tz='America/Sao_Paulo')

        assert not result.startswith('[CurrentDateTool Error]')
        assert '-03:00' in result or '-02:00' in result

    def test_error_message_format_consistency(self):
        """Error messages from _run should follow consistent format."""
        tool = CurrentDateTool()

        # Test invalid timezone (handled in _run method)
        error = tool.run(action='date', tz='Invalid/TZ')

        assert error.startswith('[CurrentDateTool Error]')
        assert ']' in error

    def test_concurrent_run(self):
        import concurrent.futures

        tool = CurrentDateTool()
        results = []

        def run_tool():
            return tool.run(action='date', tz='UTC')

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_tool) for _ in range(50)]
            results = [
                future.result()
                for future in concurrent.futures.as_completed(futures)
            ]

        assert all(
            not r.startswith('[CurrentDateTool Error]') for r in results
        )
        assert len(results) == 50

    def test_multiple_tool_instances_independent(self):
        tool1 = CurrentDateTool()
        tool2 = CurrentDateTool()

        result1 = tool1.run(action='date', tz='UTC')
        result2 = tool2.run(action='time', tz='America/New_York')

        assert not result1.startswith('[CurrentDateTool Error]')
        assert not result2.startswith('[CurrentDateTool Error]')
        assert result1 != result2

    def test_run_with_chicago_timezone(self):
        tool = CurrentDateTool()
        result = tool.run(action='datetime', tz='America/Chicago')

        assert not result.startswith('[CurrentDateTool Error]')

    def test_run_with_lisbon_timezone(self):
        tool = CurrentDateTool()
        result = tool.run(action='datetime', tz='Europe/Lisbon')

        assert not result.startswith('[CurrentDateTool Error]')

    def test_date_with_weekday_contains_proper_format(self):
        tool = CurrentDateTool()
        result = tool.run(action='date_with_weekday', tz='UTC')

        assert ', ' in result
        parts = result.split(', ')
        assert len(parts) == 2
        assert parts[0] in [
            'Monday',
            'Tuesday',
            'Wednesday',
            'Thursday',
            'Friday',
            'Saturday',
            'Sunday',
        ]

    def test_timezone_case_sensitivity(self):
        tool = CurrentDateTool()

        result_correct = tool.run(action='date', tz='UTC')
        assert not result_correct.startswith('[CurrentDateTool Error]')

        result_wrong = tool.run(action='date', tz='utc')
        assert result_wrong.startswith('[CurrentDateTool Error]')

    def test_tool_is_safe_no_io_operations(self):
        tool = CurrentDateTool()

        with patch(
            'builtins.open',
            side_effect=AssertionError('Should not open files'),
        ):
            with patch(
                'urllib.request.urlopen',
                side_effect=AssertionError('Should not access network'),
            ):
                result = tool.run(action='date', tz='UTC')
                assert not result.startswith('[CurrentDateTool Error]')

    def test_error_includes_allowed_actions(self):
        """ValidationError should show allowed action values."""
        tool = CurrentDateTool()

        with pytest.raises(ValidationError) as exc_info:
            tool.run(action='bad_action', tz='UTC')

        error_message = str(exc_info.value)
        # Pydantic shows literal values in the error message
        assert 'date' in error_message
        assert 'time' in error_message
        assert 'datetime' in error_message

    def test_cache_size_limit(self):
        _get_zoneinfo.cache_clear()

        for i in range(40):
            try:
                _get_zoneinfo(f'Etc/GMT+{i % 12}')
            except Exception:
                pass

        cache_info = _get_zoneinfo.cache_info()
        assert cache_info.maxsize == 32

    def test_schema_completeness(self):
        tool = CurrentDateTool()
        schema = tool.get_schema()
        params = schema['parameters']

        assert params['type'] == 'object'
        assert 'properties' in params
        assert 'required' in params

        action_prop = params['properties']['action']
        assert 'description' in action_prop

        tz_prop = params['properties']['tz']
        assert 'description' in tz_prop

    def test_logger_initialization(self):
        tool = CurrentDateTool()
        logger = tool._CurrentDateTool__logger

        assert logger is not None
        assert (
            logger.name
            == 'createagents.infra.adapters.Tools.Current_Data_Tool.current_data_tool'
        )

    def test_no_side_effects_between_calls(self):
        tool = CurrentDateTool()

        results = []
        for _ in range(5):
            result = tool.run(action='timestamp', tz='UTC')
            results.append(int(result))
            time.sleep(0.1)

        assert all(r > 0 for r in results)
        assert results[-1] >= results[0]


@pytest.mark.unit
class TestGetZoneInfo:
    def setup_method(self):
        _get_zoneinfo.cache_clear()

    def test_returns_zoneinfo_object(self):
        zone = _get_zoneinfo('UTC')
        assert isinstance(zone, ZoneInfo)

    def test_caches_timezone(self):
        zone1 = _get_zoneinfo('UTC')
        zone2 = _get_zoneinfo('UTC')

        assert zone1 is zone2

    def test_different_timezones_cached_separately(self):
        utc = _get_zoneinfo('UTC')
        ny = _get_zoneinfo('America/New_York')

        assert utc is not ny

    def test_cache_info_accessible(self):
        _get_zoneinfo('UTC')
        info = _get_zoneinfo.cache_info()

        assert hasattr(info, 'hits')
        assert hasattr(info, 'misses')
        assert hasattr(info, 'maxsize')
        assert hasattr(info, 'currsize')

    def test_invalid_timezone_raises_error(self):
        from zoneinfo import ZoneInfoNotFoundError

        with pytest.raises(ZoneInfoNotFoundError):
            _get_zoneinfo('Invalid/Timezone')

    def test_cache_maxsize(self):
        info = _get_zoneinfo.cache_info()
        assert info.maxsize == 32
