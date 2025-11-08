"""Comprehensive tests for CurrentDateTool."""

import time
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from src.infra.adapters.Tools.Current_Data_Tool.current_data_tool import (
    CurrentDateTool,
    _get_zoneinfo,
)


@pytest.mark.unit
class TestCurrentDateTool:
    """Test suite for CurrentDateTool functionality."""

    def setup_method(self):
        """Setup before each test."""
        # Clear LRU cache
        _get_zoneinfo.cache_clear()

    def test_tool_has_correct_name(self):
        """Test that tool has the expected name."""
        tool = CurrentDateTool()
        assert tool.name == "current_date"

    def test_tool_has_description(self):
        """Test that tool has a description."""
        tool = CurrentDateTool()
        assert tool.description
        assert "date" in tool.description.lower()
        assert "time" in tool.description.lower()

    def test_tool_has_parameters_schema(self):
        """Test that tool has properly defined parameters."""
        tool = CurrentDateTool()
        assert "type" in tool.parameters
        assert tool.parameters["type"] == "object"
        assert "properties" in tool.parameters
        assert "action" in tool.parameters["properties"]
        assert "tz" in tool.parameters["properties"]
        assert "required" in tool.parameters
        assert "action" in tool.parameters["required"]
        assert "tz" in tool.parameters["required"]

    def test_action_parameter_has_enum(self):
        """Test that action parameter has allowed values."""
        tool = CurrentDateTool()
        action_enum = tool.parameters["properties"]["action"]["enum"]
        assert "date" in action_enum
        assert "time" in action_enum
        assert "datetime" in action_enum
        assert "timestamp" in action_enum
        assert "date_with_weekday" in action_enum

    def test_execute_date_action_utc(self):
        """Test date action with UTC timezone."""
        tool = CurrentDateTool()
        result = tool.execute(action="date", tz="UTC")

        assert not result.startswith("[CurrentDateTool Error]")
        # Should be ISO format date: YYYY-MM-DD
        assert len(result) == 10
        assert result.count("-") == 2

    def test_execute_time_action_utc(self):
        """Test time action with UTC timezone."""
        tool = CurrentDateTool()
        result = tool.execute(action="time", tz="UTC")

        assert not result.startswith("[CurrentDateTool Error]")
        # Should be HH:MM:SS format
        assert len(result) == 8
        assert result.count(":") == 2

    def test_execute_datetime_action_utc(self):
        """Test datetime action with UTC timezone."""
        tool = CurrentDateTool()
        result = tool.execute(action="datetime", tz="UTC")

        assert not result.startswith("[CurrentDateTool Error]")
        # Should be ISO format datetime
        assert "T" in result
        assert "-" in result
        assert ":" in result

    def test_execute_timestamp_action_utc(self):
        """Test timestamp action with UTC timezone."""
        tool = CurrentDateTool()
        result = tool.execute(action="timestamp", tz="UTC")

        assert not result.startswith("[CurrentDateTool Error]")
        # Should be numeric timestamp
        assert result.isdigit()
        # Should be reasonable Unix timestamp (after 2020)
        assert int(result) > 1577836800

    def test_execute_date_with_weekday_action_utc(self):
        """Test date_with_weekday action with UTC timezone."""
        tool = CurrentDateTool()
        result = tool.execute(action="date_with_weekday", tz="UTC")

        assert not result.startswith("[CurrentDateTool Error]")
        # Should contain weekday name
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        assert any(day in result for day in weekdays)
        assert "de" in result  # Portuguese format

    def test_execute_with_different_timezones(self):
        """Test execution with various timezones."""
        tool = CurrentDateTool()
        timezones = [
            "UTC",
            "America/New_York",
            "America/Los_Angeles",
            "America/Sao_Paulo",
            "Europe/London",
            "Asia/Tokyo",
        ]

        for tz in timezones:
            result = tool.execute(action="date", tz=tz)
            assert not result.startswith(
                "[CurrentDateTool Error]"
            ), f"Failed for timezone: {tz}"

    def test_execute_with_invalid_action(self):
        """Test that invalid action returns error."""
        tool = CurrentDateTool()
        result = tool.execute(action="invalid_action", tz="UTC")

        assert result.startswith("[CurrentDateTool Error]")
        assert "Invalid action" in result
        assert "invalid_action" in result

    def test_execute_with_invalid_timezone(self):
        """Test that invalid timezone returns error."""
        tool = CurrentDateTool()
        result = tool.execute(action="date", tz="Invalid/Timezone")

        assert result.startswith("[CurrentDateTool Error]")
        assert "Invalid timezone" in result

    def test_execute_with_empty_timezone(self):
        """Test that empty timezone returns error."""
        tool = CurrentDateTool()
        result = tool.execute(action="date", tz="")

        assert result.startswith("[CurrentDateTool Error]")

    def test_execute_strips_whitespace_from_timezone(self):
        """Test that whitespace in timezone is handled."""
        tool = CurrentDateTool()
        result = tool.execute(action="date", tz="  UTC  ")

        assert not result.startswith("[CurrentDateTool Error]")

    def test_zoneinfo_cache_functionality(self):
        """Test that timezone resolution is cached."""
        _get_zoneinfo.cache_clear()

        # First call - cache miss
        zone1 = _get_zoneinfo("UTC")
        cache_info = _get_zoneinfo.cache_info()
        assert cache_info.misses == 1
        assert cache_info.hits == 0

        # Second call - cache hit
        zone2 = _get_zoneinfo("UTC")
        cache_info = _get_zoneinfo.cache_info()
        assert cache_info.hits == 1

        assert zone1 is zone2

    def test_zoneinfo_cache_different_timezones(self):
        """Test cache with multiple timezones."""
        _get_zoneinfo.cache_clear()

        zones = ["UTC", "America/New_York", "Europe/London"]
        for tz in zones:
            _get_zoneinfo(tz)

        cache_info = _get_zoneinfo.cache_info()
        assert cache_info.currsize == 3

    def test_execute_with_various_actions(self):
        """Test all valid actions produce non-error results."""
        tool = CurrentDateTool()
        actions = ["date", "time", "datetime", "timestamp", "date_with_weekday"]

        for action in actions:
            result = tool.execute(action=action, tz="UTC")
            assert not result.startswith(
                "[CurrentDateTool Error]"
            ), f"Failed for action: {action}"

    def test_output_is_sanitized(self):
        """Test that output goes through text sanitization."""
        tool = CurrentDateTool()
        with patch(
            "src.infra.adapters.Tools.Current_Data_Tool.current_data_tool.TextSanitizer.sanitize"
        ) as mock_sanitize:
            mock_sanitize.return_value = "sanitized_output"

            result = tool.execute(action="date", tz="UTC")

            assert mock_sanitize.called
            assert result == "sanitized_output"

    def test_logging_on_execution(self):
        """Test that execution is logged."""
        tool = CurrentDateTool()
        with patch.object(tool._CurrentDateTool__logger, "info") as mock_info:
            tool.execute(action="date", tz="UTC")

            assert mock_info.called
            call_args = str(mock_info.call_args)
            assert "CurrentDateTool.execute" in call_args

    def test_logging_on_error(self):
        """Test that errors are logged."""
        tool = CurrentDateTool()
        with patch.object(tool._CurrentDateTool__logger, "warning") as mock_warning:
            tool.execute(action="invalid", tz="UTC")

            assert mock_warning.called

    def test_unexpected_exception_handling(self):
        """Test handling of unexpected exceptions."""
        tool = CurrentDateTool()

        with patch(
            "src.infra.adapters.Tools.Current_Data_Tool.current_data_tool.datetime"
        ) as mock_datetime:
            mock_datetime.now.side_effect = RuntimeError("Unexpected error")

            result = tool.execute(action="date", tz="UTC")

            assert result.startswith("[CurrentDateTool Error]")
            assert "Unexpected error" in result

    def test_execute_date_returns_iso_format(self):
        """Test that date action returns ISO formatted date."""
        tool = CurrentDateTool()
        result = tool.execute(action="date", tz="UTC")

        # Try to parse as ISO date
        try:
            datetime.fromisoformat(result)
            assert True
        except ValueError:
            pytest.fail("Date is not in ISO format")

    def test_execute_datetime_returns_iso_format(self):
        """Test that datetime action returns ISO formatted datetime."""
        tool = CurrentDateTool()
        result = tool.execute(action="datetime", tz="UTC")

        # Should be parseable as ISO datetime
        try:
            datetime.fromisoformat(result.replace("+00:00", ""))
            assert True
        except ValueError:
            pytest.fail("Datetime is not in ISO format")

    def test_execute_timestamp_is_numeric(self):
        """Test that timestamp is a valid integer."""
        tool = CurrentDateTool()
        result = tool.execute(action="timestamp", tz="UTC")

        timestamp = int(result)
        # Should be a reasonable timestamp (between 2020 and 2050)
        assert 1577836800 < timestamp < 2524608000

    def test_execute_with_sao_paulo_timezone(self):
        """Test with Brazil timezone specifically."""
        tool = CurrentDateTool()
        result = tool.execute(action="datetime", tz="America/Sao_Paulo")

        assert not result.startswith("[CurrentDateTool Error]")
        # Should contain timezone offset
        assert "-03:00" in result or "-02:00" in result  # DST consideration

    def test_constants_defined(self):
        """Test that tool constants are defined."""
        tool = CurrentDateTool()
        assert hasattr(tool, "MAX_OFFSET_DAYS")
        assert hasattr(tool, "MAX_FORMAT_LENGTH")
        assert tool.MAX_OFFSET_DAYS == 3650
        assert tool.MAX_FORMAT_LENGTH == 200

    def test_error_message_format_consistency(self):
        """Test that error messages follow consistent format."""
        tool = CurrentDateTool()

        errors = [
            tool.execute(action="invalid", tz="UTC"),
            tool.execute(action="date", tz="Invalid/TZ"),
        ]

        for error in errors:
            assert error.startswith("[CurrentDateTool Error]")
            assert "]" in error

    def test_concurrent_execution(self):
        """Test tool can handle concurrent executions."""
        import concurrent.futures

        tool = CurrentDateTool()
        results = []

        def execute_tool():
            return tool.execute(action="date", tz="UTC")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_tool) for _ in range(50)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All should succeed
        assert all(not r.startswith("[CurrentDateTool Error]") for r in results)
        assert len(results) == 50

    def test_multiple_tool_instances_independent(self):
        """Test that multiple tool instances work independently."""
        tool1 = CurrentDateTool()
        tool2 = CurrentDateTool()

        result1 = tool1.execute(action="date", tz="UTC")
        result2 = tool2.execute(action="time", tz="America/New_York")

        assert not result1.startswith("[CurrentDateTool Error]")
        assert not result2.startswith("[CurrentDateTool Error]")
        assert result1 != result2

    def test_execute_with_chicago_timezone(self):
        """Test with Chicago timezone mentioned in description."""
        tool = CurrentDateTool()
        result = tool.execute(action="datetime", tz="America/Chicago")

        assert not result.startswith("[CurrentDateTool Error]")

    def test_execute_with_lisbon_timezone(self):
        """Test with Lisbon timezone mentioned in description."""
        tool = CurrentDateTool()
        result = tool.execute(action="datetime", tz="Europe/Lisbon")

        assert not result.startswith("[CurrentDateTool Error]")

    def test_date_with_weekday_contains_proper_format(self):
        """Test date_with_weekday has expected format."""
        tool = CurrentDateTool()
        result = tool.execute(action="date_with_weekday", tz="UTC")

        # Should have format: "Weekday, DD de Month de YYYY"
        assert ", " in result
        parts = result.split(", ")
        assert len(parts) == 2
        # First part is weekday
        assert parts[0] in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

    def test_timezone_case_sensitivity(self):
        """Test timezone names are case-sensitive as expected."""
        tool = CurrentDateTool()

        # Correct case should work
        result_correct = tool.execute(action="date", tz="UTC")
        assert not result_correct.startswith("[CurrentDateTool Error]")

        # Wrong case should fail (timezone names are case-sensitive)
        result_wrong = tool.execute(action="date", tz="utc")
        assert result_wrong.startswith("[CurrentDateTool Error]")

    def test_tool_is_safe_no_io_operations(self):
        """Test that tool doesn't perform any I/O operations."""
        tool = CurrentDateTool()

        # Execute tool and ensure no file or network operations
        with patch(
            "builtins.open", side_effect=AssertionError("Should not open files")
        ):
            with patch(
                "urllib.request.urlopen",
                side_effect=AssertionError("Should not access network"),
            ):
                result = tool.execute(action="date", tz="UTC")
                assert not result.startswith("[CurrentDateTool Error]")

    def test_error_includes_allowed_actions(self):
        """Test that error message includes allowed actions."""
        tool = CurrentDateTool()
        result = tool.execute(action="bad_action", tz="UTC")

        assert "Allowed:" in result
        assert "date" in result
        assert "time" in result
        assert "datetime" in result

    def test_cache_size_limit(self):
        """Test that LRU cache has size limit."""
        _get_zoneinfo.cache_clear()

        # Create more entries than cache size (32)
        for i in range(40):
            try:
                _get_zoneinfo(f"Etc/GMT+{i % 12}")
            except Exception:
                pass

        cache_info = _get_zoneinfo.cache_info()
        assert cache_info.maxsize == 32

    def test_parameters_schema_completeness(self):
        """Test that parameters schema is complete."""
        tool = CurrentDateTool()
        params = tool.parameters

        # Check all required fields are present
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params

        # Check action property
        action_prop = params["properties"]["action"]
        assert action_prop["type"] == "string"
        assert "enum" in action_prop
        assert "description" in action_prop

        # Check tz property
        tz_prop = params["properties"]["tz"]
        assert tz_prop["type"] == "string"
        assert "description" in tz_prop
        assert "Examples:" in tz_prop["description"]

    def test_logger_initialization(self):
        """Test that logger is properly initialized."""
        tool = CurrentDateTool()
        logger = tool._CurrentDateTool__logger

        assert logger is not None
        assert (
            logger.name
            == "src.infra.adapters.Tools.Current_Data_Tool.current_data_tool"
        )

    def test_no_side_effects_between_calls(self):
        """Test that repeated calls don't affect each other."""
        tool = CurrentDateTool()

        results = []
        for _ in range(5):
            result = tool.execute(action="timestamp", tz="UTC")
            results.append(int(result))
            time.sleep(0.1)

        # All should be valid timestamps
        assert all(r > 0 for r in results)
        # Should be in ascending order (time moves forward)
        assert results[-1] >= results[0]


@pytest.mark.unit
class TestGetZoneInfo:
    """Test suite for _get_zoneinfo caching function."""

    def setup_method(self):
        """Setup before each test."""
        _get_zoneinfo.cache_clear()

    def test_returns_zoneinfo_object(self):
        """Test that function returns ZoneInfo object."""
        zone = _get_zoneinfo("UTC")
        assert isinstance(zone, ZoneInfo)

    def test_caches_timezone(self):
        """Test that timezone is cached."""
        zone1 = _get_zoneinfo("UTC")
        zone2 = _get_zoneinfo("UTC")

        assert zone1 is zone2

    def test_different_timezones_cached_separately(self):
        """Test that different timezones are cached separately."""
        utc = _get_zoneinfo("UTC")
        ny = _get_zoneinfo("America/New_York")

        assert utc is not ny

    def test_cache_info_accessible(self):
        """Test that cache info is accessible."""
        _get_zoneinfo("UTC")
        info = _get_zoneinfo.cache_info()

        assert hasattr(info, "hits")
        assert hasattr(info, "misses")
        assert hasattr(info, "maxsize")
        assert hasattr(info, "currsize")

    def test_invalid_timezone_raises_error(self):
        """Test that invalid timezone raises ZoneInfoNotFoundError."""
        from zoneinfo import ZoneInfoNotFoundError

        with pytest.raises(ZoneInfoNotFoundError):
            _get_zoneinfo("Invalid/Timezone")

    def test_cache_maxsize(self):
        """Test cache has correct maxsize."""
        info = _get_zoneinfo.cache_info()
        assert info.maxsize == 32
