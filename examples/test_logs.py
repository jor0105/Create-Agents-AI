import logging
import sys
import asyncio
import os
from typing import Any, List, Optional
from createagents import (
    configure_logging,
    create_logger,
    CreateAgent,
    LoggerInterface,
)

# --- Configuration ---
# Test new configure_logging parameters
print('=' * 60)
print('🧪 Testing configure_logging with all new parameters')
print('=' * 60)

# Test 1: Custom format string without timestamp
print('\n[Test 1] Custom format_string + include_timestamp=False')
configure_logging(
    level=logging.DEBUG,
    format_string='%(levelname)s [%(name)s] %(message)s',
    include_timestamp=False,
    max_bytes=1024 * 1024,  # 1MB
    backup_count=3,
)
logger = create_logger(__name__)
logger.info('Custom format test - no timestamp visible')

# Test 2: JSON format
print('\n[Test 2] JSON format (json_format=True)')
configure_logging(level=logging.INFO, json_format=True)
logger2 = create_logger('json_test')
logger2.info('JSON format test message')

# Test 3: File logging (creates logs/test_example.log)
print('\n[Test 3] File logging (log_to_file=True)')
configure_logging(
    level=logging.DEBUG,
    log_to_file=True,
    log_file_path='logs/test_example.log',
    max_bytes=512 * 1024,  # 512KB
    backup_count=2,
)
logger3 = create_logger('file_test')
logger3.info('This should appear in console AND file')

# Reset to standard format for agent tests
print('\n[Test 4] Standard format with timestamp (default)')
configure_logging(level=logging.DEBUG, include_timestamp=True)
logger = create_logger(__name__)
logger.info('Back to standard format with timestamp')

# --- Mock Environment for Testing ---
# Ideally, these should be set in your .env file,
# but for a standalone example,
# we can warn if they are missing.
if not os.getenv('OPENAI_API_KEY'):
    logger.warning(
        'OPENAI_API_KEY not found in environment. OpenAI tests will likely fail.'
    )


# --- Custom Logger for Interface Testing ---
class MyCustomLogger(LoggerInterface):
    """
    A custom logger implementation to verify that CreateAgent accepts
    any class implementing LoggerInterface, not just the internal LoggingConfig.
    """

    def __init__(self):
        self.logs = []

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        print(f'[CUSTOM-DEBUG] {message}')
        self.logs.append(f'DEBUG: {message}')

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        print(f'[CUSTOM-INFO] {message}')
        self.logs.append(f'INFO: {message}')

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        print(f'[CUSTOM-WARNING] {message}')
        self.logs.append(f'WARNING: {message}')

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        print(f'[CUSTOM-ERROR] {message}')
        self.logs.append(f'ERROR: {message}')

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        print(f'[CUSTOM-CRITICAL] {message}')
        self.logs.append(f'CRITICAL: {message}')

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        print(f'[CUSTOM-EXCEPTION] {message}')
        self.logs.append(f'EXCEPTION: {message}')


async def run_agent_test(
    test_name: str,
    provider: str,
    model: str,
    stream: bool,
    tools: Optional[List[str]] = None,
    message: str = 'Hello, who are you?',
    custom_logger: Optional[LoggerInterface] = None,
):
    """
    Generic test runner for an agent configuration.

    Args:
        test_name: Label for the test case.
        provider: 'openai' or 'ollama'.
        model: Model identifier.
        stream: Whether to enable streaming.
        tools: List of tools to enable.
        message: The prompt to send.
        custom_logger: Optional custom logger to inject.
    """
    # Use the custom logger if provided, otherwise use the global one
    test_logger = custom_logger if custom_logger else logger

    test_logger.info(f'\n{"=" * 20} START TEST: {test_name} {"=" * 20}')
    test_logger.info(
        f'Configuration: Provider={provider}, Model={model}, Stream={stream}, Tools={tools}'
    )

    try:
        # 1. Initialize Agent
        agent = CreateAgent(
            provider=provider,
            model=model,
            name=f'TestAgent-{test_name}',
            instructions='You are a helpful AI assistant used for integration testing.',
            config={'stream': stream},
            tools=tools,
            logger=custom_logger,  # Inject custom logger here!
        )

        test_logger.info('Agent initialized successfully.')

        # 2. Send Message
        test_logger.info(f"Sending message: '{message}'")
        response = await agent.chat(message)

        # 3. Handle Response (Stream vs Non-Stream)
        if stream:
            test_logger.info('Stream mode detected. Consuming stream...')
            full_response = ''
            # In a real scenario, response is a StreamingResponseDTO which is iterable
            # We need to iterate over it to consume the stream and trigger logs
            async for token in response:
                full_response += token
                # Optional:
                # print token to stdout to visualize stream
                # (bypassing logger for raw output)
                sys.stdout.write(token)
                sys.stdout.flush()

            print()  # Newline after stream

            test_logger.info(
                f'\nStream consumed completely. Full response length: {len(full_response)}'
            )
            # Log first 100 chars
            if isinstance(test_logger, MyCustomLogger):
                test_logger.debug(
                    f'Full Response Content: {full_response[:100]}...'
                )
            else:
                test_logger.debug(
                    f'Full Response Content: {full_response[:100]}...'
                )

        else:
            test_logger.info('Non-stream mode. Response received immediately.')
            test_logger.info(f'Response: {response}')
            print(f'Response: {response}')

        test_logger.info(f'{"=" * 20} PASS: {test_name} {"=" * 20}\n')

    except Exception as e:
        test_logger.error(f'{"=" * 20} FAIL: {test_name} {"=" * 20}')
        if isinstance(test_logger, MyCustomLogger):
            test_logger.exception(f'Test failed with error: {e}')
        else:
            test_logger.exception(f'Test failed with error: {e}')


async def main():
    """Execute comprehensive test suite."""

    # --- Part 1: Standard Tests (using internal logger) ---
    logger.info('>>> PART 1: Standard Logging Tests')

    # Test Case 1: OpenAI - Standard - No Tools
    await run_agent_test(
        test_name='OpenAI_Standard',
        provider='openai',
        model='gpt-5-nano',
        stream=False,
        message='What is 2 + 2?',
    )
    print('=' * 60)
    # Test Case 2: OpenAI - Streaming - With Tools
    # Note: 'currentdate' is a system tool, usually available by default or by name if registered.
    await run_agent_test(
        test_name='OpenAI_Stream_Tools',
        provider='openai',
        model='gpt-5-nano',
        stream=True,
        tools=['currentdate'],
        message="What is today's date?",
    )
    print('=' * 60)
    # Test Case 3: Ollama - Standard - No Tools
    await run_agent_test(
        test_name='Ollama_Standard',
        provider='ollama',
        model='gpt-oss:120b-cloud',
        stream=False,
        message='Explain quantum computing briefly.',
    )
    print('=' * 60)
    # Test Case 4: Ollama - Streaming - With Tools
    await run_agent_test(
        test_name='Ollama_Stream_Tools',
        provider='ollama',
        model='gpt-oss:120b-cloud',
        stream=True,
        tools=['currentdate'],
        message='What time is it right now?',
    )
    print('=' * 60)
    # --- Part 2: Custom Logger Interface Tests ---
    logger.info('\n>>> PART 2: Custom LoggerInterface Tests')

    custom_logger = MyCustomLogger()

    # Test Case 5: Custom Logger Injection
    await run_agent_test(
        test_name='Custom_Logger_Test',
        provider='openai',  # Using OpenAI as it's faster/more reliable for this check
        model='gpt-5-nano',
        stream=False,
        message='Say hello to my custom logger!',
        custom_logger=custom_logger,
    )
    print('=' * 60)
    # Verify that the custom logger actually captured logs
    logger.info(
        f'Verifying Custom Logger captured {len(custom_logger.logs)} messages...'
    )
    if len(custom_logger.logs) > 0:
        logger.info('SUCCESS: Custom Logger captured messages correctly.')
        for log in custom_logger.logs[:3]:  # Show first 3 captured logs
            logger.info(f'Captured: {log}')
    else:
        logger.error('FAILURE: Custom Logger did not capture any messages!')


if __name__ == '__main__':
    # Run the async main loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Tests interrupted by user.')
    except Exception as e:
        logger.critical(f'Fatal error in test suite: {e}', exc_info=True)
