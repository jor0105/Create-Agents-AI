"""Global pytest configuration and shared fixtures for the application."""

from unittest.mock import Mock

import pytest

from src.application.interfaces.chat_repository import ChatRepository
from src.domain.entities.agent_domain import Agent
from src.domain.value_objects import History

DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-5-nano"
DEFAULT_TEST_AGENT_NAME = "Test Agent"
DEFAULT_TEST_INSTRUCTIONS = "You are a test agent"
MOCKED_AI_RESPONSE = "Mocked AI response"


@pytest.fixture
def mock_chat_repository():
    """Mock ChatRepository for tests. Provides a fully configured mock with a default chat response."""
    mock = Mock(spec=ChatRepository)
    mock.chat.return_value = MOCKED_AI_RESPONSE
    return mock


@pytest.fixture
def sample_agent():
    """Basic example Agent for tests with minimal configuration."""
    return Agent(
        provider=DEFAULT_PROVIDER,
        model=DEFAULT_MODEL,
        name=DEFAULT_TEST_AGENT_NAME,
        instructions=DEFAULT_TEST_INSTRUCTIONS,
    )


@pytest.fixture
def sample_agent_with_history(sample_agent):
    """Agent fixture pre-populated with conversation history for context-dependent tests."""
    sample_agent.add_user_message("Hello")
    sample_agent.add_assistant_message("Hi there!")
    sample_agent.add_user_message("How are you?")
    sample_agent.add_assistant_message("I'm doing well!")
    return sample_agent


@pytest.fixture
def empty_history():
    """Empty History instance for tests that validate initial behavior without prior messages."""
    return History()


@pytest.fixture
def populated_history():
    """History pre-populated with example messages for tests that validate processing of multiple messages."""
    history = History()
    history.add_user_message("Message 1")
    history.add_assistant_message("Response 1")
    history.add_user_message("Message 2")
    history.add_assistant_message("Response 2")
    return history


def pytest_configure(config):
    """Executed before tests: register custom markers for categorizing and filtering tests."""
    markers = [
        ("unit", "marks the test as unit - isolated component tests"),
        (
            "integration",
            "marks the test as integration - tests with multiple components",
        ),
        ("slow", "marks the test as slow - tests that take longer"),
    ]

    for marker_name, marker_description in markers:
        config.addinivalue_line("markers", f"{marker_name}: {marker_description}")
