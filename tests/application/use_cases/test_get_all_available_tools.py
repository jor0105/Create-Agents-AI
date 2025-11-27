from unittest.mock import patch

import pytest

from createagents.application import GetAllAvailableToolsUseCase


@pytest.mark.unit
class TestGetAllAvailableToolsUseCase:
    @patch(
        'createagents.application.use_cases.get_all_available_tools.AvailableTools.get_all_available_tools'
    )
    def test_execute_returns_dict(self, mock_get_all):
        mock_get_all.return_value = {'tool1': 'desc1'}
        use_case = GetAllAvailableToolsUseCase()
        result = use_case.execute()
        assert isinstance(result, dict)

    @patch(
        'createagents.application.use_cases.get_all_available_tools.AvailableTools.get_all_available_tools'
    )
    def test_execute_returns_non_empty_dict(self, mock_get_all):
        mock_get_all.return_value = {'tool1': 'desc1'}
        use_case = GetAllAvailableToolsUseCase()
        result = use_case.execute()
        assert len(result) > 0

    @patch(
        'createagents.application.use_cases.get_all_available_tools.AvailableTools.get_all_available_tools'
    )
    def test_execute_tool_names_are_strings(self, mock_get_all):
        mock_get_all.return_value = {'tool1': 'desc1', 'tool2': 'desc2'}
        use_case = GetAllAvailableToolsUseCase()
        result = use_case.execute()
        for tool_name in result.keys():
            assert isinstance(tool_name, str)
            assert len(tool_name) > 0

    @patch(
        'createagents.application.use_cases.get_all_available_tools.AvailableTools.get_all_available_tools'
    )
    def test_execute_tool_descriptions_are_strings(self, mock_get_all):
        mock_get_all.return_value = {'tool1': 'desc1', 'tool2': 'desc2'}
        use_case = GetAllAvailableToolsUseCase()
        result = use_case.execute()
        for tool_description in result.values():
            assert isinstance(tool_description, str)
            assert len(tool_description) > 0

    @patch(
        'createagents.application.use_cases.get_all_available_tools.AvailableTools.get_all_available_tools'
    )
    def test_execute_returns_consistent_results(self, mock_get_all):
        mock_get_all.return_value = {'tool1': 'desc1'}
        use_case = GetAllAvailableToolsUseCase()
        result1 = use_case.execute()
        result2 = use_case.execute()
        assert result1 == result2

    @patch(
        'createagents.application.use_cases.get_all_available_tools.AvailableTools.get_all_available_tools'
    )
    def test_execute_includes_system_tools(self, mock_get_all):
        mock_get_all.return_value = {
            'currentdate': 'Gets current date',
            'tool2': 'desc2',
        }
        use_case = GetAllAvailableToolsUseCase()
        result = use_case.execute()
        assert 'currentdate' in result

    @patch(
        'createagents.application.use_cases.get_all_available_tools.AvailableTools.get_all_available_tools'
    )
    def test_execute_with_empty_tools(self, mock_get_all):
        mock_get_all.return_value = {}
        use_case = GetAllAvailableToolsUseCase()
        result = use_case.execute()
        assert result == {}
