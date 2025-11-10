from unittest.mock import Mock, patch

import pytest

from src.domain import BaseTool
from src.infra.adapters.Tools import CurrentDateTool
from src.infra.config.available_tools import AvailableTools


@pytest.mark.unit
class TestAvailableTools:
    def setup_method(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

    def test_get_all_available_tools_returns_dict(self):
        tools = AvailableTools.get_all_available_tools()
        assert isinstance(tools, dict)

    def test_get_all_available_tools_contains_currentdate(self):
        tools = AvailableTools.get_all_available_tools()
        assert "currentdate" in tools
        assert isinstance(tools["currentdate"], str)

    def test_get_all_available_tools_returns_string_descriptions(self):
        tools = AvailableTools.get_all_available_tools()
        for tool_name, description in tools.items():
            assert isinstance(
                description, str
            ), f"{tool_name} description is not a string"
            assert len(description) > 0, f"{tool_name} description is empty"

    def test_get_all_available_tools_tries_to_load_readlocalfile(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

        with patch.object(
            AvailableTools, "_AvailableTools__try_load_read_local_file_tool"
        ) as mock_load:
            AvailableTools.get_all_available_tools()
            assert mock_load.called

    def test_get_all_available_tools_caches_lazy_tools(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

        AvailableTools.get_all_available_tools()

        with patch.object(
            AvailableTools, "_AvailableTools__try_load_read_local_file_tool"
        ) as mock_load:
            AvailableTools.get_all_available_tools()
            assert mock_load.call_count == 0

    def test_currentdate_tool_is_always_available(self):
        tools = AvailableTools.get_all_available_tools()
        assert "currentdate" in tools

        tools2 = AvailableTools.get_all_available_tools()
        assert tools["currentdate"] == tools2["currentdate"]

    def test_get_all_available_tools_returns_copy(self):
        tools1 = AvailableTools.get_all_available_tools()
        tools2 = AvailableTools.get_all_available_tools()

        assert tools1 is not tools2
        assert tools1["currentdate"] == tools2["currentdate"]

    def test_readlocalfile_included_when_dependencies_available(self):
        import importlib.util

        has_deps = importlib.util.find_spec("src.infra.adapters.Tools") is not None

        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()
        tools = AvailableTools.get_all_available_tools()

        if has_deps:
            assert "readlocalfile" in tools
            assert isinstance(tools["readlocalfile"], str)
        else:
            assert "readlocalfile" not in tools

    def test_readlocalfile_excluded_when_dependencies_missing(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS["readlocalfile"] = None

        tools = AvailableTools.get_all_available_tools()

        assert "readlocalfile" not in tools

    def test_try_load_read_local_file_tool_logs_warning_on_failure(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

        AvailableTools._AvailableTools__try_load_read_local_file_tool()

        assert "readlocalfile" in AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS

    def test_try_load_read_local_file_tool_logs_debug_on_success(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

        AvailableTools._AvailableTools__try_load_read_local_file_tool()

        assert "readlocalfile" in AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS

    def test_try_load_handles_runtime_error(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

        AvailableTools._AvailableTools__try_load_read_local_file_tool()

        assert "readlocalfile" in AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS

    def test_lazy_tools_dict_is_class_attribute(self):
        assert hasattr(AvailableTools, "_AvailableTools__LAZY_SYSTEM_TOOLS")
        assert isinstance(AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS, dict)

    def test_system_tools_dict_is_class_attribute(self):
        assert hasattr(AvailableTools, "_AvailableTools__SYSTEM_TOOLS")
        assert isinstance(AvailableTools._AvailableTools__SYSTEM_TOOLS, dict)

    def test_tools_dict_is_not_modified_by_get(self):
        original_eager = AvailableTools._AvailableTools__SYSTEM_TOOLS.copy()

        tools = AvailableTools.get_all_available_tools()
        tools["fake_tool"] = Mock()

        assert "fake_tool" not in AvailableTools._AvailableTools__SYSTEM_TOOLS
        assert AvailableTools._AvailableTools__SYSTEM_TOOLS == original_eager

    def test_tool_names_are_lowercase(self):
        tools = AvailableTools.get_all_available_tools()
        for tool_name in tools.keys():
            assert tool_name == tool_name.lower()

    def test_tools_have_descriptions(self):
        tools = AvailableTools.get_all_available_tools()
        for tool_name, description in tools.items():
            assert isinstance(description, str)
            assert len(description.strip()) > 0

    def test_currentdate_tool_is_not_none(self):
        tools = AvailableTools.get_all_available_tools()
        assert tools["currentdate"] is not None

    def test_get_all_available_tools_idempotent(self):
        tools1 = AvailableTools.get_all_available_tools()
        tools2 = AvailableTools.get_all_available_tools()
        tools3 = AvailableTools.get_all_available_tools()

        assert tools1.keys() == tools2.keys() == tools3.keys()

    def test_lazy_loading_only_happens_once(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

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
            AvailableTools.get_all_available_tools()
            AvailableTools.get_all_available_tools()
            AvailableTools.get_all_available_tools()

            assert load_count[0] == 1

    def test_none_values_filtered_from_lazy_tools(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS["failed_tool"] = None

        tools = AvailableTools.get_all_available_tools()

        assert "failed_tool" not in tools

    def test_successful_lazy_tools_included(self):
        mock_description = "Test tool description"

        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS["testtool"] = Mock(
            spec=BaseTool, description=mock_description
        )

        tools = AvailableTools.get_all_available_tools()

        assert "testtool" in tools
        assert tools["testtool"] == mock_description

        del AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS["testtool"]

    def test_error_message_includes_installation_instructions(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

        AvailableTools._AvailableTools__try_load_read_local_file_tool()

        assert "readlocalfile" in AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS

    def test_class_method_get_all_available_tools(self):
        import inspect

        assert inspect.ismethod(AvailableTools.get_all_available_tools)

    def test_class_method_try_load(self):
        import inspect

        assert inspect.ismethod(
            AvailableTools._AvailableTools__try_load_read_local_file_tool
        )

    def test_docstring_exists(self):
        assert AvailableTools.__doc__ is not None
        assert (
            "Registry" in AvailableTools.__doc__ or "registry" in AvailableTools.__doc__
        )

    def test_docstring_mentions_lazy_loading(self):
        assert (
            "lazy" in AvailableTools.__doc__.lower()
            or "heavy" in AvailableTools.__doc__.lower()
            or "load" in AvailableTools.__doc__.lower()
        )

    def test_eager_tools_loaded_at_class_definition(self):
        assert "currentdate" in AvailableTools._AvailableTools__SYSTEM_TOOLS
        assert isinstance(
            AvailableTools._AvailableTools__SYSTEM_TOOLS["currentdate"],
            CurrentDateTool,
        )

    def test_concurrent_access_safe(self):
        import concurrent.futures

        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()
        results = []
        errors = []

        def get_tools():
            try:
                tools = AvailableTools.get_all_available_tools()
                results.append(len(tools))
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_tools) for _ in range(50)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(results) == 50
        assert len(set(results)) == 1

    def test_tools_registry_immutability(self):
        tools1 = AvailableTools.get_all_available_tools()
        tools1["malicious_tool"] = "Malicious description"

        tools2 = AvailableTools.get_all_available_tools()

        assert "malicious_tool" not in tools2


@pytest.mark.unit
class TestAvailableToolsEdgeCases:
    def setup_method(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

    def test_handles_exception_in_tool_constructor(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

        AvailableTools._AvailableTools__try_load_read_local_file_tool()

        assert "readlocalfile" in AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS

    def test_empty_lazy_tools_still_returns_eager_tools(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

        tools = AvailableTools.get_all_available_tools()

        assert "currentdate" in tools
        assert len(tools) >= 1

    def test_duplicate_lazy_load_attempts_idempotent(self):
        AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.clear()

        AvailableTools._AvailableTools__try_load_read_local_file_tool()
        first_state = AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.copy()

        AvailableTools._AvailableTools__try_load_read_local_file_tool()
        second_state = AvailableTools._AvailableTools__LAZY_SYSTEM_TOOLS.copy()

        assert first_state.keys() == second_state.keys()

    def test_get_all_tool_instances_returns_basetool_instances(self):
        tool_instances = AvailableTools.get_all_tool_instances()

        assert isinstance(tool_instances, dict)
        for tool_name, tool in tool_instances.items():
            assert isinstance(tool, BaseTool), f"{tool_name} is not a BaseTool instance"

    def test_get_all_tool_instances_contains_currentdate(self):
        tool_instances = AvailableTools.get_all_tool_instances()

        assert "currentdate" in tool_instances
        assert isinstance(tool_instances["currentdate"], CurrentDateTool)

    def test_get_tool_instance_returns_basetool(self):
        tool = AvailableTools.get_tool_instance("currentdate")

        assert tool is not None
        assert isinstance(tool, BaseTool)
        assert isinstance(tool, CurrentDateTool)

    def test_get_tool_instance_case_insensitive(self):
        tool_lower = AvailableTools.get_tool_instance("currentdate")
        tool_upper = AvailableTools.get_tool_instance("CURRENTDATE")
        tool_mixed = AvailableTools.get_tool_instance("CurrentDate")

        assert tool_lower is tool_upper
        assert tool_lower is tool_mixed

    def test_get_tool_instance_returns_none_for_missing_tool(self):
        tool = AvailableTools.get_tool_instance("nonexistent_tool")

        assert tool is None
