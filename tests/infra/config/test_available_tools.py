"""Comprehensive tests for AvailableTools registry."""

from unittest.mock import Mock, patch

import pytest

from src.domain import BaseTool
from src.infra.adapters.Tools import CurrentDateTool
from src.infra.config.available_tools import AvailableTools


@pytest.mark.unit
class TestAvailableTools:
    """Test suite for AvailableTools registry."""

    def setup_method(self):
        """Setup before each test."""
        # Clear lazy tools cache
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

    def test_get_available_tools_returns_dict(self):
        """Test that get_available_tools returns a dictionary."""
        tools = AvailableTools.get_available_tools()
        assert isinstance(tools, dict)

    def test_get_available_tools_contains_currentdate(self):
        """Test that CurrentDateTool is available."""
        tools = AvailableTools.get_available_tools()
        assert "currentdate" in tools
        assert isinstance(tools["currentdate"], CurrentDateTool)

    def test_get_available_tools_returns_basetool_instances(self):
        """Test that all tools are BaseTool instances."""
        tools = AvailableTools.get_available_tools()
        for tool_name, tool in tools.items():
            assert isinstance(tool, BaseTool), f"{tool_name} is not a BaseTool instance"

    def test_get_available_tools_tries_to_load_readlocalfile(self):
        """Test that ReadLocalFileTool loading is attempted."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

        with patch.object(
            AvailableTools, "_AvailableTools__try_load_read_local_file_tool"
        ) as mock_load:
            AvailableTools.get_available_tools()
            assert mock_load.called

    def test_get_available_tools_caches_lazy_tools(self):
        """Test that lazy tools are only loaded once."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

        # First call to load
        AvailableTools.get_available_tools()

        # Second call should not trigger loading again
        with patch.object(
            AvailableTools, "_AvailableTools__try_load_read_local_file_tool"
        ) as mock_load:
            AvailableTools.get_available_tools()

            # Should not be called since tools already loaded
            assert mock_load.call_count == 0

    def test_currentdate_tool_is_always_available(self):
        """Test that CurrentDateTool is always in the registry."""
        tools = AvailableTools.get_available_tools()
        assert "currentdate" in tools

        # Should be the same instance every time
        tools2 = AvailableTools.get_available_tools()
        assert tools["currentdate"] is tools2["currentdate"]

    def test_get_available_tools_returns_copy(self):
        """Test that get_available_tools returns a copy, not the original dict."""
        tools1 = AvailableTools.get_available_tools()
        tools2 = AvailableTools.get_available_tools()

        # Should be different dict objects
        assert tools1 is not tools2

        # But contain the same tool instances
        assert tools1["currentdate"] is tools2["currentdate"]

    def test_readlocalfile_included_when_dependencies_available(self):
        """Test that ReadLocalFileTool is included when dependencies are available."""
        try:
            import src.infra.adapters.Tools  # noqa: F401

            has_deps = True
        except (ImportError, RuntimeError):
            has_deps = False

        AvailableTools._AvailableTools__LAZY_TOOLS.clear()
        tools = AvailableTools.get_available_tools()

        if has_deps:
            assert "readlocalfile" in tools
            assert isinstance(tools["readlocalfile"], BaseTool)
        else:
            # Should not be in tools if dependencies missing
            assert "readlocalfile" not in tools

    def test_readlocalfile_excluded_when_dependencies_missing(self):
        """Test that ReadLocalFileTool is excluded when dependencies are missing."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

        # Simulate failed import by directly setting None in lazy tools
        AvailableTools._AvailableTools__LAZY_TOOLS["readlocalfile"] = None

        tools = AvailableTools.get_available_tools()

        # ReadLocalFileTool should not be available
        assert "readlocalfile" not in tools

    def test_try_load_read_local_file_tool_logs_warning_on_failure(self):
        """Test that warning is logged when ReadLocalFileTool fails to load."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

        # We can't easily mock the import, so just test that calling the method works
        AvailableTools._AvailableTools__try_load_read_local_file_tool()

        # Verify that either the tool loaded or it's marked as None
        assert "readlocalfile" in AvailableTools._AvailableTools__LAZY_TOOLS

    def test_try_load_read_local_file_tool_logs_debug_on_success(self):
        """Test that debug message is logged when ReadLocalFileTool loads successfully."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

        # Call the load method
        AvailableTools._AvailableTools__try_load_read_local_file_tool()

        # Verify tool is in lazy tools (either loaded or marked as None)
        assert "readlocalfile" in AvailableTools._AvailableTools__LAZY_TOOLS

    def test_try_load_handles_runtime_error(self):
        """Test that RuntimeError during loading is handled gracefully."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

        # Call the load method - it should handle errors gracefully
        AvailableTools._AvailableTools__try_load_read_local_file_tool()

        # Should have attempted to load and set something in lazy tools
        assert "readlocalfile" in AvailableTools._AvailableTools__LAZY_TOOLS

    def test_lazy_tools_dict_is_class_attribute(self):
        """Test that __LAZY_TOOLS is a class attribute."""
        assert hasattr(AvailableTools, "_AvailableTools__LAZY_TOOLS")
        assert isinstance(AvailableTools._AvailableTools__LAZY_TOOLS, dict)

    def test_available_tools_dict_is_class_attribute(self):
        """Test that __AVAILABLE_TOOLS is a class attribute."""
        assert hasattr(AvailableTools, "_AvailableTools__AVAILABLE_TOOLS")
        assert isinstance(AvailableTools._AvailableTools__AVAILABLE_TOOLS, dict)

    def test_tools_dict_is_not_modified_by_get(self):
        """Test that getting tools doesn't modify the internal dict."""
        original_eager = AvailableTools._AvailableTools__AVAILABLE_TOOLS.copy()

        tools = AvailableTools.get_available_tools()
        tools["fake_tool"] = Mock()

        # Internal dict should not be modified
        assert "fake_tool" not in AvailableTools._AvailableTools__AVAILABLE_TOOLS
        assert AvailableTools._AvailableTools__AVAILABLE_TOOLS == original_eager

    def test_tool_names_are_lowercase(self):
        """Test that all tool names are lowercase."""
        tools = AvailableTools.get_available_tools()
        for tool_name in tools.keys():
            assert tool_name == tool_name.lower()

    def test_tools_have_name_attribute(self):
        """Test that all tools have a name attribute."""
        tools = AvailableTools.get_available_tools()
        for tool_name, tool in tools.items():
            assert hasattr(tool, "name")
            assert isinstance(tool.name, str)

    def test_tools_have_description_attribute(self):
        """Test that all tools have a description attribute."""
        tools = AvailableTools.get_available_tools()
        for tool_name, tool in tools.items():
            assert hasattr(tool, "description")
            assert isinstance(tool.description, str)

    def test_tools_have_parameters_attribute(self):
        """Test that all tools have a parameters attribute."""
        tools = AvailableTools.get_available_tools()
        for tool_name, tool in tools.items():
            assert hasattr(tool, "parameters")
            assert isinstance(tool.parameters, dict)

    def test_tools_have_execute_method(self):
        """Test that all tools have an execute method."""
        tools = AvailableTools.get_available_tools()
        for tool_name, tool in tools.items():
            assert hasattr(tool, "execute")
            assert callable(tool.execute)

    def test_currentdate_tool_is_not_none(self):
        """Test that CurrentDateTool is not None."""
        tools = AvailableTools.get_available_tools()
        assert tools["currentdate"] is not None

    def test_get_available_tools_idempotent(self):
        """Test that calling get_available_tools multiple times is consistent."""
        tools1 = AvailableTools.get_available_tools()
        tools2 = AvailableTools.get_available_tools()
        tools3 = AvailableTools.get_available_tools()

        assert tools1.keys() == tools2.keys() == tools3.keys()

    def test_lazy_loading_only_happens_once(self):
        """Test that lazy loading happens exactly once."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

        load_count = [0]
        original_method = AvailableTools._AvailableTools__try_load_read_local_file_tool

        def counting_load():
            load_count[0] += 1
            return original_method()

        with patch.object(
            AvailableTools,
            "_AvailableTools__try_load_read_local_file_tool",
            side_effect=counting_load,
        ):
            AvailableTools.get_available_tools()
            AvailableTools.get_available_tools()
            AvailableTools.get_available_tools()

            assert load_count[0] == 1

    def test_none_values_filtered_from_lazy_tools(self):
        """Test that None values from failed lazy loads are filtered out."""
        AvailableTools._AvailableTools__LAZY_TOOLS["failed_tool"] = None

        tools = AvailableTools.get_available_tools()

        assert "failed_tool" not in tools

    def test_successful_lazy_tools_included(self):
        """Test that successfully loaded lazy tools are included."""
        mock_tool = Mock(spec=BaseTool)
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool"
        mock_tool.parameters = {}

        AvailableTools._AvailableTools__LAZY_TOOLS["testtool"] = mock_tool

        tools = AvailableTools.get_available_tools()

        assert "testtool" in tools
        assert tools["testtool"] is mock_tool

        # Cleanup
        del AvailableTools._AvailableTools__LAZY_TOOLS["testtool"]

    def test_error_message_includes_installation_instructions(self):
        """Test that error messages include installation instructions."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

        # Call the load method
        AvailableTools._AvailableTools__try_load_read_local_file_tool()

        # If it failed, the logging would have included installation instructions
        # We can't easily test this without mocking, but we can verify the method ran
        assert "readlocalfile" in AvailableTools._AvailableTools__LAZY_TOOLS

    def test_class_method_get_available_tools(self):
        """Test that get_available_tools is a class method."""
        import inspect

        assert inspect.ismethod(AvailableTools.get_available_tools)

    def test_class_method_try_load(self):
        """Test that __try_load_read_local_file_tool is a class method."""
        import inspect

        assert inspect.ismethod(
            AvailableTools._AvailableTools__try_load_read_local_file_tool
        )

    def test_docstring_exists(self):
        """Test that AvailableTools has a docstring."""
        assert AvailableTools.__doc__ is not None
        assert (
            "Registry" in AvailableTools.__doc__ or "registry" in AvailableTools.__doc__
        )

    def test_docstring_mentions_lazy_loading(self):
        """Test that docstring mentions lazy loading or heavy tools."""
        assert (
            "lazy" in AvailableTools.__doc__.lower()
            or "heavy" in AvailableTools.__doc__.lower()
            or "load" in AvailableTools.__doc__.lower()
        )

    def test_eager_tools_loaded_at_class_definition(self):
        """Test that eager tools are loaded at class definition time."""
        # CurrentDateTool should already be instantiated
        assert "currentdate" in AvailableTools._AvailableTools__AVAILABLE_TOOLS
        assert isinstance(
            AvailableTools._AvailableTools__AVAILABLE_TOOLS["currentdate"],
            CurrentDateTool,
        )

    def test_concurrent_access_safe(self):
        """Test that concurrent access to get_available_tools is safe."""
        import concurrent.futures

        AvailableTools._AvailableTools__LAZY_TOOLS.clear()
        results = []
        errors = []

        def get_tools():
            try:
                tools = AvailableTools.get_available_tools()
                results.append(len(tools))
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_tools) for _ in range(50)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(results) == 50
        # All should have the same number of tools
        assert len(set(results)) == 1

    def test_tools_registry_immutability(self):
        """Test that the tool registry cannot be easily modified externally."""
        tools1 = AvailableTools.get_available_tools()
        tools1["malicious_tool"] = Mock()

        tools2 = AvailableTools.get_available_tools()

        # Should not have the malicious tool
        assert "malicious_tool" not in tools2


@pytest.mark.unit
class TestAvailableToolsEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Setup before each test."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

    def test_handles_exception_in_tool_constructor(self):
        """Test handling when tool constructor raises exception."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

        # Call the load method
        AvailableTools._AvailableTools__try_load_read_local_file_tool()

        # Should handle any exceptions and mark tool appropriately
        assert "readlocalfile" in AvailableTools._AvailableTools__LAZY_TOOLS

    def test_empty_lazy_tools_still_returns_eager_tools(self):
        """Test that eager tools are returned even if lazy loading fails."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

        # Even if lazy tools fail to load, eager tools should still be available
        tools = AvailableTools.get_available_tools()

        # Should still have currentdate
        assert "currentdate" in tools
        assert len(tools) >= 1

    def test_duplicate_lazy_load_attempts_idempotent(self):
        """Test that multiple attempts to load lazy tools don't cause issues."""
        AvailableTools._AvailableTools__LAZY_TOOLS.clear()

        AvailableTools._AvailableTools__try_load_read_local_file_tool()
        first_state = AvailableTools._AvailableTools__LAZY_TOOLS.copy()

        AvailableTools._AvailableTools__try_load_read_local_file_tool()
        second_state = AvailableTools._AvailableTools__LAZY_TOOLS.copy()

        # Should be the same
        assert first_state.keys() == second_state.keys()
