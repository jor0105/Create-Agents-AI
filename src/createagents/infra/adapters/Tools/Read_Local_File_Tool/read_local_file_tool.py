from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel, Field

from .....domain import BaseTool, FileReadException
from .....domain.interfaces import LoggerInterface
from ....config import create_logger

IMPORT_ERROR = None

try:
    from .file_utils import (
        count_tokens,
        determine_file_type,
        initialize_tiktoken,
        read_file_by_type,
    )  # pylint: disable=import-outside-toplevel

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = e


class ReadLocalFileInput(BaseModel):
    """Input schema for ReadLocalFileTool using Pydantic validation.

    This schema validates and documents the inputs expected by the tool.
    """

    path: str = Field(
        ...,
        description='Absolute or relative path to the file to read.',
    )
    max_tokens: int = Field(
        default=30000,
        ge=1,
        description=(
            'Maximum number of tokens allowed in the file content. '
            'Files exceeding this limit will be rejected.'
        ),
    )


class ReadLocalFileTool(BaseTool):
    """Secure local file reader with token validation.

    Reads files with multiple validation layers:
    - Token limit enforcement
    - File type validation
    - Comprehensive error handling

    Supports formats: txt, csv, excel (xls/xlsx), pdf, parquet,
    and common text files.
    """

    name = 'readlocalfile'
    description = (
        'Use this tool to read local files from the system. '
        'Supports text files (txt, md, py, etc.), CSV, Excel, PDF and '
        'Parquet formats. The tool validates file size in tokens to prevent '
        'overload. Input must include the absolute or relative file path and '
        'optionally the maximum number of tokens allowed (default: 30000).'
    )
    args_schema: Type[BaseModel] = ReadLocalFileInput

    def __init__(
        self,
        max_file_size_mb: float = 50.0,
        logger: Optional[LoggerInterface] = None,
    ) -> None:
        """Initialize the ReadLocalFileTool.

        Args:
            max_file_size_mb: Maximum file size in megabytes (default: 50 MB).
            logger: Optional logger instance. If None, creates from config.

        Raises:
            RuntimeError: If tiktoken encoder initialization fails or
                          dependencies are missing.
        """
        if not DEPENDENCIES_AVAILABLE:
            raise RuntimeError(
                'ReadLocalFileTool requires optional dependencies. '
                'Install with: pip install createagents[file-tools] or '
                'poetry install -E file-tools\n'
                f'Missing dependencies error: {IMPORT_ERROR}'
            )

        self.__logger = logger or create_logger(__name__)
        self.__encoding = initialize_tiktoken()

        # Configurable max file size
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        self.__logger.debug(
            'ReadLocalFileTool initialized with max_file_size: %.2f MB (%d bytes)',
            max_file_size_mb,
            self.max_file_size_bytes,
        )

    async def execute_async(
        self,
        path: str,
        max_tokens: int = 30000,
    ) -> str:
        """Execute file reading asynchronously - optimized for I/O.

        This method runs the file reading operation in a thread pool executor
        to avoid blocking the event loop, which is important for I/O-bound
        operations like file reading.

        Args:
            path: Absolute or relative path to the file.
            max_tokens: Maximum tokens allowed (default: 30000).

        Returns:
            File content as string, or error message if operation fails.
        """
        import asyncio  # pylint: disable=import-outside-toplevel

        self.__logger.debug(
            'Executing file read asynchronously: path=%s, max_tokens=%s',
            path,
            max_tokens,
        )

        # Run the synchronous execute() in a thread pool executor
        # This prevents blocking the event loop for file I/O
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: self.execute(path=path, max_tokens=max_tokens)
        )

    def execute(
        self,
        path: str,
        max_tokens: int = 30000,
    ) -> str:
        """Execute the file reading operation with validation.

        Args:
            path: Absolute or relative path to the file.
            max_tokens: Maximum tokens allowed (default: 30000).

        Returns:
            File content as string, or error message if operation fails.

        Error Messages:
            - File not found: File doesn't exist
            - Path is a directory: Path points to a directory
            - File too large: File exceeds size limit
            - Content exceeds token limit: Content has too many tokens
            - Various file-specific errors
        """
        self.__logger.info(
            "Executing file read: path='%s', max_tokens=%s",
            path,
            max_tokens,
        )

        try:
            file_path = Path(path).resolve()

            if not file_path.exists():
                return self.__format_error('File not found', path)

            if not file_path.is_file():
                return self.__format_error('Path is a directory', path)

            # Validation: File size check (before reading)
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size_bytes:
                size_mb = file_size / (1024 * 1024)
                max_mb = self.max_file_size_bytes / (1024 * 1024)
                return self.__format_error(
                    'File too large',
                    f'{path} is {size_mb:.2f} MB (max: {max_mb:.2f} MB)',
                )

            # Determine file type and read content
            extension = file_path.suffix.lstrip('.').lower() or 'txt'
            self.__logger.debug('Processing file as type: %s', extension)

            file_type = determine_file_type(extension)
            content = read_file_by_type(file_path, file_type)

            token_count = count_tokens(content, self.__encoding)
            self.__logger.debug('File content has %s tokens', token_count)

            if token_count > max_tokens:
                return self.__format_error(
                    'Content exceeds token limit',
                    f'{path} has {token_count} tokens (max: {max_tokens}). '
                    f'Consider increasing max_tokens or processing in chunks',
                )

            self.__logger.info(
                "Successfully read file '%s': %s characters, %s tokens",
                path,
                len(content),
                token_count,
            )
            return content

        except FileNotFoundError:
            return self.__format_error('File not found', path)

        except FileReadException as e:
            return self.__format_error('File read error', e.message)

        except PermissionError:
            return self.__format_error('Permission denied', path)

        except (OSError, RuntimeError, ValueError) as e:
            return self.__format_error('File processing error', str(e))

        except Exception as e:
            error_msg = (
                f'[ReadLocalFileTool Error] Unexpected error: '
                f'{type(e).__name__}: {e}'
            )
            self.__logger.error(error_msg, exc_info=True)
            return error_msg

    def __format_error(self, error_type: str, details: str) -> str:
        """Format a consistent error message.

        Args:
            error_type: Type of error that occurred.
            details: Detailed information about the error.

        Returns:
            Formatted error message string.
        """
        error_msg = f'[ReadLocalFileTool Error] {error_type}: {details}'
        self.__logger.error(error_msg)
        return error_msg
