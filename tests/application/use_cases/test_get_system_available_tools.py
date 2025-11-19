from unittest.mock import patch

import pytest

from createagents.application import GetSystemAvailableToolsUseCase


@pytest.mark.unit
class TestGetSystemAvailableToolsUseCase:
    @patch(
        "createagents.application.use_cases.get_system_available_tools.AvailableTools.get_system_tools"
    )
    def test_execute_returns_dict(self, mock_get_system):
        mock_get_system.return_value = {"tool1": "desc1"}
        use_case = GetSystemAvailableToolsUseCase()
        result = use_case.execute()
        assert isinstance(result, dict)

    @patch(
        "createagents.application.use_cases.get_system_available_tools.AvailableTools.get_system_tools"
    )
    def test_execute_returns_non_empty_dict(self, mock_get_system):
        mock_get_system.return_value = {"tool1": "desc1"}
        use_case = GetSystemAvailableToolsUseCase()
        result = use_case.execute()
        assert len(result) > 0

    @patch(
        "createagents.application.use_cases.get_system_available_tools.AvailableTools.get_system_tools"
    )
    def test_execute_contains_currentdate_tool(self, mock_get_system):
        mock_get_system.return_value = {"currentdate": "Gets current date"}
        use_case = GetSystemAvailableToolsUseCase()
        result = use_case.execute()
        assert "currentdate" in result

    @patch(
        "createagents.application.use_cases.get_system_available_tools.AvailableTools.get_system_tools"
    )
    def test_execute_tool_descriptions_are_strings(self, mock_get_system):
        mock_get_system.return_value = {"tool1": "desc1", "tool2": "desc2"}
        use_case = GetSystemAvailableToolsUseCase()
        result = use_case.execute()
        for tool_name, tool_description in result.items():
            assert isinstance(tool_name, str)
            assert isinstance(tool_description, str)
            assert len(tool_description) > 0

    @patch(
        "createagents.application.use_cases.get_system_available_tools.AvailableTools.get_system_tools"
    )
    def test_execute_returns_consistent_results(self, mock_get_system):
        mock_get_system.return_value = {"tool1": "desc1"}
        use_case = GetSystemAvailableToolsUseCase()
        result1 = use_case.execute()
        result2 = use_case.execute()
        assert result1 == result2

    @patch(
        "createagents.application.use_cases.get_system_available_tools.AvailableTools.get_system_tools"
    )
    def test_currentdate_tool_description(self, mock_get_system):
        mock_get_system.return_value = {"currentdate": "Gets current date"}
        use_case = GetSystemAvailableToolsUseCase()
        result = use_case.execute()
        assert "currentdate" in result
        assert isinstance(result["currentdate"], str)
        assert len(result["currentdate"]) > 0

    @patch(
        "createagents.application.use_cases.get_system_available_tools.AvailableTools.get_system_tools"
    )
    def test_execute_tool_names_are_strings(self, mock_get_system):
        mock_get_system.return_value = {"tool1": "desc1", "tool2": "desc2"}
        use_case = GetSystemAvailableToolsUseCase()
        result = use_case.execute()
        for tool_name in result.keys():
            assert isinstance(tool_name, str)
            assert len(tool_name) > 0

    @patch(
        "createagents.application.use_cases.get_system_available_tools.AvailableTools.get_system_tools"
    )
    def test_execute_with_empty_tools(self, mock_get_system):
        mock_get_system.return_value = {}
        use_case = GetSystemAvailableToolsUseCase()
        result = use_case.execute()
        assert result == {}
