from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple, Union

import pytest
from pydantic import BaseModel, ValidationError

from createagents.domain.value_objects import (
    InjectedState,
    InjectedToolArg,
    InjectedToolCallId,
)
from createagents.domain.value_objects.utils.schemas import (
    _filter_injected_args,
    _get_base_type,
    _get_short_description,
    _parse_google_docstring,
    _python_type_to_json_type,
    create_schema_from_function,
    get_json_schema_from_function,
)


@pytest.mark.unit
class TestGetBaseType:
    def test_simple_type_returns_itself(self):
        assert _get_base_type(str) is str
        assert _get_base_type(int) is int
        assert _get_base_type(float) is float
        assert _get_base_type(bool) is bool

    def test_annotated_type_returns_base(self):
        annotated_str = Annotated[str, 'some metadata']
        assert _get_base_type(annotated_str) is str

        annotated_int = Annotated[int, InjectedToolArg]
        assert _get_base_type(annotated_int) is int

    def test_annotated_with_multiple_metadata(self):
        withplex_annotated = Annotated[
            Dict[str, int], 'meta1', 'meta2', 'meta3'
        ]
        base = _get_base_type(withplex_annotated)
        assert base == Dict[str, int]

    def test_nested_generic_type(self):
        list_type = List[str]
        assert _get_base_type(list_type) == list_type

        dict_type = Dict[str, List[int]]
        assert _get_base_type(dict_type) == dict_type

    def test_optional_type(self):
        optional_type = Optional[str]
        assert _get_base_type(optional_type) == optional_type

    def test_union_type(self):
        union_type = Union[int, str]
        assert _get_base_type(union_type) == union_type


@pytest.mark.unit
class TestParseGoogleDocstring:
    def test_parse_simple_docstring(self):
        def simple_func(name: str, age: int) -> str:
            """Get person info.

            Args:
                name: Name da pessoa.
                age: Age da pessoa.

            Returns:
                Info string.
            """
            return f'{name}: {age}'

        descriptions = _parse_google_docstring(simple_func)

        assert 'name' in descriptions
        assert 'Name da pessoa' in descriptions['name']
        assert 'age' in descriptions
        assert 'Age da pessoa' in descriptions['age']

    def test_parse_multiline_descriptions(self):
        def multiline_func(data: str) -> str:
            """Process data.

            Args:
                data: Descricao dos dados
                    que continua em outra linha.

            Returns:
                Processed data.
            """
            return data

        descriptions = _parse_google_docstring(multiline_func)

        assert 'data' in descriptions
        assert 'descricao' in descriptions['data'].lower()

    def test_parse_empty_docstring(self):
        def empty_doc() -> None:
            pass

        descriptions = _parse_google_docstring(empty_doc)
        assert descriptions == {}

    def test_parse_no_docstring(self):
        def no_doc() -> None:
            pass

        descriptions = _parse_google_docstring(no_doc)
        assert descriptions == {}

    def test_parse_docstring_without_args_section(self):
        def no_args_section(x: int) -> int:
            return x

        descriptions = _parse_google_docstring(no_args_section)
        assert descriptions == {}

    def test_parse_malformed_docstring(self):
        def malformed(x: int) -> int:
            return x

        descriptions = _parse_google_docstring(malformed)
        assert isinstance(descriptions, dict)

    def test_parse_with_types_in_docstring(self):
        def typed_docstring(name: str, count: int) -> str:
            """Get typed info.

            Args:
                name: The name parameter.
                count: The count parameter.

            Returns:
                Combined string.
            """
            return f'{name}: {count}'

        descriptions = _parse_google_docstring(typed_docstring)

        assert 'name' in descriptions
        assert 'count' in descriptions

    def test_parse_with_special_characters(self):
        def special_chars(path: str, regex: str) -> str:
            """Process paths and regex.

            Args:
                path: File path like /home/user/file.
                regex: Pattern like ^[a-z]+ for matching.

            Returns:
                Combined result.
            """
            return f'{path}: {regex}'

        descriptions = _parse_google_docstring(special_chars)

        assert 'path' in descriptions
        assert '/home' in descriptions['path']
        assert 'regex' in descriptions
        assert '^[a-z]' in descriptions['regex']


@pytest.mark.unit
class TestGetShortDescription:
    def test_extracts_first_line(self):
        def func():
            """Esta e a first line.

            More details here.
            """
            pass

        desc = _get_short_description(func)
        assert desc == 'Esta e a first line.'

    def test_empty_docstring_returns_empty_string(self):
        def func():
            pass

        desc = _get_short_description(func)
        assert desc == ''

    def test_no_docstring_returns_empty_string(self):
        def func():
            pass

        desc = _get_short_description(func)
        assert desc == ''

    def test_single_line_docstring(self):
        def func():
            """Docstring de uma linha apenas."""
            pass

        desc = _get_short_description(func)
        assert desc == 'Docstring de uma linha apenas.'

    def test_strips_whitespace(self):
        def func():
            """Descricao with spaces."""
            pass

        desc = _get_short_description(func)
        assert desc == 'Descricao with spaces.'


@pytest.mark.unit
class TestFilterInjectedArgs:
    def test_no_injected_args(self):
        type_hints = {
            'name': str,
            'age': int,
            'active': bool,
        }

        regular, injected = _filter_injected_args(type_hints)

        assert regular == type_hints
        assert injected == {}

    def test_filters_injected_tool_arg(self):
        type_hints = {
            'query': str,
            'internal': Annotated[str, InjectedToolArg],
        }

        regular, injected = _filter_injected_args(type_hints)

        assert 'query' in regular
        assert 'internal' not in regular
        assert 'internal' in injected

    def test_filters_injected_tool_call_id(self):
        type_hints = {
            'data': str,
            'call_id': Annotated[str, InjectedToolCallId],
        }

        regular, injected = _filter_injected_args(type_hints)

        assert 'data' in regular
        assert 'call_id' not in regular
        assert 'call_id' in injected

    def test_filters_injected_state(self):
        type_hints = {
            'action': str,
            'state': Annotated[Dict[str, Any], InjectedState],
        }

        regular, injected = _filter_injected_args(type_hints)

        assert 'action' in regular
        assert 'state' not in regular
        assert 'state' in injected

    def test_filters_multiple_injected_args(self):
        type_hints = {
            'query': str,
            'call_id': Annotated[str, InjectedToolCallId],
            'state': Annotated[Dict[str, Any], InjectedState],
            'custom': Annotated[int, InjectedToolArg],
        }

        regular, injected = _filter_injected_args(type_hints)

        assert len(regular) == 1
        assert 'query' in regular
        assert len(injected) == 3

    def test_ignores_return_type(self):
        type_hints = {
            'x': int,
            'return': str,
        }

        regular, injected = _filter_injected_args(type_hints)

        assert 'return' not in regular
        assert 'return' not in injected
        assert 'x' in regular

    def test_custom_injected_marker(self):
        class CustomInjected(InjectedToolArg):
            pass

        type_hints = {
            'data': str,
            'custom': Annotated[int, CustomInjected],
        }

        regular, injected = _filter_injected_args(type_hints)

        assert 'data' in regular
        assert 'custom' in injected


@pytest.mark.unit
class TestPythonTypeToJsonType:
    def test_string_type(self):
        assert _python_type_to_json_type(str) == 'string'

    def test_int_type(self):
        assert _python_type_to_json_type(int) == 'integer'

    def test_float_type(self):
        assert _python_type_to_json_type(float) == 'number'

    def test_bool_type(self):
        assert _python_type_to_json_type(bool) == 'boolean'

    def test_list_type(self):
        assert _python_type_to_json_type(list) == 'array'
        assert _python_type_to_json_type(List[str]) == 'array'
        assert _python_type_to_json_type(List[int]) == 'array'

    def test_dict_type(self):
        assert _python_type_to_json_type(dict) == 'object'
        assert _python_type_to_json_type(Dict[str, int]) == 'object'

    def test_none_type(self):
        assert _python_type_to_json_type(type(None)) == 'null'

    def test_tuple_type(self):
        assert _python_type_to_json_type(tuple) == 'array'
        assert _python_type_to_json_type(Tuple[int, str]) == 'array'

    def test_set_type(self):
        assert _python_type_to_json_type(set) == 'array'
        assert _python_type_to_json_type(frozenset) == 'array'

    def test_optional_type(self):
        assert _python_type_to_json_type(Optional[str]) == 'string'
        assert _python_type_to_json_type(Optional[int]) == 'integer'

    def test_union_type(self):
        assert _python_type_to_json_type(Union[str, int]) == 'string'
        assert _python_type_to_json_type(Union[int, str]) == 'integer'

    def test_unknown_type_returns_string(self):
        class CustomClass:
            pass

        assert _python_type_to_json_type(CustomClass) == 'string'
        assert _python_type_to_json_type(Any) == 'string'


@pytest.mark.unit
class TestCreateSchemaFromFunction:
    def test_creates_pydantic_model(self):
        def simple_func(name: str, age: int) -> str:
            return f'{name}: {age}'

        Model = create_schema_from_function(simple_func)

        assert issubclass(Model, BaseModel)

    def test_model_validates_correct_input(self):
        def typed_func(x: int, y: str) -> str:
            return f'{x}: {y}'

        Model = create_schema_from_function(typed_func)

        instance = Model(x=10, y='test')
        assert instance.x == 10
        assert instance.y == 'test'

    def test_model_rejects_invalid_input(self):
        def strict_func(value: int) -> int:
            return value

        Model = create_schema_from_function(strict_func)

        with pytest.raises(ValidationError):
            Model(value='not an integer')

    def test_model_has_default_values(self):
        def with_defaults(
            name: str, count: int = 10, active: bool = True
        ) -> str:
            return name

        Model = create_schema_from_function(with_defaults)

        instance = Model(name='test')
        assert instance.name == 'test'
        assert instance.count == 10
        assert instance.active is True

    def test_model_has_field_descriptions(self):
        def documented(query: str, limit: int = 10) -> str:
            """Search for something.

            Args:
                query: The search query to execute.
                limit: Maximum number of results.

            Returns:
                Search results.
            """
            return query

        Model = create_schema_from_function(documented)
        schema = Model.model_json_schema()

        assert 'query' in schema['properties']
        assert 'description' in schema['properties']['query']
        assert 'query' in schema['properties']['query']['description'].lower()

    def test_filters_injected_args_by_default(self):
        def with_injection(
            query: str,
            call_id: Annotated[str, InjectedToolCallId],
        ) -> str:
            return query

        Model = create_schema_from_function(with_injection)
        schema = Model.model_json_schema()

        assert 'query' in schema['properties']
        assert 'call_id' not in schema['properties']

    def test_can_disable_injected_filtering(self):
        def with_injection(
            query: str,
            call_id: Annotated[str, InjectedToolCallId],
        ) -> str:
            return query

        Model = create_schema_from_function(
            with_injection, filter_injected=False
        )
        schema = Model.model_json_schema()

        assert 'query' in schema['properties']
        assert 'call_id' in schema['properties']

    def test_can_disable_docstring_parsing(self):
        def documented(query: str) -> str:
            return query

        Model = create_schema_from_function(documented, parse_docstring=False)
        schema = Model.model_json_schema()

        assert 'query' in schema['properties']
        desc = schema['properties']['query'].get('description', '')
        assert 'detalhada' not in desc.lower()

    def test_custom_model_name(self):
        def func(x: int) -> int:
            return x

        Model = create_schema_from_function(
            func, model_name='CustomInputModel'
        )

        assert Model.__name__ == 'CustomInputModel'

    def test_default_model_name_from_function(self):
        def my_awesome_function(x: int) -> int:
            return x

        Model = create_schema_from_function(my_awesome_function)

        assert 'MyAwesomeFunction' in Model.__name__

    def test_handles_function_without_type_hints(self):
        def untyped(name, age):
            return f'{name}: {age}'

        Model = create_schema_from_function(untyped)
        schema = Model.model_json_schema()

        assert 'name' in schema['properties']
        assert 'age' in schema['properties']

    def test_handles_withplex_types(self):
        def withplex_func(
            items: List[str],
            data: Dict[str, int],
            optional: Optional[str] = None,
            union: Union[int, str] = 0,
        ) -> str:
            return str(items)

        Model = create_schema_from_function(withplex_func)
        schema = Model.model_json_schema()

        assert 'items' in schema['properties']
        assert 'data' in schema['properties']
        assert 'optional' in schema['properties']
        assert 'union' in schema['properties']

    def test_ignores_self_and_cls(self):
        class MyClass:
            def method(self, x: int) -> int:
                return x

            @classmethod
            def class_method(cls, y: str) -> str:
                return y

        instance = MyClass()
        Model1 = create_schema_from_function(instance.method)
        Model2 = create_schema_from_function(MyClass.class_method)

        schema1 = Model1.model_json_schema()
        schema2 = Model2.model_json_schema()

        assert 'self' not in schema1['properties']
        assert 'x' in schema1['properties']

        assert 'cls' not in schema2['properties']
        assert 'y' in schema2['properties']

    def test_ignores_args_kwargs(self):
        def varargs(x: int, *args, **kwargs) -> int:
            return x

        Model = create_schema_from_function(varargs)
        schema = Model.model_json_schema()

        assert 'x' in schema['properties']
        assert len(schema['properties']) == 1


@pytest.mark.unit
class TestGetJsonSchemaFromFunction:
    def test_returns_dict(self):
        def func(x: int) -> int:
            return x

        schema = get_json_schema_from_function(func)

        assert isinstance(schema, dict)

    def test_schema_has_properties(self):
        def func(name: str, age: int) -> str:
            return name

        schema = get_json_schema_from_function(func)

        assert 'properties' in schema
        assert 'name' in schema['properties']
        assert 'age' in schema['properties']

    def test_schema_has_required(self):
        def func(required: str, optional: int = 10) -> str:
            return required

        schema = get_json_schema_from_function(func)

        assert 'required' in schema
        assert 'required' in schema['required']

    def test_schema_is_json_serializable(self):
        import json

        def withplex_func(
            name: str, items: List[str], data: Optional[Dict[str, int]] = None
        ) -> str:
            return name

        schema = get_json_schema_from_function(withplex_func)

        json_str = json.dumps(schema)
        assert isinstance(json_str, str)

    def test_filters_injected_args(self):
        def with_injection(
            query: str,
            state: Annotated[Dict[str, Any], InjectedState],
        ) -> str:
            return query

        schema = get_json_schema_from_function(with_injection)

        assert 'query' in schema['properties']
        assert 'state' not in schema['properties']

    def test_includes_field_descriptions(self):
        def documented(search_query: str) -> str:
            """Search for results.

            Args:
                search_query: The search query to execute.

            Returns:
                Results.
            """
            return search_query

        schema = get_json_schema_from_function(documented)

        assert 'description' in schema['properties']['search_query']
        assert (
            'query'
            in schema['properties']['search_query']['description'].lower()
        )


@pytest.mark.unit
class TestSchemaUtilsIntegration:
    def test_lambda_function(self):
        def double(x: int) -> int:
            return x * 2

        Model = create_schema_from_function(double)
        assert issubclass(Model, BaseModel)

    def test_empty_function(self):
        def no_params() -> str:
            return 'constant'

        Model = create_schema_from_function(no_params)
        schema = Model.model_json_schema()

        assert schema['properties'] == {}

    def test_all_optional_params(self):
        def all_optional(x: int = 1, y: int = 2, z: int = 3) -> int:
            return x + y + z

        Model = create_schema_from_function(all_optional)
        schema = Model.model_json_schema()

        required = schema.get('required', [])
        assert len(required) == 0

    def test_literal_type(self):
        def with_literal(action: Literal['start', 'stop', 'pause']) -> str:
            return action

        Model = create_schema_from_function(with_literal)
        schema = Model.model_json_schema()

        assert 'action' in schema['properties']

    def test_nested_annotated(self):
        def with_nested(
            value: Annotated[Annotated[int, 'inner'], 'outer'],
        ) -> int:
            return value

        Model = create_schema_from_function(with_nested)
        assert issubclass(Model, BaseModel)

    def test_preserves_type_in_schema(self):
        def typed(
            string_val: str,
            int_val: int,
            float_val: float,
            bool_val: bool,
            list_val: List[str],
        ) -> str:
            return string_val

        schema = get_json_schema_from_function(typed)
        props = schema['properties']

        assert props['string_val']['type'] == 'string'
        assert props['int_val']['type'] == 'integer'
        assert props['float_val']['type'] == 'number'
        assert props['bool_val']['type'] == 'boolean'
        assert props['list_val']['type'] == 'array'
