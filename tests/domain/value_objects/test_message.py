import pytest

from src.domain.value_objects.message import Message, MessageRole


@pytest.mark.unit
class TestMessageRole:
    def test_message_role_values(self):
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"

    def test_message_role_string_representation(self):
        assert str(MessageRole.USER) == "user"
        assert str(MessageRole.ASSISTANT) == "assistant"
        assert str(MessageRole.SYSTEM) == "system"


@pytest.mark.unit
class TestMessage:
    def test_create_message_with_valid_data(self):
        message = Message(role=MessageRole.USER, content="Hello")

        assert message.role == MessageRole.USER
        assert message.content == "Hello"

    def test_create_user_message(self):
        message = Message(role=MessageRole.USER, content="User message")

        assert message.role == MessageRole.USER
        assert message.content == "User message"

    def test_create_assistant_message(self):
        message = Message(role=MessageRole.ASSISTANT, content="Assistant response")

        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Assistant response"

    def test_create_system_message(self):
        message = Message(role=MessageRole.SYSTEM, content="System instruction")

        assert message.role == MessageRole.SYSTEM
        assert message.content == "System instruction"

    def test_message_is_immutable(self):
        message = Message(role=MessageRole.USER, content="Test")

        with pytest.raises(AttributeError):
            message.content = "New content"

    def test_message_validation_empty_content(self):
        with pytest.raises(ValueError, match="The message content cannot be empty"):
            Message(role=MessageRole.USER, content="")

    def test_message_validation_whitespace_content(self):
        with pytest.raises(ValueError, match="The message content cannot be empty"):
            Message(role=MessageRole.USER, content="   ")

    def test_message_validation_invalid_role_type(self):
        with pytest.raises(
            ValueError, match="The 'role' must be an instance of MessageRole"
        ):
            Message(role="user", content="Hello")

    def test_to_dict_conversion(self):
        message = Message(role=MessageRole.USER, content="Hello")
        result = message.to_dict()

        assert result == {"role": "user", "content": "Hello"}
        assert isinstance(result, dict)

    def test_from_dict_with_valid_data(self):
        data = {"role": "user", "content": "Hello"}
        message = Message.from_dict(data)

        assert message.role == MessageRole.USER
        assert message.content == "Hello"

    def test_from_dict_all_roles(self):
        roles = ["user", "assistant", "system"]

        for role in roles:
            data = {"role": role, "content": "Test"}
            message = Message.from_dict(data)
            assert message.role.value == role

    def test_from_dict_missing_role(self):
        data = {"content": "Hello"}

        with pytest.raises(
            ValueError, match="The dictionary must contain 'role' and 'content'"
        ):
            Message.from_dict(data)

    def test_from_dict_missing_content(self):
        data = {"role": "user"}

        with pytest.raises(
            ValueError, match="The dictionary must contain 'role' and 'content'"
        ):
            Message.from_dict(data)

    def test_from_dict_invalid_role(self):
        data = {"role": "invalid_role", "content": "Hello"}

        with pytest.raises(ValueError, match="Invalid role"):
            Message.from_dict(data)

    def test_message_equality(self):
        msg1 = Message(role=MessageRole.USER, content="Hello")
        msg2 = Message(role=MessageRole.USER, content="Hello")
        msg3 = Message(role=MessageRole.USER, content="Different")

        assert msg1 == msg2
        assert msg1 != msg3

    def test_to_dict_and_from_dict_roundtrip(self):
        original = Message(role=MessageRole.ASSISTANT, content="Test message")
        dict_form = original.to_dict()
        reconstructed = Message.from_dict(dict_form)

        assert original == reconstructed

    def test_message_with_long_content(self):
        long_content = "A" * 10000
        message = Message(role=MessageRole.USER, content=long_content)

        assert message.content == long_content
        assert len(message.content) == 10000

    def test_message_with_special_characters(self):
        special_content = "Hello! 你好 🎉 @#$%^&*()"
        message = Message(role=MessageRole.USER, content=special_content)

        assert message.content == special_content

    def test_message_with_newlines(self):
        multiline_content = "Line 1\nLine 2\nLine 3"
        message = Message(role=MessageRole.USER, content=multiline_content)

        assert message.content == multiline_content
        assert "\n" in message.content

    def test_message_role_enum_values(self):
        assert MessageRole.USER == MessageRole.USER
        assert MessageRole.ASSISTANT == MessageRole.ASSISTANT
        assert MessageRole.SYSTEM == MessageRole.SYSTEM

    def test_message_from_dict_with_empty_content(self):
        data = {"role": "user", "content": ""}

        with pytest.raises(ValueError, match="cannot be empty"):
            Message.from_dict(data)

    def test_message_from_dict_with_whitespace_content(self):
        data = {"role": "user", "content": "   "}

        with pytest.raises(ValueError, match="cannot be empty"):
            Message.from_dict(data)

    def test_message_immutability_all_fields(self):
        message = Message(role=MessageRole.USER, content="Test")

        with pytest.raises(AttributeError):
            message.content = "New"

        with pytest.raises(AttributeError):
            message.role = MessageRole.ASSISTANT

    def test_message_to_dict_consistency(self):
        message = Message(role=MessageRole.USER, content="Test")

        dict1 = message.to_dict()
        dict2 = message.to_dict()

        assert dict1 == dict2
        assert dict1 is not dict2

    def test_message_with_tab_characters(self):
        content_with_tabs = "Column1\tColumn2\tColumn3"
        message = Message(role=MessageRole.USER, content=content_with_tabs)

        assert "\t" in message.content
        assert message.content == content_with_tabs

    def test_message_equality_different_roles(self):
        msg1 = Message(role=MessageRole.USER, content="Same content")
        msg2 = Message(role=MessageRole.ASSISTANT, content="Same content")

        assert msg1 != msg2

    def test_message_from_dict_all_valid_roles(self):
        roles = ["user", "assistant", "system"]

        for role_str in roles:
            data = {"role": role_str, "content": "Test content"}
            message = Message.from_dict(data)
            assert message.role.value == role_str
            assert message.content == "Test content"
