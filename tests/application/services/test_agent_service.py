from unittest.mock import Mock

import pytest

from createagents.application.services.agent_service import AgentService
from createagents.domain.entities.agent_domain import Agent
from createagents.domain.interfaces.logger_interface import LoggerInterface
from createagents.domain.value_objects import BaseTool


class TestTool(BaseTool):
    name = 'test_tool'
    description = 'Test tool'

    def execute(self, *args, **kwargs) -> str:
        return 'test'


@pytest.mark.unit
class TestAgentService:
    def test_scenario_initialization_success(self):
        agent = Agent(provider='openai', model='gpt-4', name='Test Agent')
        logger = Mock(spec=LoggerInterface)

        service = AgentService(agent, logger)

        assert service.agent == agent
        logger.info.assert_called_once()

    def test_scenario_name_property(self):
        agent = Agent(provider='openai', model='gpt-4', name='Test Agent Name')
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        assert service.name == 'Test Agent Name'

    def test_scenario_provider_property(self):
        agent = Agent(provider='ollama', model='llama2', name='Test')
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        assert service.provider == 'ollama'

    def test_scenario_model_property(self):
        agent = Agent(provider='openai', model='gpt-3.5-turbo', name='Test')
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        assert service.model == 'gpt-3.5-turbo'

    def test_scenario_instructions_property(self):
        agent = Agent(
            provider='openai',
            model='gpt-4',
            name='Test',
            instructions='Test instructions',
        )
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        assert service.instructions == 'Test instructions'

    def test_scenario_config_property(self):
        config = {'temperature': 0.7, 'max_tokens': 100}
        agent = Agent(
            provider='openai', model='gpt-4', name='Test', config=config
        )
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        assert service.config == config

    def test_scenario_tools_property_none(self):
        agent = Agent(provider='openai', model='gpt-4', name='Test')
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        assert service.tools is None

    def test_scenario_tools_property_with_tools(self):
        tool = TestTool()
        agent = Agent(
            provider='openai', model='gpt-4', name='Test', tools=[tool]
        )
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        assert len(service.tools) == 1
        assert service.tools[0].name == 'test_tool'

    def test_scenario_history_property(self):
        agent = Agent(provider='openai', model='gpt-4', name='Test')
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        history = service.history
        assert len(history) == 0

    def test_scenario_add_user_message_success(self):
        agent = Agent(provider='openai', model='gpt-4', name='Test')
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        service.add_user_message('Hello')

        assert len(service.history) == 1
        logger.debug.assert_called()

    def test_scenario_add_assistant_message_success(self):
        agent = Agent(provider='openai', model='gpt-4', name='Test')
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        service.add_assistant_message('Hi there')

        assert len(service.history) == 1
        logger.debug.assert_called()

    def test_scenario_add_tool_message_success(self):
        agent = Agent(provider='openai', model='gpt-4', name='Test')
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        service.add_tool_message('Tool result')

        assert len(service.history) == 1
        logger.debug.assert_called()

    def test_scenario_clear_history_empty(self):
        agent = Agent(provider='openai', model='gpt-4', name='Test')
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        service.clear_history()

        assert len(service.history) == 0
        logger.debug.assert_called()

    def test_scenario_clear_history_with_messages(self):
        agent = Agent(provider='openai', model='gpt-4', name='Test')
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        service.add_user_message('Message 1')
        service.add_assistant_message('Response 1')
        service.add_user_message('Message 2')

        assert len(service.history) == 3

        service.clear_history()

        assert len(service.history) == 0

    def test_scenario_logging_initialization_with_tools(self):
        tool = TestTool()
        agent = Agent(
            provider='openai', model='gpt-4', name='TestAgent', tools=[tool]
        )
        logger = Mock(spec=LoggerInterface)

        AgentService(agent, logger)

        logger.info.assert_called_once()
        call_args = logger.info.call_args[0]
        assert 'TestAgent' in str(call_args)
        assert 'openai' in str(call_args)
        assert 'gpt-4' in str(call_args)
        assert '1' in str(call_args)

    def test_scenario_message_logging_captures_length(self):
        agent = Agent(provider='openai', model='gpt-4', name='Test')
        logger = Mock(spec=LoggerInterface)
        service = AgentService(agent, logger)

        long_message = 'A' * 1000
        service.add_user_message(long_message)

        debug_call = logger.debug.call_args[0]
        assert '1000' in str(debug_call)
