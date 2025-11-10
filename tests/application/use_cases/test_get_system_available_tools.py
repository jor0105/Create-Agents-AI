"""Tests for GetSystemAvailableToolsUseCase."""

from src.application.use_cases.get_system_available_tools import (
    GetSystemAvailableToolsUseCase,
)


class TestGetSystemAvailableToolsUseCase:
    """Test suite for GetSystemAvailableToolsUseCase."""

    def setup_method(self):
        """Set up test fixtures."""
        self.use_case = GetSystemAvailableToolsUseCase()

    def test_execute_returns_dict(self):
        """Test that execute returns a dictionary."""
        result = self.use_case.execute()
        assert isinstance(result, dict)

    def test_execute_returns_non_empty_dict(self):
        """Test that execute returns a non-empty dictionary (at least currentdate)."""
        result = self.use_case.execute()
        assert len(result) > 0

    def test_execute_contains_currentdate_tool(self):
        """Test that system tools include currentdate."""
        result = self.use_case.execute()
        assert "currentdate" in result

    def test_execute_tool_descriptions_are_strings(self):
        """Test that all tool descriptions are strings."""
        result = self.use_case.execute()
        for tool_name, tool_description in result.items():
            assert isinstance(tool_name, str)
            assert isinstance(tool_description, str)
            assert len(tool_description) > 0

    def test_execute_returns_consistent_results(self):
        """Test that execute returns consistent results across multiple calls."""
        result1 = self.use_case.execute()
        result2 = self.use_case.execute()
        assert result1 == result2

    def test_currentdate_tool_description(self):
        """Test that currentdate tool has a description."""
        result = self.use_case.execute()
        assert "currentdate" in result
        assert isinstance(result["currentdate"], str)
        assert len(result["currentdate"]) > 0
