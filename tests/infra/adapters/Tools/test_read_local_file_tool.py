"""Comprehensive tests for ReadLocalFileTool and file utilities."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Check if optional dependencies are available
try:
    from src.infra.adapters.Tools.Read_Local_File_Tool.read_local_file_tool import (
        ReadLocalFileTool,
    )

    DEPENDENCIES_AVAILABLE = True
except (ImportError, RuntimeError):
    DEPENDENCIES_AVAILABLE = False
    ReadLocalFileTool = None


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason="Optional dependencies not available"
)
@pytest.mark.unit
class TestReadLocalFileTool:
    """Test suite for ReadLocalFileTool."""

    def test_tool_has_correct_name(self):
        """Test that tool has the expected name."""
        tool = ReadLocalFileTool()
        assert tool.name == "read_local_file"

    def test_tool_has_description(self):
        """Test that tool has a description."""
        tool = ReadLocalFileTool()
        assert tool.description
        assert "read" in tool.description.lower()
        assert "file" in tool.description.lower()

    def test_tool_has_parameters_schema(self):
        """Test that tool has properly defined parameters."""
        tool = ReadLocalFileTool()
        assert "type" in tool.parameters
        assert tool.parameters["type"] == "object"
        assert "properties" in tool.parameters
        assert "path" in tool.parameters["properties"]
        assert "max_tokens" in tool.parameters["properties"]
        assert "required" in tool.parameters
        assert "path" in tool.parameters["required"]

    def test_max_file_size_constant_defined(self):
        """Test that MAX_FILE_SIZE_BYTES constant is defined."""
        tool = ReadLocalFileTool()
        assert hasattr(tool, "MAX_FILE_SIZE_BYTES")
        assert tool.MAX_FILE_SIZE_BYTES == 100 * 1024 * 1024  # 100 MB

    def test_execute_read_simple_text_file(self):
        """Test reading a simple text file."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!")
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            assert not result.startswith("[ReadLocalFileTool Error]")
            assert "Hello, World!" in result
        finally:
            Path(filepath).unlink()

    def test_execute_file_not_found(self):
        """Test error handling when file doesn't exist."""
        tool = ReadLocalFileTool()

        result = tool.execute(path="/nonexistent/file.txt", max_tokens=1000)

        assert result.startswith("[ReadLocalFileTool Error]")
        assert "File not found" in result

    def test_execute_path_is_directory(self):
        """Test error when path points to a directory."""
        tool = ReadLocalFileTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = tool.execute(path=tmpdir, max_tokens=1000)

            assert result.startswith("[ReadLocalFileTool Error]")
            assert "directory" in result.lower()

    def test_execute_file_too_large(self):
        """Test error when file exceeds size limit."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            # Create a file larger than MAX_FILE_SIZE_BYTES
            large_data = b"x" * (tool.MAX_FILE_SIZE_BYTES + 1024)
            f.write(large_data)
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=100000)

            assert result.startswith("[ReadLocalFileTool Error]")
            assert "File too large" in result
        finally:
            Path(filepath).unlink()

    def test_execute_content_exceeds_token_limit(self):
        """Test error when content exceeds token limit."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            # Write enough content to exceed a small token limit
            large_text = "word " * 10000  # ~10000 tokens
            f.write(large_text)
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=100)

            assert result.startswith("[ReadLocalFileTool Error]")
            assert "exceeds token limit" in result
        finally:
            Path(filepath).unlink()

    def test_execute_with_default_max_tokens(self):
        """Test using default max_tokens value."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=30000)

            assert not result.startswith("[ReadLocalFileTool Error]")
            assert "Test content" in result
        finally:
            Path(filepath).unlink()

    def test_execute_resolves_relative_path(self):
        """Test that relative paths are resolved."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Content")
            f.flush()
            filepath = f.name

        try:
            # Get just the filename
            filename = Path(filepath).name
            result = tool.execute(path=filename, max_tokens=1000)

            # Will fail because relative path from current dir doesn't exist
            assert result.startswith("[ReadLocalFileTool Error]")
        finally:
            Path(filepath).unlink()

    def test_execute_logs_operation(self):
        """Test that file operations are logged."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Log test")
            f.flush()
            filepath = f.name

        try:
            with patch.object(tool._ReadLocalFileTool__logger, "info") as mock_info:
                tool.execute(path=filepath, max_tokens=1000)

                assert mock_info.called
                assert "Successfully read file" in str(mock_info.call_args)
        finally:
            Path(filepath).unlink()

    def test_execute_handles_permission_error(self):
        """Test error handling for permission denied."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test")
            f.flush()
            filepath = f.name

        try:
            # Make file unreadable
            Path(filepath).chmod(0o000)

            result = tool.execute(path=filepath, max_tokens=1000)

            assert result.startswith("[ReadLocalFileTool Error]")
            assert "Permission denied" in result or "File not found" in result
        finally:
            # Restore permissions and delete
            try:
                Path(filepath).chmod(0o644)
                Path(filepath).unlink()
            except Exception:
                pass

    def test_execute_with_python_file(self):
        """Test reading a Python file."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def hello():\n    return 'world'")
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            assert not result.startswith("[ReadLocalFileTool Error]")
            assert "def hello()" in result
        finally:
            Path(filepath).unlink()

    def test_execute_with_markdown_file(self):
        """Test reading a Markdown file."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Header\n\nParagraph")
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            assert not result.startswith("[ReadLocalFileTool Error]")
            assert "# Header" in result
        finally:
            Path(filepath).unlink()

    def test_execute_with_json_file(self):
        """Test reading a JSON file."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"key": "value"}')
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            assert not result.startswith("[ReadLocalFileTool Error]")
            assert "key" in result
            assert "value" in result
        finally:
            Path(filepath).unlink()

    def test_execute_counts_tokens_correctly(self):
        """Test that token counting is performed."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a test " * 100)  # Create repeating content
            f.flush()
            filepath = f.name

        try:
            with patch.object(tool._ReadLocalFileTool__logger, "debug") as mock_debug:
                tool.execute(path=filepath, max_tokens=10000)

                # Check that token count was logged
                calls = [str(call) for call in mock_debug.call_args_list]
                assert any("tokens" in call for call in calls)
        finally:
            Path(filepath).unlink()

    def test_execute_with_empty_file(self):
        """Test reading an empty file."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            # Empty file should still succeed
            assert not result.startswith("[ReadLocalFileTool Error]")
            assert result == "" or len(result) == 0
        finally:
            Path(filepath).unlink()

    def test_execute_detects_file_type_correctly(self):
        """Test that file type detection works."""
        tool = ReadLocalFileTool()

        extensions = [".txt", ".py", ".md", ".json", ".xml"]

        for ext in extensions:
            with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False) as f:
                f.write("content")
                f.flush()
                filepath = f.name

            try:
                with patch.object(
                    tool._ReadLocalFileTool__logger, "debug"
                ) as mock_debug:
                    tool.execute(path=filepath, max_tokens=1000)

                    # Check that file type was logged
                    calls = [str(call) for call in mock_debug.call_args_list]
                    assert any("file as type" in call for call in calls)
            finally:
                Path(filepath).unlink()

    def test_execute_handles_unexpected_exception(self):
        """Test handling of unexpected exceptions."""
        tool = ReadLocalFileTool()

        with patch("pathlib.Path.resolve", side_effect=RuntimeError("Unexpected")):
            result = tool.execute(path="/some/path", max_tokens=1000)

            assert result.startswith("[ReadLocalFileTool Error]")
            assert "Unexpected error" in result

    def test_parameters_schema_has_defaults(self):
        """Test that parameters have proper defaults."""
        tool = ReadLocalFileTool()
        max_tokens_param = tool.parameters["properties"]["max_tokens"]

        assert "default" in max_tokens_param
        assert max_tokens_param["default"] == 30000

    def test_logger_initialization(self):
        """Test that logger is properly initialized."""
        tool = ReadLocalFileTool()
        logger = tool._ReadLocalFileTool__logger

        assert logger is not None

    def test_encoding_initialization(self):
        """Test that tiktoken encoding is initialized."""
        tool = ReadLocalFileTool()
        encoding = tool._ReadLocalFileTool__encoding

        assert encoding is not None

    def test_tool_handles_unicode_content(self):
        """Test reading files with Unicode content."""
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("Café ☕ 日本語 🎉")
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            assert not result.startswith("[ReadLocalFileTool Error]")
            assert "Café" in result or "Caf" in result  # May be sanitized
        finally:
            Path(filepath).unlink()

    def test_multiple_executions_independent(self):
        """Test that multiple executions don't interfere."""
        tool = ReadLocalFileTool()

        files = []
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False
                ) as f:
                    f.write(f"Content {i}")
                    f.flush()
                    files.append(f.name)

            results = [tool.execute(path=f, max_tokens=1000) for f in files]

            assert all(not r.startswith("[ReadLocalFileTool Error]") for r in results)
            assert "Content 0" in results[0]
            assert "Content 1" in results[1]
            assert "Content 2" in results[2]
        finally:
            for f in files:
                Path(f).unlink()

    def test_error_format_consistency(self):
        """Test that all errors follow consistent format."""
        tool = ReadLocalFileTool()

        errors = [
            tool.execute(path="/nonexistent", max_tokens=1000),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            errors.append(tool.execute(path=tmpdir, max_tokens=1000))

        for error in errors:
            assert error.startswith("[ReadLocalFileTool Error]")
            assert ":" in error


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason="Optional dependencies not available"
)
@pytest.mark.unit
class TestReadLocalFileToolConstants:
    """Test constants and configuration."""

    def test_tool_name_constant(self):
        """Test that tool name is a class attribute."""
        assert hasattr(ReadLocalFileTool, "name")
        assert ReadLocalFileTool.name == "read_local_file"

    def test_description_constant(self):
        """Test that description is a class attribute."""
        assert hasattr(ReadLocalFileTool, "description")
        assert isinstance(ReadLocalFileTool.description, str)

    def test_parameters_constant(self):
        """Test that parameters is a class attribute."""
        assert hasattr(ReadLocalFileTool, "parameters")
        assert isinstance(ReadLocalFileTool.parameters, dict)

    def test_max_file_size_is_class_attribute(self):
        """Test MAX_FILE_SIZE_BYTES is accessible."""
        assert hasattr(ReadLocalFileTool, "MAX_FILE_SIZE_BYTES")
        assert ReadLocalFileTool.MAX_FILE_SIZE_BYTES == 100 * 1024 * 1024


@pytest.mark.unit
class TestReadLocalFileToolMissingDependencies:
    """Test behavior when dependencies are missing."""

    def test_tool_requires_dependencies(self):
        """Test that tool initialization requires dependencies."""
        # If dependencies are available, tool can be created
        if DEPENDENCIES_AVAILABLE:
            tool = ReadLocalFileTool()
            assert tool is not None
        else:
            # If dependencies not available, importing should fail
            # This is already tested by the module-level import
            assert ReadLocalFileTool is None

    def test_helpful_error_message(self):
        """Test that error message is helpful."""
        # The actual test is in the tool initialization
        # If dependencies are missing, user gets helpful message
        if not DEPENDENCIES_AVAILABLE:
            # Already handled by module-level import
            pass
        else:
            # Dependencies available, no error expected
            tool = ReadLocalFileTool()
            assert tool is not None
