"""
Tests for BaseTool abstract class and its contract.
"""

import pytest

from src.domain.value_objects.base_tools import BaseTool


class ConcreteTestTool(BaseTool):
    """Concrete implementation of BaseTool for testing."""

    name = "test_tool"
    description = "A tool for testing purposes"
    parameters = {
        "type": "object",
        "properties": {
            "input": {
                "type": "string",
                "description": "Test input",
            }
        },
        "required": ["input"],
    }

    def execute(self, input: str) -> str:
        """Execute the test tool."""
        return f"Executed with: {input}"


class MinimalTestTool(BaseTool):
    """Minimal implementation with default parameters."""

    name = "minimal_tool"
    description = "Minimal tool implementation"

    def execute(self) -> str:
        """Execute with no arguments."""
        return "Minimal execution"


class ComplexParametersTool(BaseTool):
    """Tool with complex parameter schema."""

    name = "complex_tool"
    description = "Tool with complex parameters"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {"type": "integer", "description": "Result limit", "default": 10},
            "filters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string"},
                            "end": {"type": "string"},
                        },
                    },
                },
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str, limit: int = 10, filters: dict = None) -> str:
        """Execute with complex parameters."""
        return f"Query: {query}, Limit: {limit}, Filters: {filters}"


@pytest.mark.unit
class TestBaseTool:
    """Test suite for BaseTool abstract class."""

    def test_cannot_instantiate_base_tool_directly(self):
        """Test that BaseTool cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseTool()

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that concrete implementations can be instantiated."""
        tool = ConcreteTestTool()

        assert isinstance(tool, BaseTool)
        assert tool.name == "test_tool"
        assert tool.description == "A tool for testing purposes"

    def test_execute_method_is_required(self):
        """Test that execute method must be implemented."""

        with pytest.raises(TypeError):

            class IncompleteToolNoExecute(BaseTool):
                name = "incomplete"
                description = "No execute method"

            IncompleteToolNoExecute()

    def test_name_attribute_is_accessible(self):
        """Test that name attribute is accessible."""
        tool = ConcreteTestTool()

        assert hasattr(tool, "name")
        assert isinstance(tool.name, str)
        assert tool.name == "test_tool"

    def test_description_attribute_is_accessible(self):
        """Test that description attribute is accessible."""
        tool = ConcreteTestTool()

        assert hasattr(tool, "description")
        assert isinstance(tool.description, str)
        assert tool.description == "A tool for testing purposes"

    def test_parameters_attribute_is_accessible(self):
        """Test that parameters attribute is accessible."""
        tool = ConcreteTestTool()

        assert hasattr(tool, "parameters")
        assert isinstance(tool.parameters, dict)
        assert "type" in tool.parameters
        assert "properties" in tool.parameters

    def test_default_parameters_schema(self):
        """Test that default parameters schema is valid."""
        tool = MinimalTestTool()

        assert tool.parameters == {"type": "object", "properties": {}}

    def test_execute_method_can_be_called(self):
        """Test that execute method can be called."""
        tool = ConcreteTestTool()

        result = tool.execute(input="test")

        assert result == "Executed with: test"
        assert isinstance(result, str)

    def test_execute_with_no_arguments(self):
        """Test execute method with no arguments."""
        tool = MinimalTestTool()

        result = tool.execute()

        assert result == "Minimal execution"

    def test_execute_with_multiple_arguments(self):
        """Test execute method with multiple arguments."""
        tool = ComplexParametersTool()

        result = tool.execute(
            query="search term", limit=5, filters={"category": "tech"}
        )

        assert "search term" in result
        assert "5" in result
        assert "tech" in result


@pytest.mark.unit
class TestGetSchema:
    """Test suite for get_schema method."""

    def test_get_schema_returns_dict(self):
        """Test that get_schema returns a dictionary."""
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert isinstance(schema, dict)

    def test_get_schema_contains_name(self):
        """Test that schema contains name field."""
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert "name" in schema
        assert schema["name"] == tool.name

    def test_get_schema_contains_description(self):
        """Test that schema contains description field."""
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert "description" in schema
        assert schema["description"] == tool.description

    def test_get_schema_contains_parameters(self):
        """Test that schema contains parameters field."""
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert "parameters" in schema
        assert schema["parameters"] == tool.parameters

    def test_get_schema_has_all_required_fields(self):
        """Test that schema has all required fields."""
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert set(schema.keys()) == {"name", "description", "parameters"}

    def test_get_schema_with_minimal_tool(self):
        """Test get_schema with minimal implementation."""
        tool = MinimalTestTool()

        schema = tool.get_schema()

        assert schema["name"] == "minimal_tool"
        assert schema["description"] == "Minimal tool implementation"
        assert schema["parameters"] == {"type": "object", "properties": {}}

    def test_get_schema_with_complex_parameters(self):
        """Test get_schema with complex parameter schema."""
        tool = ComplexParametersTool()

        schema = tool.get_schema()

        assert "query" in schema["parameters"]["properties"]
        assert "limit" in schema["parameters"]["properties"]
        assert "filters" in schema["parameters"]["properties"]
        assert "required" in schema["parameters"]
        assert "query" in schema["parameters"]["required"]

    def test_get_schema_returns_copy(self):
        """Test that get_schema returns a new dict each time."""
        tool = ConcreteTestTool()

        schema1 = tool.get_schema()
        schema2 = tool.get_schema()

        assert schema1 == schema2
        assert schema1 is not schema2

    def test_get_schema_can_be_modified_without_affecting_tool(self):
        """Test that modifying returned schema doesn't affect tool."""
        tool = ConcreteTestTool()

        schema = tool.get_schema()
        schema["name"] = "modified_name"

        assert tool.name == "test_tool"
        new_schema = tool.get_schema()
        assert new_schema["name"] == "test_tool"

    def test_get_schema_with_nested_parameters(self):
        """Test get_schema with deeply nested parameters."""
        tool = ComplexParametersTool()

        schema = tool.get_schema()
        filters = schema["parameters"]["properties"]["filters"]

        assert "properties" in filters
        assert "category" in filters["properties"]
        assert "date_range" in filters["properties"]


@pytest.mark.unit
class TestToolInheritance:
    """Test suite for tool inheritance patterns."""

    def test_multiple_tools_have_independent_schemas(self):
        """Test that different tools have independent schemas."""
        tool1 = ConcreteTestTool()
        tool2 = MinimalTestTool()

        schema1 = tool1.get_schema()
        schema2 = tool2.get_schema()

        assert schema1["name"] != schema2["name"]
        assert schema1["description"] != schema2["description"]

    def test_tool_can_be_subclassed_further(self):
        """Test that tools can be subclassed further."""

        class ExtendedTool(ConcreteTestTool):
            name = "extended_tool"
            description = "Extended version"

            def execute(self, input: str) -> str:
                """Extended execution."""
                return f"Extended: {super().execute(input)}"

        tool = ExtendedTool()

        assert tool.name == "extended_tool"
        result = tool.execute(input="test")
        assert "Extended" in result
        assert "Executed with: test" in result

    def test_tools_are_isinstance_of_basetool(self):
        """Test that all tools are instances of BaseTool."""
        tools = [
            ConcreteTestTool(),
            MinimalTestTool(),
            ComplexParametersTool(),
        ]

        for tool in tools:
            assert isinstance(tool, BaseTool)

    def test_tool_attributes_are_class_attributes(self):
        """Test that tool attributes are defined at class level."""
        assert hasattr(ConcreteTestTool, "name")
        assert hasattr(ConcreteTestTool, "description")
        assert hasattr(ConcreteTestTool, "parameters")

    def test_default_parameters_can_be_overridden(self):
        """Test that default parameters can be overridden."""

        class CustomParamsTool(BaseTool):
            name = "custom"
            description = "Custom parameters"
            parameters = {"type": "custom", "properties": {"x": {"type": "number"}}}

            def execute(self) -> str:
                return "custom"

        tool = CustomParamsTool()

        assert tool.parameters["type"] == "custom"
        assert "x" in tool.parameters["properties"]


@pytest.mark.unit
class TestToolParameterSchemas:
    """Test suite for parameter schema validation."""

    def test_parameters_follow_json_schema_structure(self):
        """Test that parameters follow JSON Schema structure."""
        tool = ConcreteTestTool()

        params = tool.parameters
        assert params["type"] == "object"
        assert isinstance(params["properties"], dict)

    def test_parameters_with_required_fields(self):
        """Test parameters with required fields."""
        tool = ConcreteTestTool()

        params = tool.parameters
        assert "required" in params
        assert isinstance(params["required"], list)
        assert "input" in params["required"]

    def test_parameters_with_optional_fields(self):
        """Test parameters with optional fields."""
        tool = ComplexParametersTool()

        params = tool.parameters
        required = params.get("required", [])
        all_props = params["properties"].keys()

        optional = set(all_props) - set(required)
        assert "limit" in optional or "filters" in optional

    def test_parameters_with_default_values(self):
        """Test parameters with default values."""
        tool = ComplexParametersTool()

        limit_param = tool.parameters["properties"]["limit"]
        assert "default" in limit_param
        assert limit_param["default"] == 10

    def test_parameters_with_nested_objects(self):
        """Test parameters with nested object structures."""
        tool = ComplexParametersTool()

        filters = tool.parameters["properties"]["filters"]
        assert filters["type"] == "object"
        assert "properties" in filters

        date_range = filters["properties"]["date_range"]
        assert date_range["type"] == "object"
        assert "properties" in date_range


@pytest.mark.unit
class TestToolExecution:
    """Test suite for tool execution behavior."""

    def test_execute_returns_value(self):
        """Test that execute returns a value."""
        tool = ConcreteTestTool()

        result = tool.execute(input="test")

        assert result is not None

    def test_execute_with_different_inputs(self):
        """Test execute with various input types."""
        tool = ConcreteTestTool()

        inputs = ["simple", "with spaces", "special!@#$%", "123", ""]
        for inp in inputs:
            result = tool.execute(input=inp)
            assert inp in result

    def test_execute_can_raise_exceptions(self):
        """Test that execute can raise exceptions for invalid input."""

        class StrictTool(BaseTool):
            name = "strict"
            description = "Raises on empty input"

            def execute(self, value: str) -> str:
                if not value:
                    raise ValueError("Value cannot be empty")
                return value

        tool = StrictTool()

        with pytest.raises(ValueError, match="cannot be empty"):
            tool.execute(value="")

    def test_execute_with_kwargs(self):
        """Test execute with keyword arguments."""
        tool = ComplexParametersTool()

        result = tool.execute(query="test", limit=20)

        assert "test" in result
        assert "20" in result

    def test_execute_with_default_arguments(self):
        """Test execute with default argument values."""
        tool = ComplexParametersTool()

        result = tool.execute(query="test")

        assert "test" in result
        assert "10" in result  # default limit


@pytest.mark.unit
class TestToolDocumentation:
    """Test suite for tool documentation and metadata."""

    def test_tool_has_docstring(self):
        """Test that tools can have docstrings."""
        tool = ConcreteTestTool()

        assert tool.__doc__ is not None or tool.execute.__doc__ is not None

    def test_description_is_informative(self):
        """Test that description provides information about tool."""
        tool = ConcreteTestTool()

        assert len(tool.description) > 10
        assert tool.description != "Base tool description (should be overridden)"

    def test_parameter_descriptions_exist(self):
        """Test that parameter descriptions exist."""
        tool = ConcreteTestTool()

        for prop in tool.parameters["properties"].values():
            assert "description" in prop
            assert len(prop["description"]) > 0

    def test_complex_tool_has_detailed_schema(self):
        """Test that complex tools have detailed schemas."""
        tool = ComplexParametersTool()

        schema = tool.get_schema()
        assert len(schema["parameters"]["properties"]) >= 3
        assert "required" in schema["parameters"]


@pytest.mark.unit
class TestToolEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_tool_with_empty_parameters(self):
        """Test tool with empty parameters."""

        class NoParamsTool(BaseTool):
            name = "no_params"
            description = "Tool with no parameters"
            parameters = {"type": "object", "properties": {}}

            def execute(self) -> str:
                return "no params"

        tool = NoParamsTool()
        schema = tool.get_schema()

        assert schema["parameters"]["properties"] == {}

    def test_tool_name_with_special_characters(self):
        """Test tool with special characters in name."""

        class SpecialNameTool(BaseTool):
            name = "special_tool_123"
            description = "Tool with special name"

            def execute(self) -> str:
                return "special"

        tool = SpecialNameTool()

        assert tool.name == "special_tool_123"
        assert "_" in tool.name
        assert "123" in tool.name

    def test_tool_with_long_description(self):
        """Test tool with very long description."""
        long_desc = "A" * 1000

        class LongDescTool(BaseTool):
            name = "long_desc"
            description = long_desc

            def execute(self) -> str:
                return "long"

        tool = LongDescTool()

        assert len(tool.description) == 1000
        assert tool.description == long_desc

    def test_tool_execute_returns_different_types(self):
        """Test that execute can return different types."""

        class StringTool(BaseTool):
            name = "string_tool"
            description = "Returns string"

            def execute(self) -> str:
                return "string result"

        class DictTool(BaseTool):
            name = "dict_tool"
            description = "Returns dict"

            def execute(self) -> dict:
                return {"key": "value"}

        string_tool = StringTool()
        dict_tool = DictTool()

        assert isinstance(string_tool.execute(), str)
        assert isinstance(dict_tool.execute(), dict)

    def test_multiple_tool_instances_are_independent(self):
        """Test that multiple instances are independent."""
        tool1 = ConcreteTestTool()
        tool2 = ConcreteTestTool()

        assert tool1 is not tool2
        assert tool1.name == tool2.name
        assert tool1.get_schema() == tool2.get_schema()
