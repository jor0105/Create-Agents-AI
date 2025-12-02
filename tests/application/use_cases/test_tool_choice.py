from __future__ import annotations

import pytest

from createagents.domain.value_objects import (
    ToolChoice,
    ToolChoiceMode,
)


@pytest.mark.unit
class TestToolChoiceMode:
    def test_auto_mode_value(self):
        assert ToolChoiceMode.AUTO.value == 'auto'

    def test_none_mode_value(self):
        assert ToolChoiceMode.NONE.value == 'none'

    def test_required_mode_value(self):
        assert ToolChoiceMode.REQUIRED.value == 'required'

    def test_mode_is_string_enum(self):
        assert isinstance(ToolChoiceMode.AUTO, str)
        assert ToolChoiceMode.AUTO == 'auto'

    def test_all_modes_exist(self):
        modes = list(ToolChoiceMode)
        assert len(modes) == 3
        assert ToolChoiceMode.AUTO in modes
        assert ToolChoiceMode.NONE in modes
        assert ToolChoiceMode.REQUIRED in modes


@pytest.mark.unit
class TestToolChoiceFactoryMethods:
    def test_auto_creates_auto_mode(self):
        choice = ToolChoice.auto()

        assert choice.mode == ToolChoiceMode.AUTO
        assert choice.function_name is None

    def test_none_creates_none_mode(self):
        choice = ToolChoice.none()

        assert choice.mode == ToolChoiceMode.NONE
        assert choice.function_name is None

    def test_required_creates_required_mode(self):
        choice = ToolChoice.required()

        assert choice.mode == ToolChoiceMode.REQUIRED
        assert choice.function_name is None

    def test_for_function_creates_specific_mode(self):
        choice = ToolChoice.for_function('search')

        assert choice.mode == 'specific'
        assert choice.function_name == 'search'

    def test_for_function_with_different_names(self):
        names = ['search', 'calculator', 'weather_lookup', 'tool_v2']

        for name in names:
            choice = ToolChoice.for_function(name)
            assert choice.function_name == name


@pytest.mark.unit
class TestToolChoiceFromValue:
    def test_none_value_returns_none(self):
        result = ToolChoice.from_value(None)
        assert result is None

    def test_auto_string_creates_auto_mode(self):
        choice = ToolChoice.from_value('auto')

        assert choice is not None
        assert choice.mode == ToolChoiceMode.AUTO

    def test_none_string_creates_none_mode(self):
        choice = ToolChoice.from_value('none')

        assert choice is not None
        assert choice.mode == ToolChoiceMode.NONE

    def test_required_string_creates_required_mode(self):
        choice = ToolChoice.from_value('required')

        assert choice is not None
        assert choice.mode == ToolChoiceMode.REQUIRED

    def test_tool_name_string_with_available_tools(self):
        available_tools = ['search', 'calculator', 'weather']

        choice = ToolChoice.from_value('search', available_tools)

        assert choice is not None
        assert choice.function_name == 'search'

    def test_invalid_string_raises_error(self):
        with pytest.raises(ValueError, match='Invalid tool_choice'):
            ToolChoice.from_value('invalid_mode')

    def test_invalid_string_without_available_tools(self):
        with pytest.raises(ValueError, match='Invalid tool_choice'):
            ToolChoice.from_value('unknown_tool', available_tools=None)

    def test_dict_format_with_function(self):
        value = {
            'type': 'function',
            'function': {'name': 'search'},
        }

        choice = ToolChoice.from_value(value)

        assert choice is not None
        assert choice.function_name == 'search'

    def test_invalid_type_raises_error(self):
        with pytest.raises(ValueError, match='Invalid tool_choice type'):
            ToolChoice.from_value(123)

        with pytest.raises(ValueError, match='Invalid tool_choice type'):
            ToolChoice.from_value(['auto'])


@pytest.mark.unit
class TestToolChoiceParseDict:
    def test_valid_dict_format(self):
        value = {
            'type': 'function',
            'function': {'name': 'calculator'},
        }

        choice = ToolChoice._parse_dict(value)

        assert choice.function_name == 'calculator'

    def test_missing_type_raises_error(self):
        value = {'function': {'name': 'search'}}

        with pytest.raises(ValueError, match="must contain 'type' key"):
            ToolChoice._parse_dict(value)

    def test_invalid_type_value_raises_error(self):
        value = {'type': 'invalid', 'function': {'name': 'search'}}

        with pytest.raises(ValueError, match="'type' must be 'function'"):
            ToolChoice._parse_dict(value)

    def test_missing_function_key_raises_error(self):
        value = {'type': 'function'}

        with pytest.raises(ValueError, match="must contain 'function' key"):
            ToolChoice._parse_dict(value)

    def test_invalid_function_spec_raises_error(self):
        value1 = {'type': 'function', 'function': 'search'}

        with pytest.raises(ValueError, match="must be a dict with 'name' key"):
            ToolChoice._parse_dict(value1)

        value2 = {'type': 'function', 'function': {'description': 'search'}}

        with pytest.raises(ValueError, match="must be a dict with 'name' key"):
            ToolChoice._parse_dict(value2)


@pytest.mark.unit
class TestToolChoiceValidateAgainstTools:
    def test_auto_mode_always_valid(self):
        choice = ToolChoice.auto()
        tool_names = {'search', 'calculator'}

        choice.validate_against_tools(tool_names)

    def test_none_mode_always_valid(self):
        choice = ToolChoice.none()
        tool_names = {'search', 'calculator'}

        choice.validate_against_tools(tool_names)

    def test_required_mode_always_valid(self):
        choice = ToolChoice.required()
        tool_names = {'search', 'calculator'}

        choice.validate_against_tools(tool_names)

    def test_specific_function_valid_when_exists(self):
        choice = ToolChoice.for_function('search')
        tool_names = {'search', 'calculator', 'weather'}

        choice.validate_against_tools(tool_names)

    def test_specific_function_invalid_when_not_exists(self):
        choice = ToolChoice.for_function('nonexistent')
        tool_names = {'search', 'calculator'}

        with pytest.raises(ValueError, match="unknown tool 'nonexistent'"):
            choice.validate_against_tools(tool_names)

    def test_specific_function_with_empty_tools(self):
        choice = ToolChoice.for_function('search')
        tool_names = set()

        with pytest.raises(ValueError, match="unknown tool 'search'"):
            choice.validate_against_tools(tool_names)

    def test_error_message_lists_available_tools(self):
        choice = ToolChoice.for_function('nonexistent')
        tool_names = {'search', 'calculator'}

        try:
            choice.validate_against_tools(tool_names)
            assert False, 'Should have raised ValueError'
        except ValueError as e:
            error_msg = str(e)
            assert 'calculator' in error_msg
            assert 'search' in error_msg


@pytest.mark.unit
class TestToolChoiceToOpenAIFormat:
    def test_auto_mode_returns_string(self):
        choice = ToolChoice.auto()

        result = choice.to_openai_format()

        assert result == 'auto'

    def test_none_mode_returns_string(self):
        choice = ToolChoice.none()

        result = choice.to_openai_format()

        assert result == 'none'

    def test_required_mode_returns_string(self):
        choice = ToolChoice.required()

        result = choice.to_openai_format()

        assert result == 'required'

    def test_specific_function_returns_dict(self):
        choice = ToolChoice.for_function('search')

        result = choice.to_openai_format()

        assert isinstance(result, dict)
        assert result['type'] == 'function'
        assert result['function']['name'] == 'search'

    def test_specific_function_format_is_valid(self):
        choice = ToolChoice.for_function('calculator')

        result = choice.to_openai_format()

        assert 'type' in result
        assert 'function' in result
        assert 'name' in result['function']
        assert result['function']['name'] == 'calculator'


@pytest.mark.unit
class TestToolChoiceToDict:
    def test_auto_mode_serializes(self):
        choice = ToolChoice.auto()

        result = choice.to_dict()

        assert result == {'mode': 'auto'}

    def test_none_mode_serializes(self):
        choice = ToolChoice.none()

        result = choice.to_dict()

        assert result == {'mode': 'none'}

    def test_required_mode_serializes(self):
        choice = ToolChoice.required()

        result = choice.to_dict()

        assert result == {'mode': 'required'}

    def test_specific_function_serializes(self):
        choice = ToolChoice.for_function('search')

        result = choice.to_dict()

        assert result['mode'] == 'specific'
        assert result['function_name'] == 'search'

    def test_to_dict_is_json_serializable(self):
        import json

        choices = [
            ToolChoice.auto(),
            ToolChoice.none(),
            ToolChoice.required(),
            ToolChoice.for_function('test'),
        ]

        for choice in choices:
            json_str = json.dumps(choice.to_dict())
            assert isinstance(json_str, str)


@pytest.mark.unit
class TestToolChoiceIsSpecificFunction:
    def test_auto_is_not_specific(self):
        choice = ToolChoice.auto()
        assert choice.is_specific_function is False

    def test_none_is_not_specific(self):
        choice = ToolChoice.none()
        assert choice.is_specific_function is False

    def test_required_is_not_specific(self):
        choice = ToolChoice.required()
        assert choice.is_specific_function is False

    def test_for_function_is_specific(self):
        choice = ToolChoice.for_function('search')
        assert choice.is_specific_function is True


@pytest.mark.unit
class TestToolChoiceImmutability:
    def test_toolchoice_is_frozen_dataclass(self):
        choice = ToolChoice.auto()

        with pytest.raises((AttributeError, TypeError)):
            choice.mode = ToolChoiceMode.NONE

    def test_cannot_modify_function_name(self):
        choice = ToolChoice.for_function('search')

        with pytest.raises((AttributeError, TypeError)):
            choice.function_name = 'other'


@pytest.mark.unit
class TestToolChoicePostInitValidation:
    def test_specific_mode_requires_function_name(self):
        with pytest.raises(ValueError, match='function_name is required'):
            ToolChoice(mode='specific', function_name=None)

    def test_specific_mode_with_function_name_is_valid(self):
        choice = ToolChoice(mode='specific', function_name='test')

        assert choice.mode == 'specific'
        assert choice.function_name == 'test'

    def test_auto_mode_without_function_name_is_valid(self):
        choice_auto = ToolChoice(mode=ToolChoiceMode.AUTO)
        choice_none = ToolChoice(mode=ToolChoiceMode.NONE)
        choice_required = ToolChoice(mode=ToolChoiceMode.REQUIRED)

        assert choice_auto.function_name is None
        assert choice_none.function_name is None
        assert choice_required.function_name is None


@pytest.mark.unit
class TestToolChoiceEdgeCases:
    def test_case_sensitivity_of_mode_strings(self):
        choice_lower = ToolChoice.from_value('auto')
        assert choice_lower.mode == ToolChoiceMode.AUTO

        with pytest.raises(ValueError):
            ToolChoice.from_value('AUTO')

        with pytest.raises(ValueError):
            ToolChoice.from_value('Auto')

    def test_whitespace_in_mode_string(self):
        with pytest.raises(ValueError):
            ToolChoice.from_value(' auto')

        with pytest.raises(ValueError):
            ToolChoice.from_value('auto ')

    def test_empty_string_raises_error(self):
        with pytest.raises(ValueError):
            ToolChoice.from_value('')

    def test_function_name_with_special_characters(self):
        names = ['tool_v2', 'my_tool_123', 'CamelCaseTool']

        for name in names:
            choice = ToolChoice.for_function(name)
            assert choice.function_name == name

    def test_empty_available_tools_list(self):
        choice = ToolChoice.from_value('auto', available_tools=[])
        assert choice.mode == ToolChoiceMode.AUTO

        with pytest.raises(ValueError):
            ToolChoice.from_value('search', available_tools=[])

    def test_tool_name_matching_mode_name(self):
        choice = ToolChoice.from_value(
            'auto', available_tools=['auto', 'other']
        )

        assert choice.mode == ToolChoiceMode.AUTO
        assert choice.function_name is None

    def test_validate_with_set_vs_list(self):
        choice = ToolChoice.for_function('search')

        choice.validate_against_tools({'search', 'calculator'})

    def test_equality_of_tool_choices(self):
        choice1 = ToolChoice.auto()
        choice2 = ToolChoice.auto()

        assert choice1 == choice2

        choice3 = ToolChoice.for_function('search')
        choice4 = ToolChoice.for_function('search')

        assert choice3 == choice4

    def test_inequality_of_different_choices(self):
        choice1 = ToolChoice.auto()
        choice2 = ToolChoice.none()

        assert choice1 != choice2

        choice3 = ToolChoice.for_function('search')
        choice4 = ToolChoice.for_function('calculator')

        assert choice3 != choice4

    def test_hash_allows_use_in_sets(self):
        choices = {
            ToolChoice.auto(),
            ToolChoice.none(),
            ToolChoice.required(),
            ToolChoice.for_function('search'),
        }

        assert len(choices) == 4

    def test_repr_string_representation(self):
        choice = ToolChoice.auto()
        repr_str = repr(choice)

        assert 'ToolChoice' in repr_str or 'auto' in repr_str


@pytest.mark.unit
class TestToolChoiceAPIIntegration:
    def test_roundtrip_from_value_to_openai(self):
        choice = ToolChoice.from_value('auto')
        openai_format = choice.to_openai_format()
        assert openai_format == 'auto'

        original = {'type': 'function', 'function': {'name': 'search'}}
        choice = ToolChoice.from_value(original)
        openai_format = choice.to_openai_format()

        assert openai_format == original

    def test_openai_format_structure(self):
        choice = ToolChoice.for_function('my_tool')
        result = choice.to_openai_format()

        expected_keys = {'type', 'function'}
        assert set(result.keys()) == expected_keys

        expected_func_keys = {'name'}
        assert set(result['function'].keys()) == expected_func_keys

    def test_all_modes_produce_valid_openai_format(self):
        test_cases = [
            (ToolChoice.auto(), 'auto'),
            (ToolChoice.none(), 'none'),
            (ToolChoice.required(), 'required'),
            (
                ToolChoice.for_function('test'),
                {'type': 'function', 'function': {'name': 'test'}},
            ),
        ]

        for choice, expected in test_cases:
            result = choice.to_openai_format()
            assert result == expected
