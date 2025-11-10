from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.domain import FileReadException
from src.infra.config.logging_config import LoggingConfig

from .constants import (
    COMMON_ENCODINGS,
    DOCUMENT_EXTENSIONS,
    EXCEL_EXTENSIONS,
    TEXT_EXTENSIONS,
    TIKTOKEN_ENCODING,
    FileType,
)

if TYPE_CHECKING:
    import tiktoken

logger = LoggingConfig.get_logger(__name__)


def _lazy_import(module_name: str, package_name: str):
    """Import a module lazily with helpful error messages.

    Args:
        module_name: Name of the module to import (e.g., 'pandas')
        package_name: Name used in pip install (e.g., 'pandas')

    Returns:
        The imported module

    Raises:
        RuntimeError: If module is not available with helpful installation message
    """
    try:
        return __import__(module_name)
    except ImportError as e:
        error_msg = (
            f"'{module_name}' is required for this operation. "
            f"Install it with: pip install ai-agent[file-tools] "
            f"or poetry install -E file-tools"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def initialize_tiktoken() -> "tiktoken.Encoding":
    """Initialize the tiktoken encoder for token counting.

    Returns:
        Initialized tiktoken encoding instance.

    Raises:
        RuntimeError: If tiktoken is not installed or initialization fails.
    """
    try:
        import tiktoken

        encoding = tiktoken.get_encoding(TIKTOKEN_ENCODING)
        logger.debug(f"Initialized tiktoken encoder: {TIKTOKEN_ENCODING}")
        return encoding
    except ImportError as e:
        raise RuntimeError(
            "tiktoken is required for token counting. "
            "Install with: pip install ai-agent[file-tools]"
        ) from e
    except Exception as e:
        error_msg = f"Failed to initialize tiktoken encoder: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def count_tokens(text: str, encoding: "tiktoken.Encoding") -> int:
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
        import chardet

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

    except ImportError:
        logger.warning("chardet not available, using utf-8 as default encoding")
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
        RuntimeError: If pandas is not installed.
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise RuntimeError(
            "pandas is required for CSV reading. "
            "Install with: pip install ai-agent[file-tools]"
        ) from e

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

                if not df.empty:
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
        RuntimeError: If pandas is not installed.
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise RuntimeError(
            "pandas is required for Excel reading. "
            "Install with: pip install ai-agent[file-tools]"
        ) from e

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
        RuntimeError: If pandas is not installed.
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise RuntimeError(
            "pandas is required for Parquet reading. "
            "Install with: pip install ai-agent[file-tools]"
        ) from e

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

    Uses unstructured library for robust PDF parsing that handles various formats,
    including scanned PDFs with OCR capabilities. Supports additional document types
    beyond basic PDFs.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text from all PDF pages.

    Raises:
        FileReadException: If PDF reading fails.
        RuntimeError: If unstructured is not installed.
    """
    try:
        from unstructured.partition.pdf import partition_pdf
    except ImportError as e:
        raise RuntimeError(
            "unstructured is required for PDF reading. "
            "Install with: pip install ai-agent[file-tools]"
        ) from e

    try:
        logger.debug(f"Reading PDF file: {file_path}")

        # partition_pdf automatically handles:
        # - Text extraction from native PDFs
        # - OCR for scanned PDFs (if pytesseract is available)
        # - Layout detection and element classification
        # - Tables, images, and other structured content
        elements = partition_pdf(
            filename=str(file_path),
            strategy="auto",  # Automatically chooses best strategy (fast, hi_res, ocr_only)
            infer_table_structure=True,  # Extract tables as structured data
        )

        if not elements:
            raise FileReadException(str(file_path), "No readable content found in PDF")

        # Combine all extracted text elements
        content_parts: list[str] = []
        current_page = None
        page_content: list[str] = []

        for element in elements:
            # Group content by page if metadata is available
            element_page = (
                getattr(element.metadata, "page_number", None)
                if hasattr(element, "metadata")
                else None
            )

            if element_page is not None and element_page != current_page:
                # Save previous page content
                if page_content:
                    content_parts.append(
                        f"--- Page {current_page} ---\n" + "\n".join(page_content)
                    )
                    page_content = []
                current_page = element_page

            element_text = str(element).strip()
            if element_text:
                page_content.append(element_text)

        # Add last page
        if page_content:
            if current_page is not None:
                content_parts.append(
                    f"--- Page {current_page} ---\n" + "\n".join(page_content)
                )
            else:
                content_parts.extend(page_content)

        result = "\n\n".join(content_parts)
        logger.debug(f"Successfully extracted {len(elements)} elements from PDF")
        return result

    except FileReadException:
        raise
    except Exception as e:
        raise FileReadException(
            str(file_path),
            f"PDF processing failed: {type(e).__name__}: {e}",
        )


def read_document_file(file_path: Path) -> str:
    """Read various document formats using unstructured library.

    Supports Word documents (.doc, .docx), PowerPoint (.ppt, .pptx),
    OpenDocument (.odt), EPUB, MSG, RTF, and other formats.

    Args:
        file_path: Path to the document file.

    Returns:
        Extracted text from the document.

    Raises:
        FileReadException: If document reading fails.
        RuntimeError: If unstructured is not installed.
    """
    try:
        from unstructured.partition.auto import partition
    except ImportError as e:
        raise RuntimeError(
            "unstructured is required for document reading. "
            "Install with: pip install ai-agent[file-tools]"
        ) from e

    try:
        logger.debug(f"Reading document file: {file_path}")

        # partition automatically detects file type and uses appropriate parser
        elements = partition(
            filename=str(file_path),
            strategy="auto",
            infer_table_structure=True,
        )

        if not elements:
            raise FileReadException(
                str(file_path), "No readable content found in document"
            )

        content_parts = [
            str(element).strip() for element in elements if str(element).strip()
        ]

        result = "\n\n".join(content_parts)
        logger.debug(f"Successfully extracted {len(elements)} elements from document")
        return result

    except FileReadException:
        raise
    except Exception as e:
        raise FileReadException(
            str(file_path),
            f"Document processing failed: {type(e).__name__}: {e}",
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
    elif extension in DOCUMENT_EXTENSIONS:
        return FileType.DOCUMENT
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
        elif file_type == FileType.DOCUMENT:
            return read_document_file(file_path)
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
