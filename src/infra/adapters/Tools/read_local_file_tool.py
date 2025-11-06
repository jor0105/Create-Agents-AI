from enum import Enum
from pathlib import Path
from typing import Any, Dict, Final, FrozenSet

import fitz
import pandas as pd
import tiktoken

from src.domain import BaseTool
from src.infra.config.logging_config import LoggingConfig


class FileType(Enum):
    """Supported file types for reading."""

    TEXT = "text"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    PARQUET = "parquet"
    UNKNOWN = "unknown"


class ReadLocalFileTool(BaseTool):
    """Secure local file reader with token validation.

    Reads files with multiple validation layers:
    - Token limit enforcement
    - File type validation
    - Comprehensive error handling

    Supports formats: txt, csv, excel (xls/xlsx), pdf, parquet, and common text files.
    """

    name = "read_local_file"
    description = (
        "Use this tool to read local files from the system. "
        "Supports text files (txt, md, py, etc.), CSV, Excel, PDF, and Parquet formats. "
        "The tool validates file size in tokens to prevent overload. "
        "Input must include the absolute or relative file path and optionally "
        "the maximum number of tokens allowed (default: 30000)."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute or relative path to the file to read.",
            },
            "max_tokens": {
                "type": "integer",
                "description": "Maximum number of tokens allowed in the file content. Files exceeding this limit will be rejected.",
                "default": 30000,
            },
        },
        "required": ["path"],
    }

    # Supported file extensions for text-based reading
    TEXT_EXTENSIONS: Final[FrozenSet[str]] = frozenset(
        {
            "txt",
            "log",
            "md",
            "py",
            "js",
            "html",
            "css",
            "json",
            "xml",
            "yaml",
            "yml",
            "rst",
            "ini",
            "cfg",
            "conf",
            "sh",
            "bash",
            "zsh",
        }
    )

    # Excel extensions
    EXCEL_EXTENSIONS: Final[FrozenSet[str]] = frozenset({"xls", "xlsx", "xlsm"})

    # Maximum file size in bytes (100 MB) as an additional safety check
    MAX_FILE_SIZE_BYTES: Final[int] = 100 * 1024 * 1024

    # Default encoding for tiktoken
    TIKTOKEN_ENCODING: Final[str] = "cl100k_base"

    def __init__(self) -> None:
        """Initialize the ReadLocalFileTool.

        Raises:
            RuntimeError: If tiktoken encoder initialization fails.
        """
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__encoding = self.__initialize_tiktoken()

    def __initialize_tiktoken(self) -> tiktoken.Encoding:
        """Initialize the tiktoken encoder for token counting.

        Returns:
            Initialized tiktoken encoding instance.

        Raises:
            RuntimeError: If encoder initialization fails.
        """
        try:
            encoding = tiktoken.get_encoding(self.TIKTOKEN_ENCODING)
            self.__logger.debug(
                f"Initialized tiktoken encoder: {self.TIKTOKEN_ENCODING}"
            )
            return encoding
        except Exception as e:
            error_msg = f"Failed to initialize tiktoken encoder: {e}"
            self.__logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Args:
            text: Text content to count tokens for.

        Returns:
            Number of tokens in the text.
        """
        try:
            return len(self.__encoding.encode(text))
        except Exception as e:
            self.__logger.error(f"Error counting tokens: {e}")
            # Fallback to character-based estimation (rough approximation: ~4 chars per token)
            return len(text) // 4

    def _read_text_file(self, file_path: Path) -> str:
        """Read a plain text file with UTF-8 encoding.

        Args:
            file_path: Path to the text file.

        Returns:
            File content as string.

        Raises:
            UnicodeDecodeError: If file cannot be decoded as UTF-8.
        """
        return file_path.read_text(encoding="utf-8", errors="replace")

    def _read_csv_file(self, file_path: Path) -> str:
        """Read a CSV file and convert to readable string format.

        Args:
            file_path: Path to the CSV file.

        Returns:
            CSV content as formatted string.

        Raises:
            pd.errors.ParserError: If CSV parsing fails.
        """
        df = pd.read_csv(file_path)
        self.__logger.debug(f"Read CSV file with shape: {df.shape}")
        result: str = df.to_string(index=False)
        return result

    def _read_excel_file(self, file_path: Path) -> str:
        """Read an Excel file (first sheet) and convert to readable string.

        Args:
            file_path: Path to the Excel file.

        Returns:
            Excel content as formatted string.

        Raises:
            Exception: If Excel reading fails.
        """
        df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")
        self.__logger.debug(f"Read Excel file (first sheet) with shape: {df.shape}")
        result: str = df.to_string(index=False)
        return result

    def _read_parquet_file(self, file_path: Path) -> str:
        """Read a Parquet file and convert to readable string.

        Args:
            file_path: Path to the Parquet file.

        Returns:
            Parquet content as formatted string.

        Raises:
            Exception: If Parquet reading fails.
        """
        df = pd.read_parquet(file_path, engine="pyarrow")
        self.__logger.debug(f"Read Parquet file with shape: {df.shape}")
        result: str = df.to_string(index=False)
        return result

    def _read_pdf_file(self, file_path: Path) -> str:
        """Read a PDF file and extract text from all pages.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text from all PDF pages.

        Raises:
            fitz.mupdf.FzError: If PDF reading fails (corrupted/encrypted).
        """
        content_parts: list[str] = []

        with fitz.open(str(file_path)) as doc:
            page_count = len(doc)
            self.__logger.debug(f"Reading PDF with {page_count} pages")

            for page_num, page in enumerate(doc, start=1):
                page_text = page.get_text()
                content_parts.append(f"--- Page {page_num} ---\n{page_text}")

        return "\n".join(content_parts)

    def _determine_file_type(self, extension: str) -> FileType:
        """Determine the file type based on extension.

        Args:
            extension: File extension without the dot (lowercase).

        Returns:
            FileType enum value.
        """
        if extension in self.TEXT_EXTENSIONS:
            return FileType.TEXT
        elif extension == "csv":
            return FileType.CSV
        elif extension in self.EXCEL_EXTENSIONS:
            return FileType.EXCEL
        elif extension == "pdf":
            return FileType.PDF
        elif extension == "parquet":
            return FileType.PARQUET
        else:
            return FileType.UNKNOWN

    def _read_file_by_type(self, file_path: Path, file_type: FileType) -> str:
        """Read file content based on its type.

        Args:
            file_path: Path to the file.
            file_type: Type of the file.

        Returns:
            File content as string.

        Raises:
            UnicodeDecodeError: If text file cannot be decoded.
            Various pandas/fitz exceptions for specific file types.
        """
        if file_type == FileType.TEXT:
            return self._read_text_file(file_path)
        elif file_type == FileType.CSV:
            return self._read_csv_file(file_path)
        elif file_type == FileType.EXCEL:
            return self._read_excel_file(file_path)
        elif file_type == FileType.PDF:
            return self._read_pdf_file(file_path)
        elif file_type == FileType.PARQUET:
            return self._read_parquet_file(file_path)
        else:
            # Try as text file (fallback for unknown types)
            try:
                content = self._read_text_file(file_path)
                self.__logger.warning(
                    f"Unknown file type, successfully read as text: {file_path.suffix}"
                )
                return content
            except UnicodeDecodeError as e:
                raise UnicodeDecodeError(
                    e.encoding,
                    e.object,
                    e.start,
                    e.end,
                    f"Cannot decode file as text: {file_path.suffix}",
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
            - Unsupported file type: File type cannot be read
            - Various format-specific errors (PDF, CSV, Excel, etc.)
        """
        self.__logger.info(
            f"Executing file read: path='{path}', max_tokens={max_tokens}"
        )

        try:
            # Construct file path
            file_path = Path(path).resolve()

            # Validation: File existence
            if not file_path.exists():
                return self.__format_error("File not found", path)

            # Validation: Is a file (not directory)
            if not file_path.is_file():
                return self.__format_error("Path is a directory", path)

            # Validation: File size check (before reading)
            file_size = file_path.stat().st_size
            if file_size > self.MAX_FILE_SIZE_BYTES:
                size_mb = file_size / (1024 * 1024)
                max_mb = self.MAX_FILE_SIZE_BYTES / (1024 * 1024)
                return self.__format_error(
                    "File too large",
                    f"{path} is {size_mb:.2f} MB (max: {max_mb:.2f} MB)",
                )

            # Determine file type and read content
            extension = file_path.suffix.lstrip(".").lower() or "txt"
            self.__logger.debug(f"Processing file as type: {extension}")

            file_type = self._determine_file_type(extension)
            content = self._read_file_by_type(file_path, file_type)

            # Token validation
            token_count = self._count_tokens(content)
            self.__logger.debug(f"File content has {token_count} tokens")

            if token_count > max_tokens:
                return self.__format_error(
                    "Content exceeds token limit",
                    f"{path} has {token_count} tokens (max: {max_tokens}). "
                    f"Consider increasing max_tokens or processing in chunks",
                )

            self.__logger.info(
                f"Successfully read file '{path}': {len(content)} characters, {token_count} tokens"
            )
            return content

        except FileNotFoundError:
            return self.__format_error("File not found", path)

        except pd.errors.ParserError as e:
            return self.__format_error("CSV/Excel parsing failed", f"{path}: {e}")

        except fitz.mupdf.FzError as e:
            return self.__format_error("PDF reading failed", f"{path}: {e}")

        except PermissionError:
            return self.__format_error("Permission denied", path)

        except UnicodeDecodeError as e:
            return self.__format_error(
                "Unsupported file type", f"Cannot decode '{path}' as text: {e.reason}"
            )

        except Exception as e:
            error_msg = (
                f"[ReadLocalFileTool Error] Unexpected error: {type(e).__name__}: {e}"
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
        error_msg = f"[ReadLocalFileTool Error] {error_type}: {details}"
        self.__logger.error(error_msg)
        return error_msg
