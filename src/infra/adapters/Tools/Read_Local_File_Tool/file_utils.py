from pathlib import Path
from typing import Optional

import chardet
import fitz
import pandas as pd
import tiktoken

from src.domain import FileReadException
from src.infra.config.logging_config import LoggingConfig

from .constants import (
    COMMON_ENCODINGS,
    EXCEL_EXTENSIONS,
    TEXT_EXTENSIONS,
    TIKTOKEN_ENCODING,
    FileType,
)

logger = LoggingConfig.get_logger(__name__)


def initialize_tiktoken() -> tiktoken.Encoding:
    """Initialize the tiktoken encoder for token counting.

    Returns:
        Initialized tiktoken encoding instance.

    Raises:
        RuntimeError: If encoder initialization fails.
    """
    try:
        encoding = tiktoken.get_encoding(TIKTOKEN_ENCODING)
        logger.debug(f"Initialized tiktoken encoder: {TIKTOKEN_ENCODING}")
        return encoding
    except Exception as e:
        error_msg = f"Failed to initialize tiktoken encoder: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def count_tokens(text: str, encoding: tiktoken.Encoding) -> int:
    """Count the number of tokens in the given text.

    Args:
        text: Text content to count tokens for.
        encoding: Tiktoken encoding instance.

    Returns:
        Number of tokens in the text.
    """
    try:
        return len(encoding.encode(text))
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        # Fallback to character-based estimation (rough approximation: ~4 chars per token)
        return len(text) // 4


def detect_encoding(file_path: Path) -> str:
    """Detect the encoding of a file using chardet.

    Args:
        file_path: Path to the file.

    Returns:
        Detected encoding name, or 'utf-8' as fallback.
    """
    try:
        with open(file_path, "rb") as file:
            raw_data = file.read(100000)  # Read first 100KB for detection
            result = chardet.detect(raw_data)
            detected_encoding = result.get("encoding", "utf-8")
            confidence = result.get("confidence", 0)

            logger.debug(
                f"Detected encoding: {detected_encoding} (confidence: {confidence:.2f})"
            )

            # If confidence is low, fallback to utf-8
            if confidence < 0.7:
                logger.warning(
                    f"Low confidence ({confidence:.2f}) in detected encoding, trying common encodings"
                )
                return "utf-8"

            return detected_encoding or "utf-8"
    except Exception as e:
        logger.warning(f"Encoding detection failed: {e}, using utf-8")
        return "utf-8"


def read_text_file(file_path: Path) -> str:
    """Read a plain text file with automatic encoding detection.

    Args:
        file_path: Path to the text file.

    Returns:
        File content as string.

    Raises:
        UnicodeDecodeError: If file cannot be decoded with any supported encoding.
    """
    # Try detected encoding first
    detected_encoding = detect_encoding(file_path)

    encodings_to_try = [detected_encoding] + [
        enc for enc in COMMON_ENCODINGS if enc != detected_encoding
    ]

    last_error: Optional[Exception] = None
    for encoding in encodings_to_try:
        try:
            content = file_path.read_text(encoding=encoding, errors="strict")
            logger.debug(f"Successfully read file with encoding: {encoding}")
            return content
        except (UnicodeDecodeError, LookupError) as e:
            last_error = e
            logger.debug(f"Failed to read with {encoding}: {e}")
            continue

    # If all encodings fail, try UTF-8 with error replacement
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        logger.warning("All encodings failed, using UTF-8 with character replacement")
        return content
    except Exception:
        raise UnicodeDecodeError(
            "unknown", b"", 0, 0, f"Failed to decode file: {last_error}"
        )


def read_csv_file(file_path: Path) -> str:
    """Read a CSV file with automatic encoding detection and error handling.

    Args:
        file_path: Path to the CSV file.

    Returns:
        CSV content as formatted string.

    Raises:
        FileReadException: If CSV parsing fails with all strategies.
    """
    # Try detected encoding first
    detected_encoding = detect_encoding(file_path)

    encodings_to_try = [detected_encoding] + [
        enc for enc in COMMON_ENCODINGS if enc != detected_encoding
    ]

    # Common CSV delimiters to try
    delimiters = [",", ";", "\t", "|"]

    last_error: Optional[Exception] = None

    # Try different encoding and delimiter combinations
    for encoding in encodings_to_try:
        for delimiter in delimiters:
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    sep=delimiter,
                    on_bad_lines="skip",  # Skip malformed lines
                    engine="python",  # More flexible parser
                )

                # Check if we got meaningful data (at least 2 columns)
                if df.shape[1] >= 2:
                    logger.debug(
                        f"Read CSV file with encoding {encoding}, "
                        f"delimiter '{delimiter}', shape: {df.shape}"
                    )
                    result: str = df.to_string(index=False)
                    return result
            except (UnicodeDecodeError, LookupError) as e:
                last_error = e
                logger.debug(
                    f"Failed to read CSV with {encoding}, delimiter '{delimiter}': {e}"
                )
                continue
            except Exception as e:
                last_error = e
                continue

    # Last resort: try with maximum error tolerance
    try:
        df = pd.read_csv(
            file_path,
            encoding="utf-8",
            encoding_errors="replace",
            on_bad_lines="skip",
            engine="python",
        )
        logger.warning(
            "All encodings/delimiters failed for CSV, "
            "using UTF-8 with character replacement and skipping bad lines"
        )
        result = df.to_string(index=False)
        return result
    except Exception:
        raise FileReadException(
            str(file_path),
            f"Failed to read CSV with any strategy. Last error: {last_error}",
        )


def read_excel_file(file_path: Path) -> str:
    """Read an Excel file with automatic engine detection and error handling.

    Tries multiple engines (openpyxl for .xlsx, xlrd for .xls) and reads
    the first available sheet.

    Args:
        file_path: Path to the Excel file.

    Returns:
        Excel content as formatted string.

    Raises:
        FileReadException: If Excel reading fails with all strategies.
    """
    # Determine which engine to try based on file extension
    extension = file_path.suffix.lower()
    engines_to_try = []

    if extension == ".xlsx":
        engines_to_try = ["openpyxl", "xlrd"]
    elif extension in [".xls", ".xlsm"]:
        engines_to_try = ["xlrd", "openpyxl"]
    else:
        engines_to_try = ["openpyxl", "xlrd"]

    last_error: Optional[Exception] = None

    for engine in engines_to_try:
        try:
            df = pd.read_excel(file_path, sheet_name=0, engine=engine)
            logger.debug(f"Read Excel file with engine {engine}, shape: {df.shape}")
            result: str = df.to_string(index=False)
            return result
        except Exception as e:
            last_error = e
            logger.debug(f"Failed to read Excel with engine {engine}: {e}")
            continue

    raise FileReadException(
        str(file_path),
        f"Failed to read Excel file with any engine. Last error: {last_error}",
    )


def read_parquet_file(file_path: Path) -> str:
    """Read a Parquet file with automatic engine detection and error handling.

    Tries multiple engines (pyarrow, fastparquet) and handles various
    parquet format variations.

    Args:
        file_path: Path to the Parquet file.

    Returns:
        Parquet content as formatted string.

    Raises:
        FileReadException: If Parquet reading fails with all strategies.
    """
    engines_to_try = ["pyarrow", "fastparquet"]
    last_error: Optional[Exception] = None

    for engine in engines_to_try:
        try:
            df = pd.read_parquet(file_path, engine=engine)
            logger.debug(f"Read Parquet file with engine {engine}, shape: {df.shape}")
            result: str = df.to_string(index=False)
            return result
        except Exception as e:
            last_error = e
            logger.debug(f"Failed to read Parquet with engine {engine}: {e}")
            continue

    raise FileReadException(
        str(file_path),
        f"Failed to read Parquet file with any engine. Last error: {last_error}",
    )


def read_pdf_file(file_path: Path) -> str:
    """Read a PDF file and extract text from all pages with error handling.

    Handles various PDF formats and corrupted pages gracefully.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text from all PDF pages.

    Raises:
        FileReadException: If PDF reading fails.
    """
    try:
        content_parts: list[str] = []

        with fitz.open(str(file_path)) as doc:
            page_count = len(doc)
            logger.debug(f"Reading PDF with {page_count} pages")

            for page_num in range(page_count):
                try:
                    page = doc[page_num]
                    page_text = page.get_text()
                    if page_text.strip():
                        content_parts.append(
                            f"--- Page {page_num + 1} ---\n{page_text}"
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to extract text from page {page_num + 1}: {e}"
                    )
                    content_parts.append(
                        f"--- Page {page_num + 1} --- [Error extracting text: {e}]\n"
                    )
                    continue

        if not content_parts:
            raise FileReadException(str(file_path), "No readable content found in PDF")

        return "\n".join(content_parts)

    except FileReadException:
        raise
    except Exception as e:
        raise FileReadException(
            str(file_path),
            f"PDF processing failed: {type(e).__name__}: {e}",
        )


def determine_file_type(extension: str) -> FileType:
    """Determine the file type based on extension.

    Args:
        extension: File extension without the dot (lowercase).

    Returns:
        FileType enum value.
    """
    if extension in TEXT_EXTENSIONS:
        return FileType.TEXT
    elif extension == "csv":
        return FileType.CSV
    elif extension in EXCEL_EXTENSIONS:
        return FileType.EXCEL
    elif extension == "pdf":
        return FileType.PDF
    elif extension == "parquet":
        return FileType.PARQUET
    else:
        return FileType.UNKNOWN


def read_file_by_type(file_path: Path, file_type: FileType) -> str:
    """Read file content based on its type.

    Args:
        file_path: Path to the file.
        file_type: Type of the file.

    Returns:
        File content as string.

    Raises:
        FileReadException: If file reading fails.
    """
    try:
        if file_type == FileType.TEXT:
            return read_text_file(file_path)
        elif file_type == FileType.CSV:
            return read_csv_file(file_path)
        elif file_type == FileType.EXCEL:
            return read_excel_file(file_path)
        elif file_type == FileType.PDF:
            return read_pdf_file(file_path)
        elif file_type == FileType.PARQUET:
            return read_parquet_file(file_path)
        else:
            # Try as text file (fallback for unknown types)
            try:
                content = read_text_file(file_path)
                logger.warning(
                    f"Unknown file type, successfully read as text: {file_path.suffix}"
                )
                return content
            except UnicodeDecodeError as e:
                raise FileReadException(
                    str(file_path),
                    f"Cannot decode file as text: {e.reason}",
                )
    except FileReadException:
        raise
    except Exception as e:
        raise FileReadException(
            str(file_path),
            f"{type(e).__name__}: {e}",
        )
