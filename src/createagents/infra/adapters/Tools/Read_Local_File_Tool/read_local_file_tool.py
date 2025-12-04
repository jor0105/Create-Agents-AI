from pathlib import Path
from time import perf_counter
from typing import Final, List, Optional, Type

from pydantic import BaseModel, Field

from .....domain import BaseTool, FileReadException
from .....domain.interfaces import LoggerInterface
from .....domain.value_objects.tools.response import ToolResponse
from ....config import create_logger

_TOOL_NAME: Final[str] = 'readlocalfile'
_TOOL_VERSION: Final[str] = '2.0.0'

FORBIDDEN_PATH_PATTERNS: Final[List[str]] = [
    '/etc',
    '/root',
    '/var/log',
    '/var/run',
    '/proc',
    '/sys',
    '/dev',
    '/boot',
    '/lib',
    '/lib64',
    '/usr/lib',
    '/usr/local/lib',
    '/.ssh',
    '/.gnupg',
    '/.aws',
    '/.config',
    '/.local/share',
    '/.bash_history',
    '/.zsh_history',
    '/.env',
    '/id_rsa',
    '/id_ed25519',
    '/credentials',
    '/secrets',
    '/private',
    '/.git/config',
]

_IMPORT_ERROR: Optional[Exception] = None
_DEPENDENCIES_AVAILABLE: bool = False

try:
    from .file_utils import (
        count_tokens,
        determine_file_type,
        initialize_tiktoken,
        read_file_by_type,
    )

    _DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    _IMPORT_ERROR = e


class ReadLocalFileInput(BaseModel):
    """Input schema for ReadLocalFileTool.

    Validates and documents the expected inputs for file reading
    with comprehensive descriptions for AI understanding.
    """

    path: str = Field(
        ...,
        description=(
            'Path to the file to read. Can be absolute or relative. '
            'Supports: txt, md, py, json, csv, xlsx, pdf, parquet, docx, and more.'
        ),
    )
    max_tokens: int = Field(
        default=30000,
        ge=100,
        le=200000,
        description=(
            'Maximum tokens allowed in response. '
            'Files exceeding this limit will be rejected. '
            'Range: 100-200000. Default: 30000.'
        ),
    )


class FileMetadata(BaseModel):
    """Metadata about the read file."""

    path: str
    size_bytes: int
    size_human: str
    token_count: int
    file_type: str
    encoding: Optional[str] = None


class ReadLocalFileTool(BaseTool):
    """Secure local file reader with validation and token management.

    Features:
    - Multi-layer security validation (forbidden paths, permissions)
    - Token counting with configurable limits
    - Support for multiple file formats (text, CSV, Excel, PDF, Parquet, etc.)
    - Automatic encoding detection
    - Async execution support for non-blocking I/O
    - Structured responses with metadata

    Security:
    - Blocks access to sensitive system directories
    - Validates file permissions before reading
    - Enforces size limits to prevent memory issues

    Supported formats:
    - Text: txt, md, py, js, json, yaml, xml, html, css, etc.
    - Data: csv, xlsx, xls, parquet
    - Documents: pdf, docx, pptx, odt
    """

    name: str = _TOOL_NAME
    description: str = (
        'Read local files securely with automatic format detection. '
        'Supports text files, CSV, Excel, PDF, Parquet, and documents. '
        'Returns content with token count validation to prevent overload. '
        'Use for accessing local data, reading configurations, or analyzing documents.'
    )
    args_schema: Type[BaseModel] = ReadLocalFileInput

    def __init__(
        self,
        max_file_size_mb: float = 50.0,
        logger: Optional[LoggerInterface] = None,
    ) -> None:
        """Initialize the file reader with configuration.

        Args:
            max_file_size_mb: Maximum file size in MB (default: 50 MB).
            logger: Optional logger instance.

        Raises:
            RuntimeError: If required dependencies are not available.
        """
        if not _DEPENDENCIES_AVAILABLE:
            raise RuntimeError(
                'ReadLocalFileTool requires optional dependencies. '
                'Install with: pip install createagents[file-tools] or '
                f'poetry install -E file-tools\nError: {_IMPORT_ERROR}'
            )

        self._logger = logger or create_logger(__name__)
        self._encoding = initialize_tiktoken()
        self._max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)

        self._logger.debug(
            'ReadLocalFileTool initialized: max_size=%.2fMB',
            max_file_size_mb,
        )

    def _validate_path_security(self, file_path: Path) -> Optional[str]:
        """Validate path against security rules.

        Args:
            file_path: Resolved absolute path to validate.

        Returns:
            Error message if path is forbidden, None if safe.
        """
        path_str = str(file_path).lower()
        home_dir = str(Path.home())

        for pattern in FORBIDDEN_PATH_PATTERNS:
            if pattern.startswith('/'):
                if path_str.startswith(pattern.lower()):
                    self._logger.warning(
                        'Security: Blocked path %s (pattern: %s)',
                        file_path,
                        pattern,
                    )
                    return f'Access denied: forbidden path pattern ({pattern})'
            else:
                home_pattern = f'{home_dir}{pattern}'.lower()
                if (
                    path_str.startswith(home_pattern)
                    or pattern.lower() in path_str
                ):
                    self._logger.warning(
                        'Security: Blocked path %s (pattern: %s)',
                        file_path,
                        pattern,
                    )
                    return f'Access denied: forbidden pattern ({pattern})'

        return None

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format byte size to human-readable string."""
        size: float = float(size_bytes)
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024:
                return f'{size:.2f} {unit}'
            size /= 1024
        return f'{size:.2f} TB'

    async def execute_async(  # type: ignore[override]
        self,
        path: str,
        max_tokens: int = 30000,
    ) -> str:
        """Execute file reading asynchronously.

        Args:
            path: Path to the file.
            max_tokens: Maximum tokens allowed.

        Returns:
            File content or error message.
        """
        import asyncio  # pylint: disable=import-outside-toplevel

        self._logger.debug('Async file read: path=%s', path)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: self.execute(path=path, max_tokens=max_tokens)
        )

    def execute(  # type: ignore[override]
        self,
        path: str,
        max_tokens: int = 30000,
    ) -> str:
        """Execute the file reading operation.

        Args:
            path: Path to the file (absolute or relative).
            max_tokens: Maximum tokens allowed (default: 30000).

        Returns:
            File content as string, or formatted error message.
        """
        start_time = perf_counter()
        self._logger.info(
            'Reading file: path=%s, max_tokens=%d', path, max_tokens
        )

        try:
            file_path = Path(path).resolve()

            security_error = self._validate_path_security(file_path)
            if security_error:
                return self._error_response(
                    security_error, 'SECURITY_VIOLATION', start_time
                )

            if not file_path.exists():
                return self._error_response(
                    f'File not found: {path}', 'FILE_NOT_FOUND', start_time
                )

            if not file_path.is_file():
                return self._error_response(
                    f'Path is a directory: {path}', 'IS_DIRECTORY', start_time
                )

            file_size = file_path.stat().st_size
            if file_size > self._max_file_size_bytes:
                size_human = self._format_size(file_size)
                max_human = self._format_size(self._max_file_size_bytes)
                return self._error_response(
                    f'File too large: {size_human} (max: {max_human})',
                    'FILE_TOO_LARGE',
                    start_time,
                )

            extension = file_path.suffix.lstrip('.').lower() or 'txt'
            file_type = determine_file_type(extension)
            content = read_file_by_type(file_path, file_type)
            token_count = count_tokens(content, self._encoding)

            self._logger.debug(
                'File read: %d chars, %d tokens', len(content), token_count
            )

            if token_count > max_tokens:
                return self._error_response(
                    f'Content exceeds token limit: {token_count:,} tokens (max: {max_tokens:,}). '
                    'Increase max_tokens or process file in chunks.',
                    'TOKEN_LIMIT_EXCEEDED',
                    start_time,
                )

            elapsed_ms = (perf_counter() - start_time) * 1000

            metadata = FileMetadata(
                path=str(file_path),
                size_bytes=file_size,
                size_human=self._format_size(file_size),
                token_count=token_count,
                file_type=file_type.value,
            )

            self._logger.info(
                'Successfully read %s: %d tokens in %.2fms',
                path,
                token_count,
                elapsed_ms,
            )

            return self._success_response(content, metadata, elapsed_ms)

        except FileNotFoundError:
            return self._error_response(
                f'File not found: {path}', 'FILE_NOT_FOUND', start_time
            )

        except FileReadException as exc:
            return self._error_response(
                f'Read error: {exc.message}', 'FILE_READ_ERROR', start_time
            )

        except PermissionError:
            return self._error_response(
                f'Permission denied: {path}', 'PERMISSION_DENIED', start_time
            )

        except (OSError, RuntimeError, ValueError) as exc:
            return self._error_response(
                f'Processing error: {exc}', 'PROCESSING_ERROR', start_time
            )

        except Exception as exc:
            self._logger.error(
                'Unexpected error reading %s: %s', path, exc, exc_info=True
            )
            return self._error_response(
                f'Unexpected error: {type(exc).__name__}: {exc}',
                'UNEXPECTED_ERROR',
                start_time,
            )

    def _success_response(
        self,
        content: str,
        metadata: FileMetadata,
        elapsed_ms: float,
    ) -> str:
        """Format successful response with content.

        Args:
            content: The file content.
            metadata: File metadata.
            elapsed_ms: Execution time in milliseconds.

        Returns:
            Formatted response string optimized for AI consumption.
        """
        return ToolResponse.success(
            data=content,
            message=(
                f'Read {metadata.size_human}, {metadata.token_count:,} tokens, '
                f'type: {metadata.file_type}'
            ),
            tool_name=_TOOL_NAME,
            execution_time_ms=elapsed_ms,
        ).format()

    def _error_response(
        self, message: str, code: str, start_time: float
    ) -> str:
        """Format error response.

        Args:
            message: Error message.
            code: Error code.
            start_time: Execution start time.

        Returns:
            Formatted error string.
        """
        elapsed_ms = (perf_counter() - start_time) * 1000
        self._logger.warning('ReadLocalFileTool error [%s]: %s', code, message)
        return ToolResponse.error(
            message=message,
            tool_name=_TOOL_NAME,
            error_code=code,
            execution_time_ms=elapsed_ms,
        ).format()


__all__ = ['ReadLocalFileTool']
