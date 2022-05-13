from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont
from PySide6.QtCore import Qt
import re


class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, text_intervals, parent=None):
        super().__init__(parent)
        self._text_intervals = sorted(text_intervals)

        self._format = QTextCharFormat()
        self._format.setForeground(Qt.yellow)
        self._format.setFontWeight(QFont.Bold)

        self._text_mapping = ''
        self._interval = None

    def set_text(self, text):
        self._text_mapping = text

    def set_interval(self, interval):
        self._interval = interval

    def highlightBlock(self, text_block):
        if self._text_mapping == '':
            return
        index_to_highlight = self.find_index_of_interval()
        index = 0
        for match in re.finditer(self._text_mapping, text_block):
            if index_to_highlight == index:
                start, end = match.span()
                self.setFormat(start, end - start, self._format)
                break
            index += 1

    def find_index_of_interval(self):
        interval_text = self._interval.data
        index = 0
        for interval in self._text_intervals:
            if interval == self._interval:
                break
            if interval_text == interval.data:
                index += 1

        return index
