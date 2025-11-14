from arcadiumai.application import GetSystemAvailableToolsUseCase


class TestGetSystemAvailableToolsUseCase:
    def setup_method(self):
        self.use_case = GetSystemAvailableToolsUseCase()

    def test_execute_returns_dict(self):
        result = self.use_case.execute()
        assert isinstance(result, dict)

    def test_execute_returns_non_empty_dict(self):
        result = self.use_case.execute()
        assert len(result) > 0

    def test_execute_contains_currentdate_tool(self):
        result = self.use_case.execute()
        assert "currentdate" in result

    def test_execute_tool_descriptions_are_strings(self):
        result = self.use_case.execute()
        for tool_name, tool_description in result.items():
            assert isinstance(tool_name, str)
            assert isinstance(tool_description, str)
            assert len(tool_description) > 0

    def test_execute_returns_consistent_results(self):
        result1 = self.use_case.execute()
        result2 = self.use_case.execute()
        assert result1 == result2

    def test_currentdate_tool_description(self):
        result = self.use_case.execute()
        assert "currentdate" in result
        assert isinstance(result["currentdate"], str)
        assert len(result["currentdate"]) > 0
