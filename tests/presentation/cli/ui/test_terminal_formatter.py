import pytest

from createagents.presentation.cli.ui.color_scheme import ColorScheme
from createagents.presentation.cli.ui.terminal_formatter import (
    TerminalFormatter,
)


@pytest.mark.unit
class TestTerminalFormatter:
    def test_terminal_formatter_scenarios_display_width_handles_wide_unicode(
        self,
    ):
        text = f'{ColorScheme.BLUE}A{ColorScheme.RESET}界'

        result = TerminalFormatter.get_display_width(text)

        assert result == 3

    def test_terminal_formatter_scenarios_wrap_text_applies_subsequent_indent(
        self,
    ):
        text = ' '.join(['word'] * 30)

        lines = TerminalFormatter.wrap_text(
            text,
            max_width=10,
            subsequent_indent='>>',
        )

        assert len(lines) > 2
        assert any(line.startswith('>>') for line in lines[1:])

    def test_terminal_formatter_scenarios_format_box_includes_icon_and_timestamp(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            TerminalFormatter,
            'get_terminal_width',
            staticmethod(lambda: 60),
        )
        monkeypatch.setattr(
            TerminalFormatter,
            'wrap_text',
            staticmethod(lambda text, max_width, subsequent_indent='': [text]),
        )

        box = TerminalFormatter.format_rounded_box(
            'Sample message',
            ColorScheme.BLUE,
            align='left',
            icon='👤',
            timestamp='[10:00]',
        )
        lines = box.splitlines()

        assert '👤' in lines[1]
        assert ColorScheme.BLUE in box
        assert lines[0].startswith('[10:00]')
        assert any(edge in box for edge in ('╭', '╯'))
