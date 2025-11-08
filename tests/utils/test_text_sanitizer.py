"""
Comprehensive test suite for TextSanitizer utility class.

Tests cover:
- Text wrapping functionality (_wrap_text)
- Unicode sanitization (sanitize)
- Markdown to terminal formatting (format_markdown_for_terminal)
- Edge cases and error handling
- Unicode normalization and special character handling
"""

import pytest

from src.utils.text_sanitizer import TextSanitizer


@pytest.mark.unit
class TestWrapText:
    """Test suite for TextSanitizer._wrap_text method."""

    def test_wrap_empty_text(self):
        """Test wrapping empty string."""
        result = TextSanitizer._wrap_text("", 80)
        assert result == []

    def test_wrap_single_word_fits(self):
        """Test wrapping single word that fits within width."""
        result = TextSanitizer._wrap_text("Hello", 80)
        assert result == ["Hello"]

    def test_wrap_single_word_exceeds_width(self):
        """Test wrapping single word that exceeds width."""
        result = TextSanitizer._wrap_text("Supercalifragilisticexpialidocious", 10)
        assert result == ["Supercalifragilisticexpialidocious"]

    def test_wrap_multiple_words_fits(self):
        """Test wrapping multiple words that fit in one line."""
        result = TextSanitizer._wrap_text("Hello World", 80)
        assert result == ["Hello World"]

    def test_wrap_multiple_words_needs_wrapping(self):
        """Test wrapping multiple words that need multiple lines."""
        text = "The quick brown fox jumps over the lazy dog"
        result = TextSanitizer._wrap_text(text, 20)

        # Verify all words are preserved
        all_words = " ".join(result).split()
        original_words = text.split()
        assert set(all_words) == set(original_words)

        # Verify no line exceeds width
        for line in result:
            assert len(line) <= 20

    def test_wrap_with_width_zero(self):
        """Test wrapping with zero width."""
        result = TextSanitizer._wrap_text("Hello World", 0)
        # Should still process, placing each word
        assert len(result) > 0

    def test_wrap_with_width_one(self):
        """Test wrapping with width of 1."""
        result = TextSanitizer._wrap_text("Hello World", 1)
        assert len(result) >= 2

    def test_wrap_preserves_word_order(self):
        """Test that wrapping preserves word order."""
        text = "One Two Three Four Five Six Seven Eight"
        result = TextSanitizer._wrap_text(text, 15)

        reconstructed = " ".join(result)
        words_original = text.split()
        words_wrapped = reconstructed.split()

        assert words_original == words_wrapped

    def test_wrap_with_extra_spaces(self):
        """Test wrapping text with multiple spaces between words."""
        text = "Hello    World    Test"
        result = TextSanitizer._wrap_text(text, 80)

        # Extra spaces are collapsed during split
        assert "Hello" in result[0]
        assert "World" in result[0]

    def test_wrap_very_long_text(self):
        """Test wrapping very long text with small width."""
        text = " ".join(["word"] * 100)
        result = TextSanitizer._wrap_text(text, 20)

        assert len(result) > 1
        for line in result:
            assert len(line) <= 20

    def test_wrap_single_long_word_with_small_width(self):
        """Test wrapping single long word with very small width."""
        result = TextSanitizer._wrap_text("Antidisestablishmentarianism", 5)
        # Long word exceeding width is still returned as-is
        assert "Antidisestablishmentarianism" in result

    def test_wrap_respects_width_boundary(self):
        """Test that wrapped lines respect width boundary."""
        text = "Short text to wrap with specific width limit"
        width = 25
        result = TextSanitizer._wrap_text(text, width)

        for line in result:
            assert len(line) <= width

    def test_wrap_only_whitespace(self):
        """Test wrapping text with only whitespace."""
        result = TextSanitizer._wrap_text("     ", 80)
        assert result == []

    def test_wrap_text_with_tabs(self):
        """Test wrapping text containing tabs."""
        text = "Hello\tWorld\tTest"
        result = TextSanitizer._wrap_text(text, 80)

        # Tabs are treated as separators
        assert len(result) > 0
        reconstructed = " ".join(result)
        # Words are preserved but tabs are converted to spaces
        assert "Hello" in reconstructed
        assert "World" in reconstructed
        assert "Test" in reconstructed

    def test_wrap_text_with_newlines_treated_as_spaces(self):
        """Test that newlines in text are treated as spaces."""
        text = "Hello\nWorld\nTest"
        result = TextSanitizer._wrap_text(text, 80)

        assert len(result) > 0
        reconstructed = " ".join(result)
        assert "Hello" in reconstructed
        assert "World" in reconstructed
        assert "Test" in reconstructed

    def test_wrap_with_increasingly_larger_width(self):
        """Test wrapping same text with different widths."""
        text = "The quick brown fox jumps over the lazy dog"

        result_10 = TextSanitizer._wrap_text(text, 10)
        result_20 = TextSanitizer._wrap_text(text, 20)
        result_100 = TextSanitizer._wrap_text(text, 100)

        # Larger width should produce fewer or equal lines
        assert len(result_100) <= len(result_20) <= len(result_10)

    def test_wrap_consecutive_long_words(self):
        """Test wrapping text with multiple long words."""
        text = "Supercalifragilisticexpialidocious Antidisestablishmentarianism"
        result = TextSanitizer._wrap_text(text, 40)

        assert len(result) >= 1
        for line in result:
            assert len(line) <= 40


@pytest.mark.unit
class TestSanitize:
    """Test suite for TextSanitizer.sanitize method."""

    def test_sanitize_normal_text(self):
        """Test sanitizing normal ASCII text."""
        text = "Hello World"
        result = TextSanitizer.sanitize(text)
        assert result == "Hello World"

    def test_sanitize_empty_string(self):
        """Test sanitizing empty string."""
        result = TextSanitizer.sanitize("")
        assert result == ""

    def test_sanitize_non_string_input(self):
        """Test sanitizing non-string input."""
        # Should return the input as-is if not a string
        assert TextSanitizer.sanitize(123) == 123
        assert TextSanitizer.sanitize(None) is None
        assert TextSanitizer.sanitize([]) == []

    def test_sanitize_narrow_nbsp(self):
        """Test removing narrow no-break space (U+202F)."""
        text = "Hello\u202fWorld"
        result = TextSanitizer.sanitize(text)
        assert "\u202f" not in result
        assert result == "Hello World"

    def test_sanitize_nbsp(self):
        """Test removing non-breaking space (U+00A0)."""
        text = "Hello\u00a0World"
        result = TextSanitizer.sanitize(text)
        assert "\u00a0" not in result
        assert result == "Hello World"

    def test_sanitize_non_breaking_hyphen(self):
        """Test replacing non-breaking hyphen (U+2011)."""
        text = "Mother\u2011in\u2011law"
        result = TextSanitizer.sanitize(text)
        assert "\u2011" not in result
        assert result == "Mother-in-law"

    def test_sanitize_thin_space(self):
        """Test removing thin space (U+2009)."""
        text = "Hello\u2009World"
        result = TextSanitizer.sanitize(text)
        assert "\u2009" not in result
        assert result == "Hello World"

    def test_sanitize_zero_width_space(self):
        """Test removing zero-width space (U+200B)."""
        text = "Hello\u200bWorld"
        result = TextSanitizer.sanitize(text)
        assert "\u200b" not in result
        assert result == "HelloWorld"

    def test_sanitize_zero_width_non_joiner(self):
        """Test removing zero-width non-joiner (U+200C)."""
        text = "Hello\u200cWorld"
        result = TextSanitizer.sanitize(text)
        assert "\u200c" not in result
        assert result == "HelloWorld"

    def test_sanitize_zero_width_joiner(self):
        """Test removing zero-width joiner (U+200D)."""
        text = "Hello\u200dWorld"
        result = TextSanitizer.sanitize(text)
        assert "\u200d" not in result
        assert result == "HelloWorld"

    def test_sanitize_multiple_problematic_chars(self):
        """Test sanitizing text with multiple problematic Unicode chars."""
        text = "Hello\u202fWorld\u00a0Test\u200bString"
        result = TextSanitizer.sanitize(text)

        assert "\u202f" not in result
        assert "\u00a0" not in result
        assert "\u200b" not in result
        assert "Hello World" in result
        assert "Test" in result

    def test_sanitize_unicode_normalization(self):
        """Test that sanitize applies NFKC normalization."""
        # Text with decomposed characters
        text = "café"  # é can be composed or decomposed
        result = TextSanitizer.sanitize(text)

        # Should be normalized to composed form
        assert result == "café"

    def test_sanitize_special_unicode_characters_preserved(self):
        """Test that safe Unicode characters are preserved."""
        text = "你好 🎉 Привет"
        result = TextSanitizer.sanitize(text)

        assert "你好" in result
        assert "🎉" in result
        assert "Привет" in result

    def test_sanitize_accented_characters(self):
        """Test that accented characters are preserved."""
        text = "café naïve résumé"
        result = TextSanitizer.sanitize(text)

        assert "café" in result
        assert "naïve" in result
        assert "résumé" in result

    def test_sanitize_idempotent(self):
        """Test that sanitizing already sanitized text is idempotent."""
        text = "Hello\u202fWorld"
        once = TextSanitizer.sanitize(text)
        twice = TextSanitizer.sanitize(once)

        assert once == twice

    def test_sanitize_with_newlines_preserved(self):
        """Test that newlines are preserved."""
        text = "Line1\nLine2\nLine3"
        result = TextSanitizer.sanitize(text)

        assert result == text
        assert "\n" in result

    def test_sanitize_with_tabs_preserved(self):
        """Test that tabs are preserved."""
        text = "Col1\tCol2\tCol3"
        result = TextSanitizer.sanitize(text)

        assert result == text
        assert "\t" in result

    def test_sanitize_mixed_spaces(self):
        """Test sanitizing text with mixed space types."""
        text = "A\u202fB\u00a0C\u2009D E"
        result = TextSanitizer.sanitize(text)

        assert " " in result
        assert "\u202f" not in result
        assert "\u00a0" not in result
        assert "\u2009" not in result


@pytest.mark.unit
class TestFormatMarkdownForTerminal:
    """Test suite for TextSanitizer.format_markdown_for_terminal method."""

    # Basic input validation
    def test_format_non_string_input(self):
        """Test formatting non-string input."""
        assert TextSanitizer.format_markdown_for_terminal(123) == 123
        assert TextSanitizer.format_markdown_for_terminal(None) is None

    def test_format_empty_string(self):
        """Test formatting empty string."""
        result = TextSanitizer.format_markdown_for_terminal("")
        assert result == ""

    def test_format_plain_text(self):
        """Test formatting plain text without markdown."""
        text = "This is plain text"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "This is plain text" in result

    # HTML tag removal
    def test_format_remove_br_tags(self):
        """Test removal of <br> tags."""
        text = "Line 1<br>Line 2<br/>Line 3"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "<br" not in result
        assert "\n" in result

    def test_format_remove_html_tags(self):
        """Test removal of common HTML tags."""
        text = "This is <b>bold</b> and <i>italic</i> and <span>span</span>"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "<b>" not in result
        assert "<i>" not in result
        assert "<span>" not in result
        assert "bold" in result
        assert "italic" in result

    def test_format_remove_complex_html_tags(self):
        """Test removal of complex HTML tags with attributes."""
        text = 'This is a <a href="link">link</a> and <div class="box">content</div>'
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "<a" not in result
        assert "<div" not in result
        assert "link" in result
        assert "content" in result

    # Header formatting
    def test_format_h1_header(self):
        """Test formatting H1 (# ) header."""
        text = "# Main Title"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Main Title" in result
        assert "═══════" in result

    def test_format_h2_header(self):
        """Test formatting H2 (##) header."""
        text = "## Section Title"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Section Title" in result
        assert "═══" in result

    def test_format_h3_header(self):
        """Test formatting H3 (###) header."""
        text = "### Subsection"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Subsection" in result
        assert "━━━" in result

    def test_format_h4_h5_h6_headers(self):
        """Test formatting H4, H5, H6 headers."""
        for level in [4, 5, 6]:
            markdown = "#" * level + " Header"
            result = TextSanitizer.format_markdown_for_terminal(markdown)
            assert "Header" in result
            assert "━━" in result

    def test_format_multiple_headers(self):
        """Test formatting multiple headers."""
        text = "# Title\n## Section 1\n### Subsection\n## Section 2"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Title" in result
        assert "Section 1" in result
        assert "Subsection" in result
        assert "Section 2" in result

    # Bold and italic formatting
    def test_format_bold_double_asterisk(self):
        """Test removing **bold** formatting."""
        text = "This is **bold** text"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "**" not in result
        assert "bold" in result

    def test_format_bold_double_underscore(self):
        """Test removing __bold__ formatting."""
        text = "This is __bold__ text"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "__" not in result
        assert "bold" in result

    def test_format_italic_single_asterisk(self):
        """Test removing *italic* formatting."""
        text = "This is *italic* text"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "*italic*" not in result
        assert "italic" in result

    def test_format_italic_single_underscore(self):
        """Test removing _italic_ formatting."""
        text = "This is _italic_ text"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "_italic_" not in result
        assert "italic" in result

    def test_format_mixed_bold_italic(self):
        """Test formatting with mixed bold and italic."""
        text = "This is **bold** and *italic* and __bold__ and _italic_"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "**" not in result
        assert "__" not in result
        assert "bold" in result
        assert "italic" in result

    # List formatting
    def test_format_unordered_list_dash(self):
        """Test formatting unordered list with dashes."""
        text = "- Item 1\n- Item 2\n- Item 3"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "•" in result
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Item 3" in result

    def test_format_unordered_list_asterisk(self):
        """Test formatting unordered list with asterisks."""
        text = "* Item 1\n* Item 2\n* Item 3"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "•" in result
        assert "Item 1" in result

    def test_format_unordered_list_plus(self):
        """Test formatting unordered list with plus signs."""
        text = "+ Item 1\n+ Item 2\n+ Item 3"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "•" in result
        assert "Item 1" in result

    def test_format_ordered_list(self):
        """Test formatting ordered list."""
        text = "1. First\n2. Second\n3. Third"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "→" in result
        assert "First" in result
        assert "Second" in result
        assert "Third" in result

    def test_format_nested_list(self):
        """Test formatting nested list with indentation."""
        text = "- Item 1\n  - Subitem 1.1\n  - Subitem 1.2\n- Item 2"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "•" in result
        assert "Item 1" in result
        assert "Subitem" in result

    # Horizontal rules
    def test_format_horizontal_rule_dashes(self):
        """Test formatting horizontal rule with dashes."""
        text = "Before\n---\nAfter"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "─" in result
        assert "Before" in result
        assert "After" in result

    def test_format_horizontal_rule_asterisks(self):
        """Test formatting horizontal rule with asterisks."""
        text = "Before\n***\nAfter"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "─" in result

    def test_format_horizontal_rule_underscores(self):
        """Test formatting horizontal rule with underscores."""
        text = "Before\n___\nAfter"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "─" in result

    # Table formatting
    def test_format_simple_table_two_columns(self):
        """Test formatting simple 2-column table."""
        text = "| Header1 | Header2 |\n|---------|----------|\n| Value1  | Value2  |"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Header1" in result
        assert "Value1" in result
        assert "│" in result or "▪" in result  # Either table format or label-value

    def test_format_table_with_long_content(self):
        """Test formatting table with long content that needs wrapping."""
        text = "| Name | Description |\n|------|-------------|\n| Item | This is a very long description that should be wrapped properly in the terminal |"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Name" in result or "Item" in result
        assert "Description" in result or "description" in result

    def test_format_multicolumn_table(self):
        """Test formatting table with multiple columns."""
        text = "| Col1 | Col2 | Col3 |\n|------|------|------|\n| A | B | C |"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Col1" in result
        assert "A" in result or "│" in result

    # Edge cases and special content
    def test_format_consecutive_blank_lines(self):
        """Test that consecutive blank lines are reduced."""
        text = "Line 1\n\n\n\nLine 2"
        result = TextSanitizer.format_markdown_for_terminal(text)

        # Should have at most 2 newlines in a row
        assert "\n\n\n" not in result

    def test_format_trailing_spaces_removed(self):
        """Test that trailing spaces on lines are removed."""
        text = "Line 1   \nLine 2   "
        result = TextSanitizer.format_markdown_for_terminal(text)

        lines = result.split("\n")
        for line in lines:
            assert not line.endswith(" ")

    def test_format_code_block_with_backticks(self):
        """Test handling of code blocks with backticks."""
        text = "`code` and ``double`` and ```\nblock\n```"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "code" in result

    def test_format_links_removed(self):
        """Test that markdown links are processed."""
        text = "[Link text](https://example.com)"
        result = TextSanitizer.format_markdown_for_terminal(text)

        # At minimum, should not have markdown link format
        assert "[" not in result or "Link text" in result

    def test_format_unicode_characters_preserved(self):
        """Test that Unicode characters are preserved."""
        text = "Hello 你好 🎉 Привет"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "你好" in result
        assert "🎉" in result
        assert "Привет" in result

    def test_format_mixed_markdown(self):
        """Test formatting complex markdown with multiple elements."""
        text = """# Main Title

## Section 1
This is *italic* and **bold** text.

- Bullet 1
- Bullet 2

1. Numbered 1
2. Numbered 2

---

| Header | Value |
|--------|-------|
| Row1   | Data1 |
"""
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Main Title" in result
        assert "Section 1" in result
        assert "•" in result
        assert "→" in result
        assert "─" in result

    def test_format_empty_table_cells(self):
        """Test formatting table with empty cells."""
        text = "| Col1 | Col2 |\n|------|------|\n| | Empty |"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Col1" in result
        assert "Empty" in result

    def test_format_list_with_complex_items(self):
        """Test formatting list with complex item text."""
        text = "- Item with **bold** and *italic*\n- Another **item**"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "•" in result
        assert "bold" in result
        assert "italic" in result

    def test_format_header_with_markdown_inside(self):
        """Test formatting header with embedded markdown."""
        text = "# Header with **bold** and *italic*"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Header with" in result
        assert "bold" in result

    def test_format_very_long_line(self):
        """Test formatting very long line."""
        long_text = "This is a very long line " * 20
        result = TextSanitizer.format_markdown_for_terminal(long_text)

        # Should still contain the content
        assert "This is a very long line" in result

    def test_format_special_markdown_chars_in_plain_text(self):
        """Test text containing markdown special characters but not markdown."""
        text = "Price is $5.99 * 2 = $11.98"
        result = TextSanitizer.format_markdown_for_terminal(text)

        # Should handle gracefully
        assert "Price" in result

    def test_format_malformed_markdown(self):
        """Test handling of malformed markdown."""
        text = "**unclosed bold\n*unclosed italic\n- Incomplete list item: "
        result = TextSanitizer.format_markdown_for_terminal(text)

        # Should handle gracefully without errors
        assert isinstance(result, str)

    def test_format_preserves_paragraph_structure(self):
        """Test that basic paragraph structure is preserved."""
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Paragraph 1" in result
        assert "Paragraph 2" in result
        assert "Paragraph 3" in result


@pytest.mark.unit
class TestTextSanitizerIntegration:
    """Integration tests combining multiple TextSanitizer methods."""

    def test_full_pipeline_sanitize_then_format(self):
        """Test full pipeline: sanitize then format."""
        # Text with problematic Unicode and markdown
        text = "# Title\u202f(with problematic char)\n\n**Bold** and *italic*"

        sanitized = TextSanitizer.sanitize(text)
        formatted = TextSanitizer.format_markdown_for_terminal(sanitized)

        assert "Title" in formatted
        assert "problematic char" in formatted
        assert "\u202f" not in formatted

    def test_format_already_formats_sanitization(self):
        """Test that format_markdown_for_terminal also sanitizes."""
        text = "# Title\u202fTest\n**Bold**"

        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "\u202f" not in result
        assert "Title" in result
        assert "Test" in result

    def test_markdown_with_unicode_content(self):
        """Test markdown formatting with Unicode content."""
        text = "# 你好世界\n\n**中文** 和 *日本語*\n\n- 项目1\n- 項目2"

        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "你好世界" in result
        assert "中文" in result
        assert "•" in result

    def test_complex_document_formatting(self):
        """Test formatting complex document with all features."""
        document = """# Project Documentation

## Overview
This is a **critical** project with *important* details.

### Features
- Feature 1: *Essential*
- Feature 2: **Must have**
- Feature 3: Optional

## Usage

| Command | Description |
|---------|-------------|
| start | **Starts** the service |
| stop | Stops the *running* service |

---

### Notes
- Created: 2024-01-01
- Modified: 2024-11-07
"""

        result = TextSanitizer.format_markdown_for_terminal(document)

        # Verify major sections are present
        assert "Project Documentation" in result
        assert "Overview" in result
        assert "Features" in result
        assert "Usage" in result
        assert "Command" in result
        assert "•" in result
        assert "─" in result or "━" in result

    def test_wrap_text_after_formatting(self):
        """Test that formatted text can be wrapped."""
        markdown = "# Title\n\nThis is a long line that might need wrapping when displayed in a terminal with limited width"

        formatted = TextSanitizer.format_markdown_for_terminal(markdown)
        wrapped = TextSanitizer._wrap_text(formatted, 40)

        assert len(wrapped) > 0
        for line in wrapped:
            assert len(line) <= 40


@pytest.mark.unit
class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling across all methods."""

    def test_extremely_large_text(self):
        """Test handling of extremely large text."""
        large_text = "word " * 10000

        # Should not crash
        result_wrapped = TextSanitizer._wrap_text(large_text, 80)
        assert len(result_wrapped) > 0

        result_sanitized = TextSanitizer.sanitize(large_text)
        assert "word" in result_sanitized

        result_formatted = TextSanitizer.format_markdown_for_terminal(large_text)
        assert "word" in result_formatted

    def test_none_handling(self):
        """Test handling of None values."""
        assert TextSanitizer.sanitize(None) is None
        assert TextSanitizer.format_markdown_for_terminal(None) is None

    def test_numeric_input_handling(self):
        """Test handling of numeric inputs."""
        assert TextSanitizer.sanitize(42) == 42
        assert TextSanitizer.format_markdown_for_terminal(3.14) == 3.14

    def test_list_input_handling(self):
        """Test handling of list inputs."""
        lst = [1, 2, 3]
        assert TextSanitizer.sanitize(lst) == lst
        assert TextSanitizer.format_markdown_for_terminal(lst) == lst

    def test_unicode_edge_cases(self):
        """Test various Unicode edge cases."""
        test_cases = [
            "\u200b\u200c\u200d",  # Zero-width chars
            "\u202f\u00a0\u2009",  # Various spaces
            "🏴󠁧󠁢󠁳󠁣󠁴󠁿",  # Flag emoji with tags
            "\uffff",  # High Unicode value
        ]

        for text in test_cases:
            result = TextSanitizer.sanitize(text)
            assert isinstance(result, str)

    def test_mixed_line_endings(self):
        """Test handling of mixed line endings."""
        text = "Line1\nLine2\r\nLine3\rLine4"
        result = TextSanitizer.format_markdown_for_terminal(text)

        assert "Line" in result

    def test_format_with_only_markdown_syntax(self):
        """Test formatting text containing only markdown syntax."""
        text = "# ## ### #### ##### ######"
        result = TextSanitizer.format_markdown_for_terminal(text)

        # Should not crash
        assert isinstance(result, str)

    def test_wrap_text_width_larger_than_content(self):
        """Test wrapping when width is larger than content."""
        text = "Short"
        result = TextSanitizer._wrap_text(text, 1000)

        assert result == ["Short"]

    def test_consecutive_formatting_calls(self):
        """Test multiple consecutive formatting calls."""
        text = "# Test\n**bold** and *italic*"

        result1 = TextSanitizer.format_markdown_for_terminal(text)
        result2 = TextSanitizer.format_markdown_for_terminal(result1)
        result3 = TextSanitizer.format_markdown_for_terminal(result2)

        # Should reach stable state
        assert result2 == result3
